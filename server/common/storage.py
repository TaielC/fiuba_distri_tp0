""" Winners storage location. """
import logging
from pathlib import Path
from typing import Iterable, List

from .contestant import Contestant

STORAGE = Path("/winners")


def persist_winners(winners: Iterable[Contestant], client: str) -> None:
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


def get_winners_count(client: str) -> int:
    """Get the number of winners for a specific client."""
    if client == "*":
        return sum(get_winners_count(c) for c in get_registered_clients())
    path = STORAGE / client / "total"
    if not path.exists():
        return 0
    with open(path, "r") as file:
        return int(file.read())
