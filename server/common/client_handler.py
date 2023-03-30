import logging
from os import getpid
from socket import socket, timeout as SocketTimeout
from typing import List, Iterable, Tuple


from .interrupts_handler import TerminationSignal, set_sigterm_handler
from .serialization import (
    recv_is_load_request,
    recv_client_name,
    recv_batch,
    send_winners,
    send_winners_count,
)
from .storage import get_winners_count, persist_winners, set_as_working
from .utils import has_won, Bet


def handle_client_connection(sock: socket) -> Tuple[str, str]:
    """
    Handle client connection
    """
    set_sigterm_handler()
    try:
        return _handle_client_connection(sock)
    except (KeyboardInterrupt, TerminationSignal) as e:
        logging.info(f"[HandlerThread {getpid()}] Interrupted: {e}")
        return "", ""
    finally:
        logging.debug(f"[HandlerThread {getpid()}] Closing client socket")
        sock.close()


def _handle_client_connection(sock: socket) -> Tuple[str, str]:
    """
    Read message from a specific client socket and closes the socket

    If a problem arises in the communication with the client, the
    client socket will also be closed
    """

    client = None
    request_type = None
    try:
        is_load_request = recv_is_load_request(sock)
        client = recv_client_name(sock)
        if is_load_request:
            request_type = "load"
            handle_load_request(sock, client)
        else:
            request_type = "query"
            handle_query_request(sock, client)
        return client, request_type
    except (SocketTimeout, ConnectionResetError) as e:
        logging.error(
            f"[HandlerThread {getpid()}] Error while handling {request_type} request from {client}: {e}"
        )
        return "", ""


def process_batch(client, batch: Iterable[Bet]) -> List[bool]:
    """
    Process a batch of contestants.
    """
    winners = [has_won(c) for c in batch]
    persist_winners((c for c, w in zip(batch, winners) if w), client)
    return winners


def handle_load_request(sock: socket, client: str):
    """
    Handle load request from client
    """
    logging.info(f"[HandlerThread {getpid()}] LOAD from {client}")

    try:
        set_as_working(client, True)

        total = 0
        batches = 0
        while True:
            # Syncronic batch behavior
            batch = recv_batch(sock)
            if batch is None:
                break
            winners = process_batch(client, batch)
            send_winners(sock, winners)
            batches += 1
            total += len(batch)

        logging.info(
            f"[HandlerThread {getpid()}] Received {total} records in {batches} batches from {client}"
        )
    finally:
        set_as_working(client, False)


def handle_query_request(sock: socket, client: str):
    """
    Handle query request from client
    """
    logging.info(f"[HandlerThread {getpid()}] QUERY from {client}")

    winners_count = get_winners_count(client)
    send_winners_count(sock, winners_count)
