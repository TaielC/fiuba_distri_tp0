""" Winners storage location. """
from typing import List

from .contestant import Contestant

STORAGE = "./winners"


def persist_winners(winners: List[Contestant]) -> None:
    """Persist the information of each winner in the STORAGE file. Not thread-safe/process-safe."""
    with open(STORAGE, "a+") as file:
        for winner in winners:
            file.write(
                f'Full name: {winner.first_name} {winner.last_name} | Document: {winner.document} | Date of Birth: {winner.birthdate.strftime("%d/%m/%Y")}\n'
            )
