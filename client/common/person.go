package common

import (
	"encoding/binary"
)

type Cupon struct {
	AgencyId  string
	FirstName string
	LastName  string
	Id        uint64
	BirthDate string
	Number    uint64
}

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

func (c Cupon) Serialize() []byte {
	agency := SerializeString(c.AgencyId)
	firstName := SerializeString(c.FirstName)
	lastName := SerializeString(c.LastName)
	id := make([]byte, UINT64_SIZE)
	binary.BigEndian.PutUint64(id, c.Id)
	birthDate := SerializeString(c.BirthDate)
	number := make([]byte, UINT64_SIZE)
	binary.BigEndian.PutUint64(number, c.Number)
	buf := make([]byte, len(agency)+len(firstName)+len(lastName)+len(id)+len(birthDate)+len(number))
	copy(buf, agency)
	copy(buf[len(agency):], firstName)
	copy(buf[len(agency)+len(firstName):], lastName)
	copy(buf[len(agency)+len(firstName)+len(lastName):], id)
	copy(buf[len(agency)+len(firstName)+len(lastName)+len(id):], birthDate)
	copy(buf[len(agency)+len(firstName)+len(lastName)+len(id)+len(birthDate):], number)
	return buf
}

func SerializeBatch(batch []Cupon) []byte {
	buf := make([]byte, 4)
	binary.BigEndian.PutUint32(buf, uint32(len(batch)))
	for _, cupon := range batch {
		buf = append(buf, cupon.Serialize()...)
	}
	return buf
}
