from __future__ import annotations

from typing import Any, Optional
from collections.abc import Sequence, MutableMapping, Collection

from dataclasses import dataclass, fields
from pathlib import Path
from tempfile import NamedTemporaryFile
from glob import glob1
from multiprocessing import Pool
from copy import copy
from datetime import datetime

from notepy.zettelkasten.notes import Note
from notepy.wrappers.git_wrapper import Git, GitMixin
from notepy.wrappers.editor_wrapper import Editor
from notepy.zettelkasten.sql import DBManager
from notepy.utils import ask_for_confirmation


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
    author: str
    autocommit: bool = True
    autosync: bool = False
    editor: Optional[str] = None
    note_obj: type[Note] = Note
    delimiter: str = "---"
    header: str = "# "
    link_del: tuple[str, str] = ('[[', ']]')
    special_values: Collection[str] = ('date', 'last', 'tags', 'zk_id')

    def __post_init__(self) -> None:
        self.vault = Path(self.vault).expanduser()
        self.index = self.vault / ".index.db"
        self.last = self.vault / ".last"
        self.dbmanager = DBManager(self.index)
        self.git = self._detect_git_repo(self.vault)
        self.tmp = self.vault / ".tmp"
        self.header_obj = [note_field.name
                           for note_field in fields(self.note_obj)
                           if note_field.name not in ['links', 'body']]

        if not self.vault.is_dir():
            raise VaultError(f"Vault '{self.vault}' is not a directory "
                             "or does not exist.")

    @classmethod
    def initialize(cls,
                   path: str | Path,
                   author: str,
                   git_init: bool = False,
                   git_origin: str = "",
                   autocommit: bool = False,
                   autosync: bool = False,
                   force: bool = False,
                   note_obj: type[Note] = Note,
                   delimiter: str = "---",
                   header: str = "# ",
                   link_del: tuple[str, str] = ('[[', ']]'),
                   special_values: tuple[str, str] = ('date', 'tags'),
                   ) -> Zettelkasten:
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
            raise ZettelkastenException(f"'{path}' has already been initialized! "
                                        "Use 'force=True' to force re-initialization")

        # create vault
        path.mkdir(exist_ok=True)

        # create .last file
        last = path / ".last"
        last.touch()

        # create the tables
        index = path / ".index.db"
        DBManager(index).create_tables()

        # create tmp dir
        tmp = path / '.tmp'
        tmp.mkdir(exist_ok=True)

        # create git repo
        if git_init:
            to_ignore = ['.last', '.tmp', '.index.db']
            git_path = path / ".git"
            git = Git(path) if git_path.exists() else Git.init(path, to_ignore=to_ignore)
            # add origin if provided
            if git_origin:
                git.origin = git_origin
                git.push()

        zk_args: MutableMapping[str, Any] = {
            'vault': path,
            'author': author,
            'note_obj': note_obj,
            'delimiter': delimiter,
            'header': header,
            'link_del': link_del,
            'special_values': special_values,
            'autocommit': autocommit,
            'autosync': autosync
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
        is_zettelkasten *= (path / ".last").is_file()
        is_zettelkasten *= (path / ".tmp").is_dir()

        return bool(is_zettelkasten)

    def _check_zettelkasten(self) -> None:
        """
        Raise an exception if vault is not a zettelkasten
        """
        if not self.is_zettelkasten(self.vault):
            raise ZettelkastenException(f"'{self.vault}' must be initialized first.")

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
                             confirmation: bool = False,
                             strict: bool = False) -> Note | None:
        """
        Edit a note in a temporary file. The temporary file is created
        in the tmp so not to interfere with git. The temporary
        file is automatically deleted.

        :param note: the note to edit.
        :param confirmation: whether to ask for confirmation.
        :return: if confirmation=True and input was no,
                 return None. Else the note.
        """

        # check if tmp dir exists. We are going to create the temporary
        # note inside the .tmp so that its creation is not
        # detected by git, since by default .tmp is in .gitignore
        self.tmp.mkdir(exist_ok=True)

        with NamedTemporaryFile("w", dir=self.tmp, suffix=".md") as f:
            # write the note in the temporary file
            f.write(note.materialize())
            f.seek(0)

            # edit the note
            editor = Editor(self.editor)
            editor.edit(f.name, cwd=self.vault)

            # TODO: consider whether opening two handles to same file is good
            # idea
            # TODO: make read arguments less implementation dependent.
            # create the note from the new data
            new_note = self.note_obj.read(path=f.name,
                                          parsing_obj=self.header_obj,
                                          delimiter=self.delimiter,
                                          special_names=self.special_values,
                                          header=self.header,
                                          link_del=self.link_del,
                                          strict=strict)

        # if id was changed, raise an error.
        if new_note.zk_id != note.zk_id:
            if strict:
                raise IDChangedError("You cannot change the ID of an existing note.")
            else:
                print("The note ID looks different. It has been returned to its "
                      "original value as it could create issues in your vault.")
                new_note.zk_id = note.zk_id

        # if title was changed, make sure it doesn't clash
        # with other notes
        if new_note.title != note.title:
            self._check_unique_title(new_note.title, strict=strict)

        # ask for confirmation
        if confirmation and not ask_for_confirmation("Save note?"):
            return None

        # change access time
        new_note.last = datetime.now()

        return new_note

    def _check_unique_title(self, note_title: str, strict: bool = False) -> None:
        all_titles = [title[0] for title in self.dbmanager.get_title()]
        if note_title in all_titles:
            if strict:
                raise TitleClashError("Title is already used in another note.")
            else:
                print("Title is already in use in another note. Please consider changing it "
                      "to something different, as it may cause ambiguous links in your vault.")

    def new(self,
            title: str,
            author: Optional[str] = None,
            confirmation: bool = False,
            strict: bool = False) -> None:
        """
        Create a new note and add it to the vault.

        :param title: title of the note.
        :param author: author of the note.
        :param confirmation: whether to ask for confirmation to save the note.
        """
        # check if vault is a zettelkasten
        self._check_zettelkasten()
        # check title is unique
        self._check_unique_title(title, strict=True)

        # if different author is provided, that takes precedence
        if author is None:
            author = self.author

        # new note
        tmp_note = self.note_obj.new(title, author)

        # create new note
        new_note = self._edit_temporary_note(tmp_note, confirmation, strict)
        if new_note is None:
            return None

        filename = Path(str(new_note.zk_id)).with_suffix(".md")

        note_path = self.vault / filename
        self.dbmanager.add_to_index(new_note)

        # save the new note
        with open(note_path, "w") as f:
            f.write(new_note.materialize())

        # update .last file
        self._add_last_opened(filename)

        # add and commit
        self.commit_and_sync(msg=f'Commit "{new_note.zk_id}"',
                             commit=self.autocommit,
                             push=self.autosync)

    def update(self, zk_id: int, confirmation: bool = False, strict: bool = False) -> None:
        """
        Update the note corresponding to the provded ID.

        :param zk_id: the ID of the note.
        :param confirmation: whether to ask for confirmation to save the note.
        """

        # check if vault is a zettelkasten
        self._check_zettelkasten()
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
                                  link_del=self.link_del,
                                  strict=strict,
                                  quiet=True)

        new_note = self._edit_temporary_note(note, confirmation=confirmation, strict=strict)
        if new_note is None:
            return None

        # save the new note
        with open(note_path, "w") as f:
            f.write(new_note.materialize())

        # update the index
        self.dbmanager.update_note_to_index(new_note)

        # update .last file
        self._add_last_opened(filename)

        # add and commit
        self.commit_and_sync(msg=f'Updated "{new_note.zk_id}"',
                             commit=self.autocommit,
                             push=self.autosync)

    def open(self, zk_id: list[int]) -> None:
        # check if vault is a zettelkasten
        self._check_zettelkasten()

        filenames = []
        for id in set(zk_id):
            # check that the note exists
            if not self._note_exists(id):
                raise ZettelkastenException(f"Note '{id}' does not exist.")

            filenames.append(Path(str(id)).with_suffix(".md"))

        editor = Editor(self.editor)
        editor.multiple_edit(filenames, self.vault)

    def delete(self, zk_id: int, confirmation: bool = False) -> None:
        """
        Delete a note.

        :param zk_id: the ID of the note to delete.
        :param confirmation: whether to ask for confirmation to delete the note.
        """

        # check if vault is a zettelkasten
        self._check_zettelkasten()
        # check that the note exists
        if not self._note_exists(zk_id):
            raise ZettelkastenException(f"Note '{zk_id}' does not exist.")

        filename = Path(str(zk_id)).with_suffix(".md")
        note_path = self.vault / filename

        # ask for confirmation
        if confirmation and not ask_for_confirmation("Delete note?"):
            return None

        # remove from index
        self.dbmanager.delete_from_index(zk_id)

        # remove note
        note_path.unlink(missing_ok=True)

        # add and commit
        self.commit_and_sync(msg=f'Removed note "{zk_id}"',
                             commit=self.autocommit,
                             push=self.autosync)

    def _delete_single_note(self, zk_id: int) -> int:
        """
        Helper function.

        :return: 1 if successful, 0 otherwise
        """
        # check that the note exists
        if not self._note_exists(zk_id):
            print(f"Note '{zk_id}' does not exist.")
            return 0

        filename = Path(str(zk_id)).with_suffix(".md")
        note_path = self.vault / filename

        # remove from index
        self.dbmanager.delete_from_index(zk_id)

        # remove note
        note_path.unlink(missing_ok=True)

        return 1

    def delete_multiple(self,
                        zk_ids: list[int],
                        confirmation: bool = False) -> int:
        """
        Delete multiple notes in parallel.

        :param zk_ids: list of notes ids to delete.
        :param confirmation: whether to ask for confirmation to delete the notes.
        """
        # check if vault is a zettelkasten
        self._check_zettelkasten()

        # ask for confirmation
        if confirmation and not ask_for_confirmation("Delete notes?"):
            return 0

        # delete in parallel
        with Pool() as executor:
            no_deleted_files = executor.map(self._delete_single_note, zk_ids)

        # add and commit
        self.commit_and_sync(msg='Removed batch of notes',
                             commit=self.autocommit,
                             push=self.autosync)

        return sum(no_deleted_files)

    def list_notes(self,
                   title: Optional[list[str]] = None,
                   zk_id: Optional[list[str]] = None,
                   author: Optional[list[str]] = None,
                   tags: Optional[list[str]] = None,
                   links: Optional[list[str]] = None,
                   # creation_date: Optional[list[str]] = None,
                   # access_date: Optional[list[str]] = None,
                   sort_by: Optional[str] = None,
                   descending: bool = True,
                   show: list[str] = ['title', 'zk_id']) -> Sequence[tuple[int, str]]:
        """
        List and filter based on tags, links and date
        """
        # check if vault is a zettelkasten
        self._check_zettelkasten()
        results = self.dbmanager.list_notes(title,
                                            zk_id,
                                            author,
                                            tags,
                                            links,
                                            # creation_date,
                                            # access_date,
                                            sort_by,
                                            descending,
                                            show)

        return results

    def _note_exists(self, zk_id: int) -> bool:
        filename = Path(str(zk_id)).with_suffix(".md")
        path = self.vault / filename

        return path.is_file()

    def print_note(self, zk_id: int) -> str:
        """
        Print the content of the note with the corresponding ID.

        :param zk_id: ID of the note.
        :return: content of the note.
        """
        # check if vault is a zettelkasten
        self._check_zettelkasten()
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
        # check if vault is a zettelkasten
        self._check_zettelkasten()
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
        # check if vault is a zettelkasten
        self._check_zettelkasten()
        notes_paths: list[str] = glob1(str(self.vault), "*.md")
        # drop the tables
        self.dbmanager.drop_tables()
        # create new tables
        self.dbmanager.create_tables()

        with Pool() as executor:
            notes = executor.map(self._read_note, notes_paths)

        for note in notes:
            self.dbmanager.add_to_index(note)

    def get_last(self) -> int:
        """
        Get ID of the last note as saved in .last.

        :return: ID saved in .last
        """

        # check if vault is a zettelkasten
        self._check_zettelkasten()

        if not self.last.is_file():
            raise ZettelkastenException(".last file not found")

        try:
            last_content = int(self.last
                               .read_text()
                               .strip()
                               .removesuffix(".md"))
        except TypeError:
            raise ZettelkastenException(".last file is malformatted or empty.")
        except ValueError:
            raise ZettelkastenException(".last file is malformatted or empty.")

        return last_content

    def next(self, title: str,
             zk_id: Optional[int] = None,
             confirmation: bool = False,
             strict: bool = False) -> None:
        """
        Create a new note that is the logical continuation
        of the last note or of the ID provided.

        :param zk_id: ID of the note to continue from.
        :param confirmation: whether to ask for confirmation.
        """
        # check if vault is a zettelkasten
        self._check_zettelkasten()
        # check title is unique
        self._check_unique_title(title)

        # get ID of last note
        if zk_id is None:
            zk_id = self.get_last()

        # check that the note exists
        if not self._note_exists(zk_id):
            raise ZettelkastenException(f"Note '{zk_id}' does not exist.")

        # read the previous note
        filename = Path(str(zk_id)).with_suffix(".md")
        note_path = self.vault / filename
        note = self.note_obj.read(path=note_path,
                                  parsing_obj=self.header_obj,
                                  delimiter=self.delimiter,
                                  special_names=self.special_values,
                                  header=self.header,
                                  link_del=self.link_del,
                                  strict=strict,
                                  quiet=True)

        # get links and other metadata
        links = copy(note.links)
        tags = copy(note.tags)
        author = note.author

        # new note
        tmp_note = self.note_obj.new(title, author)
        tmp_note.tags = tags

        tmp_note.body += "\n"
        tmp_note.body += "\n".join(["- "+f"[[{link}]]" for link in links])

        # create new note
        new_note = self._edit_temporary_note(tmp_note, confirmation, strict)
        if new_note is None:
            return None

        new_filename = Path(str(new_note.zk_id)).with_suffix(".md")

        new_note_path = self.vault / new_filename
        self.dbmanager.add_to_index(new_note)

        # save the new note
        with open(new_note_path, "w") as f:
            f.write(new_note.materialize())

        # add link to new note to the body of old note
        note.body += "\n"
        note.body += "- " + f"[[{new_note.sluggify()}]]"
        note.links = list(note.links)
        note.links.append(new_note.sluggify())

        # save the modified note
        with open(note_path, "w") as f:
            f.write(note.materialize())

        # add to index the modified old note
        self.dbmanager.update_note_to_index(note)

        # update .last file
        self._add_last_opened(new_filename)

        # add and commit
        self.commit_and_sync(msg=f'Commit "{new_note.zk_id}" continuing '
                                 f'from {note.zk_id}',
                             commit=self.autocommit,
                             push=self.autosync)

    def get_metadata(self, zk_id: int) -> MutableMapping[str, Any]:
        # check if vault is a zettelkasten
        self._check_zettelkasten()
        # check that the note exists
        if not self._note_exists(zk_id):
            raise ZettelkastenException(f"Note '{zk_id}' does not exist.")

        columns = ['zk_id',
                   'title',
                   'author',
                   'creation_date',
                   'last_changed',
                   'tag',
                   'link']
        result = self.list_notes(zk_id=[zk_id],
                                 show=columns)
        metadata = {}
        metadata['zk_id'] = result[0][0]
        metadata['title'] = result[0][1]
        metadata['author'] = result[0][2]
        metadata['creation_date'] = result[0][3]
        metadata['last_changed'] = result[0][4]
        metadata['tag'] = set([result[i][5] for i in range(len(result))])
        metadata['link'] = set([result[i][6] for i in range(len(result))])

        return metadata


class ZettelkastenException(Exception):
    """Main exception raised by Zettelkasten"""


class IDChangedError(ZettelkastenException):
    pass


class TitleClashError(ZettelkastenException):
    pass


class VaultError(ZettelkastenException):
    pass
