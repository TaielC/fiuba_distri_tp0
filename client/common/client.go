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

func SerializeRequest(conn net.Conn, id string, t byte) []byte {
	buf := make([]byte, 5+len(id))
	buf[0] = t
	binary.BigEndian.PutUint32(buf[1:5], uint32(len(id)))
	copy(buf[5:], []byte(id))
	return buf
}

func SendLoadRequest(conn net.Conn, id string) error {
	_, err := conn.Write(SerializeRequest(conn, id, 1))
	return err
}

func SendQueryRequest(conn net.Conn, id string) error {
	_, err := conn.Write(SerializeRequest(conn, id, 0))
	return err
}

func DeserializeLoadResponse(buf []byte) []bool {
	response := make([]bool, len(buf))
	for i := 0; i < len(buf); i++ {
		response[i] = buf[i] == 1
	}
	return response
}

func RecvLoadResponse(conn net.Conn) ([]bool, error) {
	size_bytes := make([]byte, 4)
	_, err := RecvCompleteMessage(conn, size_bytes)
	if err != nil {
		return nil, err
	}
	size := binary.BigEndian.Uint32(size_bytes)
	if size == 0 {
		return nil, nil
	}
	response := make([]byte, size)
	_, err = RecvCompleteMessage(conn, response)
	if err != nil {
		return nil, err
	}
	return DeserializeLoadResponse(response), nil
}

func DeserializeQueryResponse(buf []byte) uint64 {
	return binary.BigEndian.Uint64(buf)
}

func RecvQueryResponse(conn net.Conn) (bool, uint64, error) {
	response := make([]byte, 8)
	_, err := RecvCompleteMessage(conn, response)
	if err != nil {
		return false, 0, err
	}
	count := DeserializeQueryResponse(response)
	count_int := int64(count)
	is_partial := count_int < 0
	if is_partial {
		count_int = -count_int
	}
	return is_partial, uint64(count_int), nil
}

func LogResults(id string, response []bool, total int) {
	total_sent := len(response)
	total_winners := 0
	for _, winner := range response {
		if winner {
			total_winners++
		}
	}
	log.Infof(
		"[CLIENT %v] Sent: %v, Winners: %v, Ratio: %v",
		id,
		total_sent,
		total_winners,
		float64(total_winners)/float64(total_sent),
	)
	if total != total_sent {
		log.Warnf(
			"[CLIENT %v] Total sent does not match total requested. Requested: %v, Sent: %v",
		)
	}
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() {
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

	responses := make([]bool, 0)
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

		batch := dataReader.ReadBatch()
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
		} else if len(response) != len(batch) {
			log.Warnf(
				"[CLIENT %v] The server didn't receive all messages!",
				c.config.ID,
			)
		}
		responses = append(responses, response...)
	}

	log.Infof("[CLIENT %v] loop_finished", c.config.ID)

	end_msg := make([]byte, 4)
	binary.BigEndian.PutUint32(end_msg, 0)
	c.conn.Write(end_msg)
	log.Infof("[CLIENT %v] Closing load connection", c.config.ID)
	LogResults(c.config.ID, responses, total_contestants)
	c.conn.Close()

	partial := true
	max_time := 60 * time.Second
	sleep_time := 1 * time.Second
	for partial {
		// Check the total results
		sleep_time = sleep_time * 2
		if sleep_time > max_time {
			sleep_time = max_time
		}
		time.Sleep(sleep_time)
		c.createClientSocket()
		err = SendQueryRequest(c.conn, "*")
		if err != nil {
			log.Fatalf(
				"[CLIENT %v] Could not send query request. Error: %v",
				c.config.ID,
				err,
			)
		}

		is_partial, count, err := RecvQueryResponse(c.conn)
		if err != nil {
			log.Errorf(
				"[CLIENT %v] Error receiving response. Error: %v",
				c.config.ID,
				err,
			)
		}
		log.Infof(
			"[CLIENT %v] Total winners: (partial? %v) %v",
			c.config.ID,
			is_partial,
			count,
		)
		partial = is_partial
		c.conn.Close()
	}
}
