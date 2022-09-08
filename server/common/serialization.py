import datetime
import logging
from socket import socket
import time
from typing import List, Optional
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


""" Serialization and Deserialization of Buisness Logic """


def recv_is_load_request(sock: socket):
    return bool(recv_int(sock, int_size=8))


def recv_client_name(sock: socket):
    return recv_string(sock)


def recv_batch(sock: socket) -> Optional[List[Contestant]]:
    count = recv_int(sock)
    if count == 0:
        return None
    return [create_contestant_from_socket(sock) for _ in range(count)]


def send_winners(sock: socket, winners: List[bool]):
    send_int(sock, len(winners))
    for winner in winners:
        send_int(sock, int(winner), int_size=8)


def create_contestant_from_socket(sock: socket):
    c = Contestant(
        recv_string(sock),
        recv_string(sock),
        recv_int(sock, int_size=64),
        recv_string(sock),
    )
    return c
