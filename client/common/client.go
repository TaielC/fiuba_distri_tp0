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

func recvCompleteMessage(conn net.Conn, buf []byte) (int, error) {
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

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() {
	// Create the connection the server in every loop iteration. Send an
	// autoincremental msgID to identify every message sent
	c.createClientSocket()

	// Setup signal channel to receive SIGINT/SIGTERM signals
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	// Get env or default for FIRST_NAME

	firstName := os.Getenv("FIRST_NAME")
	lastName := os.Getenv("LAST_NAME")
	id := os.Getenv("ID")
	birthDate := os.Getenv("BIRTH_DATE")

	// Create an array of people
	people := []Person{
		CreatePerson(firstName, lastName, id, birthDate),
	}

loop:
	for i, person := range people {
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

		// Send
		serialized := person.Serialize()
		count, err := c.conn.Write(serialized)
		if err != nil {
			log.Errorf(
				"[CLIENT %v] Error sending message %v. Error: %v",
				c.config.ID,
				i,
				err,
			)
			break loop
		} else if count != len(serialized) {
			log.Errorf(
				"[CLIENT %v] Error sending message %v. Error: %v",
				c.config.ID,
				i,
				"Could not send all bytes",
			)
			break loop
		}

		size_bytes := make([]byte, 4)
		_, err = recvCompleteMessage(c.conn, size_bytes)
		if err != nil {
			log.Errorf(
				"[CLIENT %v] Error receiving message %v. Error: %v",
				c.config.ID,
				i,
				err,
			)
			break loop
		}
		size := binary.BigEndian.Uint32(size_bytes)
		response := make([]byte, size)
		_, err = recvCompleteMessage(c.conn, response)
		if err != nil {
			log.Errorf(
				"[CLIENT %v] Error receiving message %v. Error: %v",
				c.config.ID,
				i,
				err,
			)
			break loop
		}
		log.Infof(
			"[CLIENT %v] Received response %v: %v",
			c.config.ID,
			i,
			string(response),
		)

		// Recreate connection to the server
	}

	log.Infof("[CLIENT %v] Closing connection", c.config.ID)
	c.conn.Close()
}
