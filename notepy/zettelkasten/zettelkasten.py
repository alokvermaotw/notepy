from __future__ import annotations
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Optional
import warnings
import sqlite3
from notepy.parser.parser import HeaderParser, BodyParser
from notepy.zettelkasten.notes import Note
from notepy.cli.git_wrapper import Git


_MAIN_TABLE = ""


@dataclass
class Zettelkasten:
    """
    Zettelkasten manager object. Manages notes, database and repo.

    :param vault: the path to the vault (dir containing the data).
    :param index: the connection to the database.
    :param git: whether the vault is a git repo.
    """
    vault: Path | str
    index: sqlite3.Connection
    git: Optional[Git] = None

    def __post_init__(self) -> None:
        self.vault = Path(self.vault).expanduser()
        if not self.vault.is_dir():
            raise ZettelkastenException(f"Vault '{self.vault}' is not a directory "
                                        "or does not exist.")

    @classmethod
    def initialize(cls,
                   path: str | Path,
                   git_init: bool = False,
                   force: bool = False) -> Zettelkasten:
        """
        Initialize a new vault. A vault is made of a collection of
        notes, an sqlite database (.index.db), and an optional
        git repository.

        :param path: path to the new vault.
        :param git: whether to initialize a git repo.
        :return: a new Zettelkasten object
        """

        path = Path(path).expanduser()

        # check if a zettelkasten has been already initialized
        if cls.is_zettelkasten(path) and not force:
            raise ZettelkastenException(f"'{path}' has already been initialized!"
                                        "use 'force=True' to force re-initialization")

        zk_args = {}

        # create vault
        path.mkdir(exist_ok=True)
        zk_args['vault'] = path

        # create .last file
        last = path / ".last"
        last.touch()

        # create connection
        index = path / ".index.db"
        conn = sqlite3.connect(index)
        zk_args['index'] = conn

        # create scratchpad
        scratchpad = path / 'scratchpad'
        scratchpad.mkdir(exist_ok=True)

        # create git repo
        if git_init:
            to_ignore = ['.last', '.index.db', 'scratchpad']
            git_path = path / ".git"
            git = Git(path) if git_path.exists() else Git.init(path, to_ignore=to_ignore)
            zk_args['git'] = git

        return cls(**zk_args)

    @staticmethod
    def is_zettelkasten(path: str | Path) -> bool:
        path = Path(path).expanduser()
        is_zettelkasten = True
        is_zettelkasten *= path.is_dir()
        is_zettelkasten *= (path / ".index.db").is_file()
        is_zettelkasten *= (path / "scratchpad").is_dir()
        is_zettelkasten *= (path / ".last").is_file()

        return bool(is_zettelkasten)
        
    def add(self, path: Path) -> None:
        """
        Add a new note to the vault
        """
        # parsing_objects = [obj.name for obj in fields()]
        pass


class ZettelkastenException(Exception):
    """Main exception raised by Zettelkasten"""
