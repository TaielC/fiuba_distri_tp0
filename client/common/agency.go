package common

import (
	"strconv"
)

type Agency struct {
	Id string
}

func (a Agency) CreateCupon(firstName string, lastName string, id_str string, birthDate string, number_str string) Cupon {
	id, err := strconv.ParseUint(id_str, 10, 32)
	if err != nil {
		panic(err)
	}
	number, err := strconv.ParseUint(number_str, 10, 32)
	if err != nil {
		panic(err)
	}
	return Cupon{a.Id, firstName, lastName, id, birthDate, number}
}
