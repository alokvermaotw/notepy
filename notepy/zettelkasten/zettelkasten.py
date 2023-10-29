from __future__ import annotations
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Optional, Sequence
import sqlite3
from notepy.zettelkasten import Note, BaseNote
from notepy.cli import Git
from tempfile import NamedTemporaryFile
import subprocess


_MAIN_TABLE_STMT = """CREATE TABLE index(zk_id,
                   title,
                   author,
                   date,
                   tags,
                   links,
                   PRIMARY KEY(zk_id))"""
_INSERT_STMT = "INSERT INTO index VALUES (?, ?, ?, ?, ?, ?)"
_DELETE_STMT = "DELETE FROM index WHERE zk_id = ?"


# TODO: implement an abstract class for this.
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
    note_obj: Note = Note
    delimiter: str = "---"
    header: str = "# "
    link_del: (str, str) = ('[[', ']]')
    special_values: tuple[str] = ('date', 'tags')

    def __post_init__(self) -> None:
        self.vault = Path(self.vault).expanduser()
        self.header_obj = [note_field.name
                           for note_field in fields(self.note_obj)
                           if note_field.name not in ['links', 'frontmatter', 'body']]

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
        :param git_init: whether to initialize a git repo.
        :param force: whether to force initialization.
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
            git.save()
            zk_args['git'] = git

        return cls(**zk_args)

    @staticmethod
    def is_zettelkasten(path: str | Path) -> bool:
        """
        Check whether provided path is already a vault.

        :param path: path to the vault.
        :return: True or False
        """
        path = Path(path).expanduser()
        is_zettelkasten = True
        is_zettelkasten *= path.is_dir()
        is_zettelkasten *= (path / ".index.db").is_file()
        is_zettelkasten *= (path / "scratchpad").is_dir()
        is_zettelkasten *= (path / ".last").is_file()

        return bool(is_zettelkasten)

    def add(self, note: BaseNote) -> None:
        """
        Add a new note to the vault
        """
        # parsing_objects = [obj.name for obj in fields()]
        pass

    # TODO: should we ask for confirmation here or in a higher level module?
    # TODO: use a higher level editor_wrapper instead of hx
    def new(self,
            title: str,
            author: str,
            to_scratchpad: bool = False,
            confirmation: bool = False) -> None:
        """
        Create a new note and add it to the vault.

        :param title: title of the note.
        :param author: author of the note.
        :param to_scratchpad: whether the note should go to the scratchpad.
        :param confirmation: whether to ask for confirmation to save the note.
        """
        tmp_note = self.note_obj.new(title, author)
        filename = Path(tmp_note.zk_id).with_suffix(".md")
        scratchpad = (self.vault / "scratchpad")
        scratchpad.mkdir(exist_ok=True)

        with NamedTemporaryFile("r+", dir=scratchpad, suffix=".md") as f:
            f.write(tmp_note.materialize())
            f.seek(0)
            subprocess.run(['hx', f.name],
                           cwd=self.vault)

            if confirmation:
                location = "vault" if not to_scratchpad else "scratchpad"
                response = input(f"Save to {location}? [Y/n]: ")
                if response.lower() in ['n', 'no', 'nope']:
                    return None

            # TODO: consider whether opening two handles to same file is good idea
            new_note = self.note_obj.read(path=f.name,
                                          parsing_obj=self.header_obj,
                                          delimiter=self.delimiter,
                                          special_names=self.special_values,
                                          header=self.header,
                                          link_del=self.link_del)
        if to_scratchpad:
            # create scratchpad if it doesn't exist
            note_path = scratchpad / filename
        else:
            note_path = self.vault / filename
            self.add(new_note)

        with open(note_path, "w") as f:
            f.write(new_note.materialize())

        if self.git:
            self.git.save()


class ZettelkastenException(Exception):
    """Main exception raised by Zettelkasten"""
