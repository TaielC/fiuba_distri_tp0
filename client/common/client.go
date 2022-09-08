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
	conn, err := net.Dial("tcp", c.config.ServerAddress)
	if err != nil {
		log.Fatalf(
			"[CLIENT %v] Could not connect to server. Error: %v",
			c.config.ID,
			err,
		)
	}
	c.conn = conn
	return nil
}

func RecvCompleteMessage(conn net.Conn, buf []byte) (int, error) {
	var read int
	var err error
	for read < len(buf) {
		n, err := conn.Read(buf[read:])
		read += n
		if err != nil {
			return read, err
		}
	}
	return read, err
}

func SerializeLoadRequest(conn net.Conn, id string) []byte {
	buf := make([]byte, 5+len(id))
	buf[0] = 1
	binary.BigEndian.PutUint32(buf[1:5], uint32(len(id)))
	copy(buf[5:], []byte(id))
	return buf
}

func SendLoadRequest(conn net.Conn, id string) error {
	_, err := conn.Write(SerializeLoadRequest(conn, id))
	return err
}

func DeserializeResponse(buf []byte) []bool {
	response := make([]bool, len(buf))
	for i := 0; i < len(buf); i++ {
		response[i] = buf[i] == 1
	}
	return response
}

func (c *Client) RecvResponse() ([]bool, error) {
	size_bytes := make([]byte, 4)
	_, err := RecvCompleteMessage(c.conn, size_bytes)
	if err != nil {
		return nil, err
	}
	size := binary.BigEndian.Uint32(size_bytes)
	if size == 0 {
		return nil, nil
	}
	response := make([]byte, size)
	_, err = RecvCompleteMessage(c.conn, response)
	if err != nil {
		return nil, err
	}
	return DeserializeResponse(response), nil
}

func LogResponse(id string, contestants []Person, response []bool) {
	total := len(contestants)
	positive := 0
	for _, v := range response {
		if v {
			positive++
		}
	}
	log.Infof(
		"[CLIENT %v] Winners: %v/%v (%.2f%%)",
		id,
		positive,
		total,
		100*float64(positive)/float64(total),
	)
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() {
	// Create the connection the server in every loop iteration. Send an
	// autoincremental msgID to identify every message sent
	c.createClientSocket()

	// Setup signal channel to receive SIGINT/SIGTERM signals
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	dataReader := NewDataReader("/data/contestants.csv", int(c.config.BatchSize))
	err := SendLoadRequest(c.conn, c.config.ID)
	if err != nil {
		log.Fatalf(
			"[CLIENT %v] Could not send load request. Error: %v",
			c.config.ID,
			err,
		)
	}

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

		batch := dataReader.ReadBatch()
		if len(batch) == 0 {
			break loop
		}

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

		response, res_err := c.RecvResponse()
		if res_err != nil {
			log.Errorf(
				"[CLIENT %v] Error receiving response. Error: %v",
				c.config.ID,
				res_err,
			)
			break loop
		} else if len(response) != len(batch) {
			log.Warnf(
				"[CLIENT %v] The server didn't receive all messages!",
				c.config.ID,
			)
		}
		LogResponse(c.config.ID, batch, response)
	}

	end_msg := make([]byte, 4)
	binary.BigEndian.PutUint32(end_msg, 0)
	c.conn.Write(end_msg)
	log.Infof("[CLIENT %v] Closing connection", c.config.ID)
	c.conn.Close()
}
