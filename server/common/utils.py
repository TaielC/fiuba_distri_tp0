import logging
from socket import socket
import time
import datetime

""" Recv all from socket """


def recv_all(sock: socket, length: int) -> bytearray:
    """
    Receive all data from socket
    """

    data = b""
    while len(data) < length:
        packet = sock.recv(length - len(data))
        if not packet:
            raise ConnectionError("Connection closed")
        data += packet
    return data


""" Serialization and Deserialization """


def recv_string(sock):
    s = recv_all(
        sock,
        recv_uint(sock),
    ).decode()
    return s


def recv_uint(sock, int_size=32):
    b = recv_all(sock, int_size // 8)
    i = int.from_bytes(b, byteorder="big")
    return i


""" Winners storage location. """
STORAGE = "./winners"


""" Contestant data model. """


class Contestant:
    def __init__(self, first_name, last_name, document, birthdate):
        """Birthdate must be passed with format: 'YYYY-MM-DD'."""
        self.first_name = first_name
        self.last_name = last_name
        self.document = document
        self.birthdate = datetime.datetime.strptime(birthdate, "%Y-%m-%d")

    def tuple(self):
        return (self.first_name, self.last_name, self.document, self.birthdate)

    def __hash__(self):
        return hash(self.tuple())

    def __str__(self):
        return str(self.tuple())


def create_contestant_from_socket(sock):
    return Contestant(
        recv_string(sock),
        recv_string(sock),
        recv_uint(sock, int_size=64),
        recv_string(sock),
    )


""" Checks whether a contestant is a winner or not. """


def is_winner(contestant: Contestant) -> bool:
    # Simulate strong computation requirements using a sleep to increase function retention and force concurrency.
    time.sleep(0.001)
    return hash(contestant) % 17 == 0


""" Persist the information of each winner in the STORAGE file. Not thread-safe/process-safe. """


def persist_winners(winners: list[Contestant]) -> None:
    with open(STORAGE, "a+") as file:
        for winner in winners:
            file.write(
                f'Full name: {winner.first_name} {winner.last_name} | Document: {winner.document} | Date of Birth: {winner.birthdate.strftime("%d/%m/%Y")}\n'
            )
