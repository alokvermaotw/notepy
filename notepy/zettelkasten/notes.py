"""
Define the main class that models a zettelkasten note.
"""

from __future__ import annotations
from copy import copy
from abc import ABC, abstractmethod
from datetime import datetime
from dataclasses import dataclass
from string import punctuation
from pathlib import Path
from collections.abc import Collection, MutableMapping
from typing import Any
from notepy.parser.parser import HeaderParser, BodyParser


class BaseNote(ABC):
    @classmethod
    @abstractmethod
    def new(cls, title: str, author: str) -> Note:
        """
        Create a new Note from metadata

        :param title: title of the note
        :param author: author of the note
        :return: a new note
        """

    @staticmethod
    @abstractmethod
    def _generate_frontmatter(metadata: dict[str, str]) -> str:
        """
        Generates the frontmatter string of the
        zettelkasten note

        :param metadata: the metadata of the note
        :return: the frontmatter string
        """

    @abstractmethod
    def materialize(self) -> str:
        """
        Return content of note
        """

    @classmethod
    @abstractmethod
    def read(cls,
             path: str | Path,
             parsing_obj: Collection[str],
             delimiter: str = "---",
             special_names: Collection[str] = ("date", "tags", 'zk_id'),
             header: str = "# ",
             link_del: tuple[str, str] = ('[[', ']]')) -> Note:
        """
        Read a note from a file.

        :param path: path to the note.
        :param parsing_obj: what names to parse in the frontmatter.
        :param delimiter: delimiter of the frontmatter.
        :param special_names: names of the frontmatter that need to be specially parsed.
        :param header: how a header is defined.
        :param link_del: how a link is delimited.
        :return: the note
        """


@dataclass
class Note(BaseNote):
    """
    This class models a single note in a larger zettelkasten system.

    :param title: title of the note
    :param author: author of the note
    :param date: date of the note
    :param zk_id: unique id of the note, in the form %Y%m%d%H%M%S
    :param tags: tags of the note
    :param links: links the note points to
    :param frontmatter: the whole frontmatter of the note
    :param body: the whole body of the note
    """
    title: str
    author: str
    date: datetime
    zk_id: int
    tags: Collection[str]
    links: Collection[str]
    frontmatter: str
    body: str

    @classmethod
    def new(cls, title: str, author: str) -> Note:
        """
        Create a new Note from metadata

        :param title: title of the note
        :param author: author of the note
        :return: a new note
        """
        metadata = cls._generate_metadata(title, author)
        frontmatter = cls._generate_frontmatter(metadata)
        body = f"# {title}"
        zk = cls(**metadata,
                 links=[],
                 frontmatter=frontmatter,
                 body=body)

        return zk

    @classmethod
    def read(cls,
             path: str | Path,
             parsing_obj: Collection[str],
             delimiter: str = "---",
             special_names: Collection[str] = ("date", "tags", 'zk_id'),
             header: str = "# ",
             link_del: tuple[str, str] = ('[[', ']]')) -> Note:
        """
        Read a note from a file.

        :param path: path to the note.
        :param parsing_obj: what names to parse in the frontmatter.
        :param delimiter: delimiter of the frontmatter.
        :param special_names: names of the frontmatter that need to be specially parsed.
        :param header: how a header is defined.
        :param link_del: how a link is delimited.
        :return: the note
        """
        header_parser = HeaderParser(parsing_obj=parsing_obj,
                                     delimiter=delimiter,
                                     special_names=special_names)
        body_parser = BodyParser(header1=header,
                                 link_del=link_del)

        if not Path(path).exists():
            raise NoteException("Note does not exist. Consider reindexing the vault.")

        with open(path) as f:
            frontmatter_meta, _ = header_parser.parse(handle=f)
            body_meta, _ = body_parser.parse(handle=f)

        # raise exception if first header is different from title
        if body_meta['header'][0].removeprefix(header).strip() != frontmatter_meta['title']:
            raise NoteException("First header and title must be the same.")

        frontmatter = cls._generate_frontmatter(frontmatter_meta)
        links = body_meta['links']
        body = "\n".join(body_meta['body']).strip()
        new_note = Note(links=links, frontmatter=frontmatter,
                        body=body, **frontmatter_meta)

        return new_note

    def materialize(self) -> str:
        """
        Return content of note
        """

        note = self.frontmatter
        note += "\n\n\n"
        note += self.body
        note += "\n"

        return note

    def sluggify(self) -> str:
        """
        Sluggify the title of the note.
        """
        clean_title = "".join(list(map(lambda x: x
                                       if x not in punctuation
                                       else "", self.title)))
        slug = clean_title.lower().replace(" ", "-")

        return slug

    @staticmethod
    def _generate_frontmatter(metadata: MutableMapping[str, Any]) -> str:
        """
        Generates the frontmatter string of the
        zettelkasten note

        :param metadata: the metadata of the note
        :return: the frontmatter string
        """

        frontmatter_metadata = copy(metadata)
        frontmatter_metadata['tags'] = ", ".join(frontmatter_metadata['tags'])
        frontmatter_metadata['date'] = (frontmatter_metadata['date']
                                        .strftime("%Y-%m-%dT%H:%M:%S"))
        yml_header = '\n'.join(
                ['---'] +
                [f'{key}: {el}' for key, el in frontmatter_metadata.items()] +
                ['---'])

        return yml_header

    @staticmethod
    def _generate_metadata(title: str, author: str) -> dict[str, Any]:
        """
        Generates the metadata dictionary for
        a nrew zettelkasten note.

        :param title: the title of the note
        :param author: the author of the note
        :return: the metadata dictionary
        """

        date = datetime.now()
        zk_id = Note._generate_id(date)

        metadata = {
            'title': title,
            'author': author,
            'date': date,
            'zk_id': zk_id,
            'tags': [],
        }

        return metadata

    @staticmethod
    def _generate_id(date: datetime) -> int:
        """
        Generate the id for a singe note.

        :param date: the date the note was taken
        :return: the note ID
        """

        date_formatted = int(date.strftime("%Y%m%d%H%M%S"))

        return date_formatted


class NoteException(Exception):
    """Exception raised when there is an issue with a note."""
