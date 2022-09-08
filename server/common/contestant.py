
""" Contestant data model. """
from datetime import datetime


class Contestant:
    def __init__(self, first_name, last_name, document, birthdate):
        """Birthdate must be passed with format: 'YYYY-MM-DD'."""
        self.first_name = first_name
        self.last_name = last_name
        self.document = document
        self.birthdate = datetime.strptime(birthdate, "%Y-%m-%d")

    def tuple(self):
        return (self.first_name, self.last_name, self.document, self.birthdate)

    def __hash__(self):
        return hash(self.tuple())

    def __str__(self):
        return str(self.tuple())

    def __repr__(self) -> str:
        return str(self)
