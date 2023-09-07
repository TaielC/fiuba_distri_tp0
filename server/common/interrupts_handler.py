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


def try_except_interrupt(func):
    """
    Decorator for handling KeyboardInterrupt and TerminationSignal exceptions

    Can be used in combination to @with_pool to propagate the termination process
    """

    def wrapper(*args, **kwargs):
        set_sigterm_handler()
        try:
            return func(*args, **kwargs)
        except (KeyboardInterrupt, TerminationSignal) as e:
            if 'pool' in kwargs:
                logging.debug("InterruptsHandler: Terminating pool")
                kwargs['pool'].terminate()
            logging.info(f"Interrupt received. Stopping execution {e}")

    return wrapper
