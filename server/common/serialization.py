import datetime
import logging
from socket import socket
import time
from typing import Iterable, List, Optional
from .utils import Bet

""" Recv all from socket """


def try_except_os_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except OSError as e:
            logging.info(f"Error while reading socket: {e}")

    return wrapper


@try_except_os_error
def recv_all(sock: socket, length: int) -> bytes:
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


""" Serialization and Deserialization of basic types """


BYTE_SIZE = 8
INT32_SIZE = 32
INT8_SIZE = 8
INT_BYTEORDER = "big"
INT64_SIZE = 64


@try_except_os_error
def send_int(sock: socket, i: int, int_size=INT32_SIZE, signed=False):
    sock.sendall(
        i.to_bytes(int_size // BYTE_SIZE, byteorder=INT_BYTEORDER, signed=signed)
    )


def recv_string(sock: socket):
    s = recv_all(
        sock,
        recv_int(sock),
    ).decode()
    return s


def recv_int(sock: socket, int_size=INT32_SIZE):
    b = recv_all(sock, int_size // BYTE_SIZE)
    i = int.from_bytes(b, byteorder=INT_BYTEORDER)
    return i


""" Serialization and Deserialization of Buisness Logic """


def recv_is_load_request(sock: socket):
    return bool(recv_int(sock, int_size=INT8_SIZE))


def recv_client_name(sock: socket):
    return recv_string(sock)


def create_bet_from_socket(sock: socket):
    c = Bet(
        agency=recv_string(sock),
        first_name=recv_string(sock),
        last_name=recv_string(sock),
        document=str(recv_int(sock, int_size=INT64_SIZE)),
        birthdate=recv_string(sock),
        number=str(recv_int(sock, int_size=INT64_SIZE)),
    )
    return c


def recv_batch(sock: socket) -> Optional[List[Bet]]:
    count = recv_int(sock)
    if count == 0:
        return None
    return [create_bet_from_socket(sock) for _ in range(count)]


def send_response(sock: socket, count: int):
    send_int(sock, count, int_size=INT32_SIZE)



def send_winners(sock: socket, winners: Optional[List[int]]):
    if winners is None:
        send_int(sock, -1, int_size=INT64_SIZE, signed=True)
        return

    send_int(sock, len(winners), int_size=INT64_SIZE)
    bytes = b""
    for w in winners:
        bytes += w.to_bytes(INT64_SIZE, byteorder=INT_BYTEORDER, signed=False)
    sock.sendall(bytes)
