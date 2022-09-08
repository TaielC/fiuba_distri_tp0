import datetime
import logging
from socket import socket
import time
from typing import Iterable, List, Optional
from .contestant import Contestant

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


""" Serialization and Deserialization of basic types """


BYTE_SIZE = 8
UINT32_SIZE = 32
UINT8_SIZE = 8
INT_BYTEORDER = "big"
UINT64_SIZE = 64


def send_int(sock: socket, i: int, int_size=UINT32_SIZE):
    sock.sendall(i.to_bytes(int_size // BYTE_SIZE, byteorder=INT_BYTEORDER))


def recv_string(sock: socket):
    s = recv_all(
        sock,
        recv_int(sock),
    ).decode()
    return s


def recv_int(sock: socket, int_size=UINT32_SIZE):
    b = recv_all(sock, int_size // BYTE_SIZE)
    i = int.from_bytes(b, byteorder=INT_BYTEORDER)
    return i


""" Serialization and Deserialization of Buisness Logic """

ID_SIZE = UINT64_SIZE


def recv_is_load_request(sock: socket):
    return bool(recv_int(sock, int_size=UINT8_SIZE))


def recv_client_name(sock: socket):
    return recv_string(sock)


def create_contestant_from_socket(sock: socket):
    c = Contestant(
        recv_string(sock),
        recv_string(sock),
        recv_int(sock, int_size=ID_SIZE),
        recv_string(sock),
    )
    return c


def recv_batch(sock: socket) -> Optional[Iterable[Contestant]]:
    count = recv_int(sock)
    if count == 0:
        return None
    return [create_contestant_from_socket(sock) for _ in range(count)]


def send_winners(sock: socket, winners: List[bool]):
    send_int(sock, len(winners))
    for winner in winners:
        send_int(sock, int(winner), int_size=8)


def send_winners_count(sock: socket, winners_count: int):
    send_int(sock, winners_count)
