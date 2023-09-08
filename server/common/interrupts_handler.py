import signal
import logging


class TerminationSignal(Exception):
    pass


def set_sigterm_handler():
    """
    Setup SIGTERM signal handler. Raises StopServer exception when SIGTERM
    signal is received
    """

    def signal_handler(_signum, _frame):
        logging.info("SIGTERM received")
        raise TerminationSignal("SIGTERM received")

    signal.signal(signal.SIGTERM, signal_handler)
