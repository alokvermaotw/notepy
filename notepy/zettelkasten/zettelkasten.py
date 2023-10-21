from dataclasses import fields
from pathlib import Path
import sqlite3


class Zettelkasten:
    vault: Path
    database: sqlite3.Connection

    def read(cls, path: Path):
        parsing_objects = [obj.name for obj in fields(cls)]