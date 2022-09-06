import signal
import socket
import logging
from threading import Event

class TerminationSignal(Exception):
    pass


def _set_sigterm_handler():
    """
    Setup SIGTERM signal handler. Raises StopServer exception when SIGTERM
    signal is received
    """
    def signal_handler(_signum, _frame):
        logging.info("SIGTERM received")
        raise TerminationSignal()

    signal.signal(signal.SIGTERM, signal_handler)


class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)

    def run(self, set_sigterm_handler=True):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """
        if set_sigterm_handler:
            _set_sigterm_handler()
        
        try:
            while True:
                client_sock = self.__accept_new_connection()
                self.__handle_client_connection(client_sock)
        # Handle SIGINT signal
        except (KeyboardInterrupt, TerminationSignal) as e:
            logging.info(f"Interrupt received. Stopping server {e}")
        
        self._shutdown()

    def _stay_alive(self):
        return not self.shutdown_event.is_set()

    def _shutdown(self):
        """
        Shutdown server

        Close server socket and wait for all threads to finish
        """
        logging.info("Shutting down server")
        self._server_socket.close()

    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            msg = client_sock.recv(1024).rstrip().decode('utf-8')
            logging.info(
                'Message received from connection {}. Msg: {}'
                .format(client_sock.getpeername(), msg))
            client_sock.send("Your Message has been received: {}\n".format(msg).encode('utf-8'))
        except OSError:
            logging.info("Error while reading socket {}".format(client_sock))
        finally:
            client_sock.close()

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info("Proceed to accept new connections")
        c, addr = self._server_socket.accept()
        logging.info('Got connection from {}'.format(addr))
        return c
