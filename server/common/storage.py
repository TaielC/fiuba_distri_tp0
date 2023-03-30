""" Winners storage location. """
import logging
import os
from pathlib import Path
import time
from typing import List

from .utils import Bet, has_won, load_bets, store_bets

STORAGE = Path("/data")


def lock_file(path: Path):
    """Lock file decorator"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            while True:
                try:
                    f = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                    break
                except (FileExistsError, OSError):
                    time.sleep(0.5)
            try:
                return func(*args, **kwargs)
            finally:
                os.close(f)
                os.remove(path)

        return wrapper

    return decorator


def reset_workdir():
    """Clean:
    - /data/bets.csv
    - /data/lock
    - /data/working/*
    """
    if STORAGE.exists():
        for file in STORAGE.iterdir():
            if file.name == "bets.csv":
                file.unlink()
            elif file.name == "lock":
                file.unlink()
            elif file.name == "working":
                for client in file.iterdir():
                    client.unlink()
                file.rmdir()
    else:
        STORAGE.mkdir(parents=True)


def set_is_done(client: str, is_done: bool) -> None:
    """Set the client as working."""
    path = STORAGE / "working"
    if not path.exists():
        path.mkdir(parents=True)
    with open(path / client, "w") as file:
        file.write("0" if is_done else "1")


def are_all_done() -> bool:
    """Check if all clients are done."""
    return all(is_done(c) for c in get_registered_clients())



def is_done(client: str) -> bool:
    """Check if a client is working."""
    path = STORAGE / "working" / client
    if not path.exists():
        return False
    with open(path, "r") as file:
        return bool(int(file.read()))


@lock_file(STORAGE / "lock")
def persist_batch(bets: List[Bet], client: str) -> None:
    store_bets(bets)


def get_registered_clients():
    """Run through the storage directory and return the list of registered clients."""
    return [f.name for f in (STORAGE / "working").iterdir() if f.is_dir()]


def get_winners(client: str) -> List[int]:
    """Get the number of winners for a specific client."""

    winners = list(
        map(
            lambda b: int(b.document),
            filter(lambda b: b.agency == int(client) and has_won(b), load_bets()),
        )
    )
    return winners
