package common

import (
	"encoding/binary"
	"net"
)

const UINT64_SIZE = 8

// Serialize a string as its length and then the string
func SerializeString(str string) []byte {
	serialized_string := []byte(str)
	size := len(serialized_string)
	buf := make([]byte, size+4)
	binary.BigEndian.PutUint32(buf, uint32(size))
	copy(buf[4:], serialized_string)
	return buf
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

func RecvLoadResponse(conn net.Conn) (int, error) {
	serialized := make([]byte, 4)
	_, err := RecvCompleteMessage(conn, serialized)
	if err != nil {
		return 0, err
	}
	size := binary.BigEndian.Uint32(serialized)
	return int(size), nil
}

func RecvQueryResponse(conn net.Conn) (bool, []uint64, error) {
	ser_count := make([]byte, UINT64_SIZE)
	_, err := RecvCompleteMessage(conn, ser_count)
	if err != nil {
		return true, nil, err
	}
	count := int(binary.BigEndian.Uint64(ser_count))
	if count < 0 {
		return false, nil, nil
	}
	buf := make([]byte, count*UINT64_SIZE)
	_, err = RecvCompleteMessage(conn, buf)
	if err != nil {
		return true, nil, err
	}
	winners := make([]uint64, count)
	for i := 0; i < int(count); i++ {
		winners[i] = binary.BigEndian.Uint64(buf[i*UINT64_SIZE : (i+1)*UINT64_SIZE])
	}
	return true, winners, nil
}
