""" Checks whether a contestant is a winner or not. """
import time


def is_winner(self) -> bool:
    # Simulate strong computation requirements using a sleep to increase function retention and force concurrency.
    # time.sleep(0.001)
    return hash(self) % 17 == 0
