package common

import (
	"encoding/binary"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	log "github.com/sirupsen/logrus"
)

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopLapse     time.Duration
	LoopPeriod    time.Duration
	BatchSize     int
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
	conn   net.Conn
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config: config,
	}
	return client
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	conn, err := net.DialTimeout("tcp", c.config.ServerAddress, 5*time.Second)
	if err != nil {
		log.Fatalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
	}
	c.conn = conn
	return nil
}

func LogResults(id string, winners []uint64) {
	total_winners := len(winners)
	log.Infof(
		"[CLIENT %v] action: consulta_ganadores | result: success | cant_ganadores: %v",
		id,
		total_winners,
	)
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() {
	// autoincremental msgID to identify every message sent
	agency := Agency{c.config.ID}
	c.createClientSocket()

	// Setup signal channel to receive SIGINT/SIGTERM signals
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	dataReader := NewDataReader("/data/contestants.csv", int(c.config.BatchSize))
	err := SendLoadRequest(c.conn, c.config.ID)
	log.Infof("[CLIENT %v] Sent load request (batch size: %v)", c.config.ID, dataReader.BatchSize)
	if err != nil {
		log.Fatalf(
			"[CLIENT %v] Could not send load request. Error: %v",
			c.config.ID,
			err,
		)
	}

	total_contestants := 0
loop:
	for !dataReader.IsAtEnd {
		select {
		case s := <-sigChan:
			log.Errorf(
				"[CLIENT %v] %v received. Exiting...",
				c.config.ID,
				s,
			)
			break loop
		default:
		}

		batch := dataReader.ReadBatch(agency)
		if len(batch) == 0 {
			break loop
		}
		total_contestants += len(batch)

		// Send
		serialized := SerializeBatch(batch)
		// log.Infof(
		// 	"[CLIENT %v] Sending batch %v",
		// 	c.config.ID,
		// 	serialized,
		// )
		count, err := c.conn.Write(serialized)
		if err != nil {
			log.Errorf(
				"[CLIENT %v] Error sending message. Error: %v",
				c.config.ID,
				err,
			)
			break loop
		} else if count != len(serialized) {
			log.Errorf(
				"[CLIENT %v] Error sending message. Error: %v",
				c.config.ID,
				"Could not send all bytes",
			)
			break loop
		}

		response, err := RecvLoadResponse(c.conn)
		if err != nil {
			log.Errorf(
				"[CLIENT %v] Error receiving response. Error: %v",
				c.config.ID,
				err,
			)
			break loop
		} else if response != len(batch) {
			log.Warnf(
				"[CLIENT %v] The server didn't receive all messages!",
				c.config.ID,
			)
		}
	}

	log.Infof(
		"[CLIENT %v] action: apuesta_enviada | result: success | total_sent: %v",
		c.config.ID,
		total_contestants,
	)

	end_msg := make([]byte, 4)
	binary.BigEndian.PutUint32(end_msg, 0)
	c.conn.Write(end_msg)
	log.Infof("[CLIENT %v] Closing load connection", c.config.ID)
	c.conn.Close()

	done := false
	max_time := c.config.LoopLapse
	sleep_time := c.config.LoopPeriod
query:
	for !done {
		select {
		case s := <-sigChan:
			log.Errorf(
				"[CLIENT %v] %v received. Exiting...",
				c.config.ID,
				s,
			)
			break query
		default:
		}
		// Check the total results
		sleep_time = sleep_time * 2
		if sleep_time > max_time {
			sleep_time = max_time
		}
		time.Sleep(sleep_time)
		c.createClientSocket()
		err = SendQueryRequest(c.conn, agency.Id)
		log.Infof("[CLIENT %v] Sent query request", c.config.ID)
		if err != nil {
			log.Fatalf(
				"[CLIENT %v] Could not send query request. Error: %v",
				c.config.ID,
				err,
			)
		}

		is_done, winners, err := RecvQueryResponse(c.conn)
		if err != nil {
			log.Errorf(
				"[CLIENT %v] Error receiving response. Error: %v",
				c.config.ID,
				err,
			)
		}
		done = is_done
		if !done {
			log.Infof("[CLIENT %v] Waiting for results...", c.config.ID)
			continue
		}
		c.conn.Close()
		LogResults(c.config.ID, winners)
	}

}
