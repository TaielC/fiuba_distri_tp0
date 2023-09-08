import logging
from multiprocessing.pool import AsyncResult, Pool
import os
import socket
from typing import Dict, Optional


from .interrupts_handler import TerminationSignal, set_sigterm_handler
from .client_handler import handle_client_connection
from .storage import reset_workdir


class Server:
    def __init__(
        self,
        port,
        listen_backlog,
        timeout,
        thread_pool_size,
        agencies_count,
    ):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._thread_pool_size = thread_pool_size
        self._agencies_count = agencies_count
        self._port = port
        self._timeout = timeout
        self._listen_backlog = listen_backlog
        self._running_tasks: Dict[str, AsyncResult] = {}

    def _accept_new_connection(self, pool):
        try:
            client_sock, addr = self.__accept_new_connection()
            res = pool.apply_async(handle_client_connection, args=(client_sock,))
            self._running_tasks[addr] = res
        except socket.timeout:
            self.check_done()

    def run(self):
        """
        Server loop
        """
        reset_workdir(self._agencies_count)
        self._server_socket.settimeout(self._timeout)
        self._server_socket.bind(("", self._port))
        self._server_socket.listen(self._listen_backlog)

        logging.info("[ServerThread] STARTED")
        pool = None
        try:
            pool = Pool(
                self._thread_pool_size,
                initializer=set_sigterm_handler,
            )
            logging.info("[ServerThread] Ready to accept new connections")
            while True:
                self._accept_new_connection(pool)
        except (KeyboardInterrupt, TerminationSignal) as e:
            logging.info(f"[ServerThread] Interrupted: {e}")
            if pool is not None:
                pool.close()
        finally:
            if pool is not None:
                pool.join()
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
                if wait:
                    print("Waiting for", addr)
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
