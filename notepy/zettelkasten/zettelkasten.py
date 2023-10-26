from __future__ import annotations
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Optional
import warnings
import sqlite3
from ..parser.parser import HeaderParser, BodyParser
from notes import Note
from ..cli.git_wrapper import Git


@dataclass
class Zettelkasten:
    """
    Zettelkasten manager object. Manages notes, database and repo.

    :param vault: the path to the vault (dir containing the data).
    :param index: the connection to the database.
    :param git: whether the vault is a git repo.
    """
    vault: Path
    index: sqlite3.Connection
    git: Optional[bool] = False

    def __post_init__(self) -> None:
        if not self.vault.is_dir():
            raise ZettelkastenException(f"Vault '{self.vault}' is not a directory "
                                        "or does not exist.")
        if self.git:
            git_repo = self.vault.parent.joinpath(".git")
            if not git_repo.is_dir():
                raise ZettelkastenException(f"Vault '{self.vault}' is not a git repo!")

    @classmethod
    def initialize(cls,
                   path: Path,
                   git: Optional[bool] = False,
                   force: bool = False) -> Zettelkasten:
        """
        Initialize a new vault. A vault is made of a collection of
        notes, an sqlite database (.index.db), and an optional
        git repository.

        :param path: path to the new vault.
        :param git: whether to initialize a git repo.
        :return: a new Zettelkasten object
        """

        if path.exists() and not force:
            raise ZettelkastenException(f"'{path}' already exists! Use 'force=True'"
                                        "to force the creation of the vault.")

        index = path.parent.joinpath(".index.db")
        conn = sqlite3.connect(index)



    def add(self, path: Path) -> None:
        """
        Add a new note to the vault
        """
        # parsing_objects = [obj.name for obj in fields()]
        pass


class ZettelkastenException(Exception):
    """Main exception raised by Zettelkasten"""
