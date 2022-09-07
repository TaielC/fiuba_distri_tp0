package common

import (
	"encoding/binary"
	"strconv"

	log "github.com/sirupsen/logrus"
)

type Person struct {
	FirstName string
	LastName  string
	Id        uint64
	BirthDate string
}

const UINT64_SIZE = 8

func CreatePerson(firstName string, lastName string, id string, birthDate string) Person {
	id_uint64, err := strconv.ParseUint(id, 10, 32)
	if err != nil {
		panic(err)
	}
	return Person{firstName, lastName, id_uint64, birthDate}
}

// Serialize a string as its length and then the string
func SerializeString(str string) []byte {
	serialized_string := []byte(str)
	size := len(serialized_string)
	buf := make([]byte, size+4)
	binary.BigEndian.PutUint32(buf, uint32(size))
	copy(buf[4:], serialized_string)
	return buf
}

func (p Person) Serialize() []byte {
	firstName := SerializeString(p.FirstName)
	lastName := SerializeString(p.LastName)
	id := make([]byte, UINT64_SIZE)
	binary.BigEndian.PutUint64(id, p.Id)
	birthDate := SerializeString(p.BirthDate)
	buf := make([]byte, len(firstName)+len(lastName)+len(id)+len(birthDate))
	copy(buf, firstName)
	copy(buf[len(firstName):], lastName)
	copy(buf[len(firstName)+len(lastName):], id)
	copy(buf[len(firstName)+len(lastName)+len(id):], birthDate)
	log.Debugf("Serialized person %v", buf)
	return buf
}
