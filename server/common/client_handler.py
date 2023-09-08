import logging
from os import getpid
from socket import socket, timeout as SocketTimeout
from typing import List, Iterable, Tuple


from .interrupts_handler import TerminationSignal, set_sigterm_handler
from .serialization import (
    recv_is_load_request,
    recv_client_name,
    recv_batch,
    send_response,
    send_winners,
)
from .storage import are_all_done, get_winners, persist_batch, set_is_done
from .utils import has_won, Bet


def handle_client_connection(sock: socket) -> Tuple[str, str]:
    """
    Handle client connection
    """
    try:
        return _handle_client_connection(sock)
    except (KeyboardInterrupt, TerminationSignal) as e:
        logging.info(f"[HandlerThread {getpid()}] Interrupted: {e}")
        return "", ""
    finally:
        logging.info(f"[HandlerThread {getpid()}] Closing client socket")
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


def process_batch(client, batch: List[Bet]) -> List[bool]:
    """
    Process a batch of contestants.
    """
    persist_batch(batch, client)
    winners = [has_won(c) for c in batch]
    return winners


def handle_load_request(sock: socket, client: str):
    """
    Handle load request from client
    """
    logging.info(f"[HandlerThread {getpid()}] LOAD from {client}")

    try:
        set_is_done(client, True)

        total = 0
        batches = 0
        while True:
            # Syncronic batch behavior
            batch = recv_batch(sock)
            if batch is None:
                break
            process_batch(client, batch)
            send_response(sock, len(batch))
            batches += 1
            total += len(batch)

        logging.info(
            f"[HandlerThread {getpid()}]"
            " action: apuestas_almacenadas | result: success "
            f"| agencia: {client} | apuestas: {total}"
        )
    finally:
        set_is_done(client, False)


def handle_query_request(sock: socket, client: str):
    """
    Handle query request from client
    """
    logging.info(f"[HandlerThread {getpid()}] QUERY from {client}")
    if not are_all_done():
        send_response(sock, -1)
        return

    winners = get_winners(client)
    send_winners(sock, winners)
