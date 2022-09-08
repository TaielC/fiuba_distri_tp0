import logging
from multiprocessing.pool import AsyncResult, Pool
import os
import socket
from typing import Dict


from .interrupts_handler import try_except_interrupt
from .client_handler import handle_client_connection
from .pool import with_pool


class Server:
    def __init__(self, port, listen_backlog, timeout, thread_pool_size):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._thread_pool_size = thread_pool_size
        self._server_socket.settimeout(timeout)
        self._server_socket.bind(("", port))
        self._server_socket.listen(listen_backlog)
        self._running_tasks: Dict[str, AsyncResult] = {}

    def run(self):
        """
        Server loop
        """

        @with_pool(self._thread_pool_size)
        @try_except_interrupt
        def run_loop(pool: Pool = None):
            while True:
                try:
                    client_sock, addr = self.__accept_new_connection()
                    res = pool.apply_async(
                        handle_client_connection, args=(client_sock,)
                    )
                    self._running_tasks[addr] = res
                except socket.timeout:
                    self.check_done()

        logging.info("[ServerThread] STARTED")
        try:
            run_loop()
        finally:
            self._shutdown()
            logging.info("[ServerThread] Shutting down")
            self.check_done(True)

    def check_done(self, wait=False):
        to_delete = []
        for addr, task in self._running_tasks.items():
            if not wait and not task.ready():
                continue
            to_delete.append(addr)
            try:
                client, request_type = task.get()
                logging.info(f"[ServerThread] Client {client} finished {request_type}")
            except Exception as e:
                logging.error(f"[ServerThread] Error processing {addr}: {e}")
        for addr in to_delete:
            self._running_tasks.pop(addr)

    def _shutdown(self):
        """
        Shutdown server

        Close server socket and wait for all threads to finish
        """
        self._server_socket.close()
        logging.debug("[ServerThread] Socket closed")

    def __accept_new_connection(self):
        """
        Accept new connections
        """
        logging.debug("[ServerThread] Proceed to accept new connections")
        c, addr = self._server_socket.accept()
        logging.info("[ServerThread] Got connection from {}".format(addr))
        return c, addr
