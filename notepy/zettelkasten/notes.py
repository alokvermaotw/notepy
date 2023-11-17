"""
Define the main class that models a zettelkasten note.
"""

from __future__ import annotations
from collections.abc import Collection
from typing import Any

from abc import ABC, abstractmethod
from datetime import datetime
from dataclasses import dataclass, fields
from string import punctuation
from pathlib import Path

from notepy.parser.parser import HeaderParser, BodyParser


def sluggify(title: str) -> str:
    """
    Sluggify the title.

    :param title: title to sluggify.
    :return: sluggified title (duh).
    """
    clean_title = "".join(list(map(lambda x: x
                                   if x not in punctuation or x == "-"
                                   else "", title)))
    slug = clean_title.lower().replace(" ", "-")

    return slug


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

    @abstractmethod
    def generate_frontmatter(self) -> str:
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
             link_del: tuple[str, str] = ('[[', ']]'),
             strict: bool = False,
             quiet: bool = False) -> Note:
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
        body = f"# {title}\n\n# References"
        zk = cls(**metadata,
                 links=[],
                 body=body)

        return zk

    @classmethod
    def read(cls,
             path: str | Path,
             parsing_obj: Collection[str],
             delimiter: str = "---",
             special_names: Collection[str] = ("date", "tags", 'zk_id'),
             header: str = "# ",
             link_del: tuple[str, str] = ('[[', ']]'),
             strict: bool = False,
             quiet: bool = False) -> Note:
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
        if not quiet:
            if body_meta['header'][0].removeprefix(header).strip() != frontmatter_meta['title']:
                if strict:
                    raise NoteException("First header and title must be the same.")
                else:
                    print(f"First header and title of note {frontmatter_meta['zk_id']} do not coincide.")

        links = body_meta['links']
        body = "\n".join(body_meta['body']).strip()
        new_note = Note(links=links,
                        body=body,
                        **frontmatter_meta)

        return new_note

    def materialize(self) -> str:
        """
        Return content of note
        """

        note = self.generate_frontmatter()
        note += "\n\n\n"
        note += self.body
        note += "\n"

        return note

    def sluggify(self) -> str:
        """
        Sluggify the title of the note.
        """
        slug = sluggify(self.title)

        return slug

    def generate_frontmatter(self) -> str:
        """
        Generates the frontmatter string of the
        zettelkasten note

        :param metadata: the metadata of the note
        :return: the frontmatter string
        """

        frontmatter_names = [note_field.name
                             for note_field in fields(Note)
                             if note_field.name not in ['links', 'body']]
        frontmatter_metadata = {name: getattr(self, name) for name in frontmatter_names}
        frontmatter_metadata['tags'] = " ".join(frontmatter_metadata['tags'])
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
