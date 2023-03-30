SHELL := /bin/bash
PWD := $(shell pwd)

CLIENTS = 5
GIT_REMOTE = github.com/7574-sistemas-distribuidos/docker-compose-init

-include .env

default: build

all:

deps:
	go mod tidy
	go mod vendor

build: deps
	GOOS=linux go build -o bin/client $(GIT_REMOTE)/client
.PHONY: build

docker-image:
	# Use CLIENTS=<number> to set the number of clients (default 1)
	./scripts/compose_multiple_clients.py ${CLIENTS}
	docker build -f ./server/Dockerfile -t "server:latest" .
	docker build -f ./client/Dockerfile -t "client:latest" .
	# Execute this command from time to time to clean up intermediate stages generated 
	# during client build (your hard drive will like this :) ). Don't left uncommented if you 
	# want to avoid rebuilding client image every time the docker-compose-up command 
	# is executed, even when client code has not changed
	# docker rmi `docker images --filter label=intermediateStageToBeDeleted=true -q`
.PHONY: docker-image

docker-compose-up: docker-image
	docker compose -f docker-compose-dev.yaml up -d --build
.PHONY: docker-compose-up

docker-compose-stop:
	docker-compose -f docker-compose-dev.yaml stop -t 1
.PHONY: docker-compose-stop

docker-compose-down: docker-compose-stop
	docker-compose -f docker-compose-dev.yaml down
.PHONY: docker-compose-down

docker-compose-logs:
	docker compose -f docker-compose-dev.yaml logs -f
.PHONY: docker-compose-logs
