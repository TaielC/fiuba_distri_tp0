import csv
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

def send_int(sock: socket, i: int, int_size=32):
    sock.sendall(i.to_bytes(int_size // 8, "big"))


def recv_string(sock: socket):
    s = recv_all(
        sock,
        recv_int(sock),
    ).decode()
    return s


def recv_int(sock: socket, int_size=32):
    b = recv_all(sock, int_size // 8)
    i = int.from_bytes(b, byteorder="big")
    return i


""" Bets storage location. """
STORAGE_FILEPATH = "./bets.csv"
""" Simulated winner number in the lottery contest. """
LOTTERY_WINNER_NUMBER = 7574


""" A lottery bet registry. """
class Bet:
    def __init__(self, agency: str, first_name: str, last_name: str, document: str, birthdate: str, number: str):
        """
        agency must be passed with integer format.
        birthdate must be passed with format: 'YYYY-MM-DD'.
        number must be passed with integer format.
        """
        self.agency = int(agency)
        self.first_name = first_name
        self.last_name = last_name
        self.document = document
        self.birthdate = datetime.date.fromisoformat(birthdate)
        self.number = int(number)

""" Checks whether a bet won the prize or not. """
def has_won(bet: Bet) -> bool:
    return bet.number == LOTTERY_WINNER_NUMBER

"""
Persist the information of each bet in the STORAGE_FILEPATH file.
Not thread-safe/process-safe.
"""
def store_bets(bets: list[Bet]) -> None:
    with open(STORAGE_FILEPATH, 'a+') as file:
        writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL)
        for bet in bets:
            writer.writerow([bet.agency, bet.first_name, bet.last_name,
                             bet.document, bet.birthdate, bet.number])

"""
Loads the information all the bets in the STORAGE_FILEPATH file.
Not thread-safe/process-safe.
"""
def load_bets() -> list[Bet]:
    with open(STORAGE_FILEPATH, 'r') as file:
        reader = csv.reader(file, quoting=csv.QUOTE_MINIMAL)
        for row in reader:
            yield Bet(row[0], row[1], row[2], row[3], row[4], row[5])


def recv_batch(sock: socket) -> list:
    count = recv_int(sock)
    if count == 0:
        return None
    return [create_contestant_from_socket(sock) for _ in range(count)]


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

    def __repr__(self) -> str:
        return str(self)


def create_contestant_from_socket(sock: socket):
    c = Contestant(
        recv_string(sock),
        recv_string(sock),
        recv_int(sock, int_size=64),
        recv_string(sock),
    )
    return c


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
