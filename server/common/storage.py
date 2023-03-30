""" Winners storage location. """
import logging
from pathlib import Path
from typing import Iterable, List

from .utils import Bet

STORAGE = Path("/winners")


def set_as_working(client: str, set: bool) -> None:
    """Set the client as working."""
    path = STORAGE / client
    if not path.exists():
        path.mkdir(parents=True)
    with open(path / "working", "w") as file:
        file.write("1" if set else "0")


def is_working(client: str) -> bool:
    """Check if a client is working."""
    path = STORAGE / client / "working"
    if not path.exists():
        return False
    with open(path, "r") as file:
        return bool(int(file.read()))


def persist_winners(winners: Iterable[Bet], client: str) -> None:
    """Persist the information of each winner in the STORAGE file. Not thread-safe/process-safe."""
    path = STORAGE / client
    if not path.exists():
        path.mkdir(parents=True)
    count = 0
    with open(path / "results.csv", "a") as file:
        for winner in winners:
            count += 1
            file.write(
                f'{winner.first_name} {winner.last_name} | {winner.document} | {winner.birthdate.strftime("%d/%m/%Y")}\n'
            )
    try:
        with open(path / "total", "r+") as file:
            previous = int(file.read())
            file.seek(0)
            file.write(str(count + previous))
    except FileNotFoundError:
        with open(path / "total", "w") as file:
            file.write(str(count))
    return


def get_registered_clients():
    """Run through the storage directory and return the list of registered clients."""
    return [f.name for f in STORAGE.iterdir() if f.is_dir()]


def get_winners_count_all() -> int:
    registered_clients = get_registered_clients()
    total = sum(get_winners_count(c, False) for c in registered_clients)
    if any(is_working(c) for c in registered_clients):
        return -total
    return total


def get_winners_count(client: str, check_active=False) -> int:
    """Get the number of winners for a specific client."""
    if client == "*":
        return get_winners_count_all()
    path = STORAGE / client / "total"
    if not path.exists():
        return 0
    with open(path, "r") as file:
        count = int(file.read())
    if check_active and is_working(client):
        return -count
    return count
