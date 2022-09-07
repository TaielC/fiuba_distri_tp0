package common

import (
	"encoding/csv"
	"os"
)

type DataReader struct {
	Reader    *csv.Reader
	File      os.File
	BatchSize int
	IsAtEnd   bool
}

func NewDataReader(path string, batchSize int) *DataReader {
	file, err := os.OpenFile(path, os.O_RDONLY, os.FileMode(0644))
	if err != nil {
		panic(err)
	}
	reader := csv.NewReader(file)

	return &DataReader{
		Reader:    reader,
		File:      *file,
		BatchSize: batchSize,
		IsAtEnd:   false,
	}
}

// define read batch
func (d *DataReader) ReadBatch() []Person {
	batch := make([]Person, 0)
	for i := 0; i < d.BatchSize; i++ {
		line, err := d.Reader.Read()
		if err != nil {
			d.IsAtEnd = true
			break
		}
		p := CreatePerson(
			line[1],
			line[0],
			line[2],
			line[3],
		)
		batch = append(batch, p)
	}
	return batch
}
