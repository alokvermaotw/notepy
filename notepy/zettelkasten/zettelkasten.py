from __future__ import annotations
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any
from collections.abc import Sequence, MutableMapping, Collection
from tempfile import NamedTemporaryFile
import subprocess
from glob import glob1
from multiprocessing import Pool
from notepy.zettelkasten.notes import Note
from notepy.wrappers.git_wrapper import Git, GitMixin
from notepy.zettelkasten.sql import DBManager


# TODO: implement an abstract class for this.
@dataclass
class Zettelkasten(GitMixin):
    """
    Zettelkasten manager object. Manages notes, database and repo.

    :param vault: the path to the vault (dir containing the data).
    :param note_obj: the type of note you're going to use.
    :param delimiter: the delimiter of the frontmatter section.
                      Defaults to '---'
    :param header: the symbol used for headers. Defaults to '# '
    :param link_del: delimiter for links. Defaults to '("[[", "]]")'
    :param special_values: values of the frontmatter
                           that require special parsing.
    """
    vault: Path
    note_obj: type[Note] = Note
    delimiter: str = "---"
    header: str = "# "
    link_del: tuple[str, str] = ('[[', ']]')
    special_values: Collection[str] = ('date', 'tags', 'zk_id')

    def __post_init__(self) -> None:
        self.vault = Path(self.vault).expanduser()
        self.index = self.vault / ".index.db"
        self.last = self.vault / ".last"
        self.scratchpad = self.vault / "scratchpad"
        self.dbmanager = DBManager(self.index)
        self.git = self._detect_git_repo(self.vault)
        self.header_obj = [note_field.name
                           for note_field in fields(self.note_obj)
                           if note_field.name not in ['links', 'frontmatter', 'body']]

        if not self.vault.is_dir():
            raise VaultError(f"Vault '{self.vault}' is not a directory "
                             "or does not exist.")

    @classmethod
    def initialize(cls,
                   path: str | Path,
                   git_init: bool = False,
                   git_origin: str = "",
                   note_obj: type[Note] = Note,
                   delimiter: str = "---",
                   header: str = "# ",
                   link_del: tuple[str, str] = ('[[', ']]'),
                   special_values: tuple[str, str] = ('date', 'tags'),
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


        # create vault
        path.mkdir(exist_ok=True)

        # create .last file
        last = path / ".last"
        last.touch()

        # create the tables
        index = path / ".index.db"
        DBManager(index).create_tables()

        # create scratchpad
        scratchpad = path / 'scratchpad'
        scratchpad.mkdir(exist_ok=True)

        # create git repo
        if git_init:
            to_ignore = ['.last', '.tmp']
            git_path = path / ".git"
            git = Git(path) if git_path.exists() else Git.init(path, to_ignore=to_ignore)
            # add origin if provided
            if git_origin:
                git.origin = git_origin
            git.save()

        zk_args: MutableMapping[str, Any] = {
            'vault': path,
            'note_obj': note_obj,
            'delimiter': delimiter,
            'header': header,
            'link_del': link_del,
            'special_values': special_values
        }
        return cls(**zk_args)

    @staticmethod
    def is_zettelkasten(path: str | Path) -> bool:
        """
        Check whether provided path is already a vault.

        :param path: path to the vault.
        :return: True or False
        """
        path = Path(path).expanduser()
        is_zettelkasten = int(True)
        is_zettelkasten *= path.is_dir()
        is_zettelkasten *= (path / ".index.db").is_file()
        is_zettelkasten *= (path / "scratchpad").is_dir()
        is_zettelkasten *= (path / ".last").is_file()

        return bool(is_zettelkasten)

    def _add_last_opened(self, name: str | Path) -> None:
        """
        Add the last opened note to .last file

        :param name: name of the note that was last opened.
        """
        with open(self.last, "w") as f:
            f.write(str(name)+"\n")

    # TODO: use a higher level editor_wrapper instead of hx
    def _edit_temporary_note(self,
                             note: Note,
                             confirmation: bool = False) -> Note | None:
        """
        Edit a note in a temporary file. The temporary file is created
        in the scratchpad so not to interfere with git. The temporary
        file is automatically deleted.

        :param note: the note to edit.
        :param confirmation: whether to ask for confirmation.
        :return: if confirmation=True and input was no,
                 return None. Else the note.
        """

        # check if scratchpad exists. We are going to create the temporary
        # note inside the scratchpad so that its creation is not
        # detected by git, since by default scratchpad is in .gitignore
        self.scratchpad.mkdir(exist_ok=True)

        with NamedTemporaryFile("w", dir=self.scratchpad, suffix=".md") as f:
            # write the note in the temporary file
            f.write(note.materialize())
            f.seek(0)
            subprocess.run(['hx', f.name],
                           cwd=self.vault)

            # TODO: consider whether opening two handles to same file is good
            # idea
            # TODO: make read arguments less implementation dependent.
            # create the note from the new data
            new_note = self.note_obj.read(path=f.name,
                                          parsing_obj=self.header_obj,
                                          delimiter=self.delimiter,
                                          special_names=self.special_values,
                                          header=self.header,
                                          link_del=self.link_del)
        # ask for confirmation
        if confirmation and not self._ask_for_confirmation():
            return None

        return new_note

    def _check_unique_title(self, note_title: str) -> None:
        all_titles = [title for zk_id, title in self.list_notes()]
        if note_title in all_titles:
            raise TitleClashError("Title is already used in another note.")

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
        # check title is unique
        self._check_unique_title(title)

        # new note
        tmp_note = self.note_obj.new(title, author)

        # create new note
        new_note = self._edit_temporary_note(tmp_note, confirmation)
        if new_note is None:
            return None

        self.scratchpad.mkdir(exist_ok=True)
        filename = Path(str(new_note.zk_id)).with_suffix(".md")

        if to_scratchpad:
            note_path = self.scratchpad / filename
        else:
            note_path = self.vault / filename
            # if not in scratchpad, add the metadata to the database
            self.dbmanager.add_to_index(new_note)

        # save the new note
        with open(note_path, "w") as f:
            f.write(new_note.materialize())

        # update .last file
        self._add_last_opened(filename)

        # add and commit
        if self.git:
            self.git.save(msg=f'Commit "{new_note.zk_id}"')

    def update(self, zk_id: int, confirmation: bool = False) -> None:
        """
        Update the note corresponding to the provded ID.

        :param zk_id: the ID of the note.
        :param confirmation: whether to ask for confirmation to save the note.
        """

        # check that the note exists
        if not self._note_exists(zk_id):
            raise ZettelkastenException(f"Note '{zk_id}' does not exist.")

        # read the note
        filename = Path(str(zk_id)).with_suffix(".md")
        note_path = self.vault / filename
        note = self.note_obj.read(path=note_path,
                                  parsing_obj=self.header_obj,
                                  delimiter=self.delimiter,
                                  special_names=self.special_values,
                                  header=self.header,
                                  link_del=self.link_del)

        new_note = self._edit_temporary_note(note, confirmation=confirmation)
        if new_note is None:
            return None

        # if id was changed, raise an error.
        if new_note.zk_id != zk_id:
            raise IDChangedError("You cannot change the ID of an existing note.")

        # if title was changed, make sure it doesn't clash
        # with other notes
        if new_note.title != note.title:
            self._check_unique_title(new_note.title)

        # save the new note
        with open(note_path, "w") as f:
            f.write(new_note.materialize())

        # update the index
        self.dbmanager.update_note_to_index(new_note)

        # update .last file
        self._add_last_opened(filename)

        # add and commit
        if self.git:
            self.git.save(msg=f'Updated "{new_note.zk_id}"')

    def delete(self, zk_id: int, confirmation: bool = False) -> None:
        """
        Delete a note.

        :param zk_id: the ID of the note to delete.
        :param confirmation: whether to ask for confirmation to save the note.
        """

        # check that the note exists
        if not self._note_exists(zk_id):
            raise ZettelkastenException(f"Note '{zk_id}' does not exist.")

        filename = Path(str(zk_id)).with_suffix(".md")
        note_path = self.vault / filename

        # ask for confirmation
        if confirmation:
            response = input("Delete note? [Y/n]: ")
            if response.lower() in ['n', 'no', 'nope']:
                return None

        # remove from index
        self.dbmanager.delete_from_index(zk_id)

        # remove note
        note_path.unlink(missing_ok=True)

        # add and commit
        if self.git:
            self.git.save(msg=f'Removed note "{zk_id}"')

    def list_notes(self) -> Sequence[tuple[int, str]]:
        results = self.dbmanager.list()

        return results

    # NOTE: maybe it could just be quicker to catch FileNotFoundError?
    def _note_exists(self, zk_id: int) -> bool:
        all_ids = [id for id, title in self.list_notes()]

        return zk_id in all_ids

    def print_note(self, zk_id: int) -> str:
        """
        Print the content of the note with the corresponding ID.

        :param zk_id: ID of the note.
        :return: content of the note.
        """
        # check that the note exists
        if not self._note_exists(zk_id):
            raise ZettelkastenException(f"Note '{zk_id}' does not exist.")

        filename = Path(str(zk_id)).with_suffix(".md")
        note_path = self.vault / filename
        note = self.note_obj.read(path=note_path,
                                  parsing_obj=self.header_obj,
                                  delimiter=self.delimiter,
                                  special_names=self.special_values,
                                  header=self.header,
                                  link_del=self.link_del)

        content = note.materialize()

        return content

    def index_vault(self) -> None:
        """
        Reindex the zettelkasten vault from scratch.
        Single threaded function.
        """
        notes_paths: list[str] = glob1(str(self.vault), "*.md")
        # drop the tables
        self.dbmanager.drop_tables()
        # create new tables
        self.dbmanager.create_tables()

        # index all the notes
        for note_path in notes_paths:
            full_path = self.vault / note_path
            note = self.note_obj.read(path=full_path,
                                      parsing_obj=self.header_obj,
                                      delimiter=self.delimiter,
                                      special_names=self.special_values,
                                      header=self.header,
                                      link_del=self.link_del)
            self.dbmanager.add_to_index(note)

        # add and commit
        if self.git:
            self.git.save(msg='Reindexed vault')

    def _read_note(self, note_path: str) -> Note:
        """
        Utility function for multi core vault reindexing.
        It reads the content of a note given its path.

        :param note_path: path to the note to read.
        :return: the note object.
        """
        full_path = self.vault / note_path
        note = self.note_obj.read(path=full_path,
                                  parsing_obj=self.header_obj,
                                  delimiter=self.delimiter,
                                  special_names=self.special_values,
                                  header=self.header,
                                  link_del=self.link_del)

        return note

    def multiprocess_index_vault(self) -> None:
        """
        Reindex the zettelkasten vault from scratch.
        Multiple cores function.
        """
        notes_paths: list[str] = glob1(str(self.vault), "*.md")
        # drop the tables
        self.dbmanager.drop_tables()
        # create new tables
        self.dbmanager.create_tables()

        with Pool() as executor:
            notes = executor.map(self._read_note, notes_paths)

        for note in notes:
            self.dbmanager.add_to_index(note)

        # add and commit
        if self.git:
            self.git.save(msg='Reindexed vault')

    def import_from_scratchpad(self,
                               zk_id: int,
                               confirmation: bool = False) -> None:
        """
        Move a note from the scratchpad to the main vault.
        This will add the note metadata to the database.

        :param zk_id: ID of the note.
        :param confirmation: whether to ask for confirmation. If True, and
                             confirmation is no, the note will not be moved.
        """
        # check the ID is unique
        if self._note_exists(zk_id):
            raise ZettelkastenException(f"Note '{zk_id}' already exists.")

        # check scratchpad exists
        self._check_scratchpad_exists()

        filename = Path(str(zk_id)).with_suffix(".md")
        note_path = self.scratchpad / filename
        note = self.note_obj.read(path=note_path,
                                  parsing_obj=self.header_obj,
                                  delimiter=self.delimiter,
                                  special_names=self.special_values,
                                  header=self.header,
                                  link_del=self.link_del)

        # check title is unique
        self._check_unique_title(note.title)

        # ask for confirmation
        msg = "Move from scratchpad?"
        if confirmation and not self._ask_for_confirmation(msg):
            return None

        # save the new note
        with open(self.vault / filename, "w") as f:
            f.write(note.materialize())

        # remove from scratchpad
        note_path.unlink(missing_ok=True)

        # update the index
        self.dbmanager.add_to_index(note)

        # update .last file
        self._add_last_opened(filename)

        # add and commit
        if self.git:
            self.git.save(msg=f'Moved "{note.zk_id}" from scratchpad')

    def list_scratchpad(self) -> list[int]:
        """
        List the note IDs of the notes contained in the scratchpad.

        :return: list of zk_id of the notes in the scratchpad.
        """
        # check scratchpad exists
        self._check_scratchpad_exists()

        notes: list[str] = glob1(str(self.scratchpad), "*.md")
        scratchpad_ids = [int(note.removesuffix(".md")) for note in notes]

        return scratchpad_ids

    def _ask_for_confirmation(self, msg: str = "Save note?") -> bool:
        response = input(f"{msg} [Y/n]: ")
        commit = True
        if response.lower() in ['n', 'no', 'nope']:
            commit = False

        return commit

    def _check_scratchpad_exists(self) -> None:

        if not self.scratchpad.exists() or not self.scratchpad.is_dir():
            raise ScratchpadError("Scratchpad does not exist.")

    def _detect_git_repo(self) -> Git | None:
        try:
            git = Git(self.vault)
            return git
        except GitException:
            return None


class ZettelkastenException(Exception):
    """Main exception raised by Zettelkasten"""


class IDChangedError(ZettelkastenException):
    pass


class TitleClashError(ZettelkastenException):
    pass


class VaultError(ZettelkastenException):
    pass


class ScratchpadError(ZettelkastenException):
    pass
