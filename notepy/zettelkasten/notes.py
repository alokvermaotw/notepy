"""
Define two classes to model zettelkasten:
    - Note: represents a single note
    - ZettelKasten: represents the whole repository
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime
from dataclasses import dataclass
from string import punctuation
from pathlib import Path
from typing import Sequence
from notepy.parser import HeaderParser, BodyParser


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
             parsing_obj: Sequence[str],
             delimiter: str = "---",
             special_names: Sequence[str] = ("date", "tags"),
             header: str = "# ",
             link_del: Sequence[str] = ('[[', ']]')) -> Note:
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
    :param zk_id: unique id of the note, in the form %Y%m%d%H%M%S-title, where
                  title is in kebab-case
    :param tags: tags of the note
    :param links: links the note points to
    :param frontmatter: the whole frontmatter of the note
    :param body: the whole body of the note
    """
    title: str
    author: str
    date: datetime
    zk_id: str
    tags: Sequence[str]
    links: Sequence[str]
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
             parsing_obj: Sequence[str],
             delimiter: str = "---",
             special_names: Sequence[str] = ("date", "tags"),
             header: str = "# ",
             link_del: Sequence[str] = ('[[', ']]')) -> Note:
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
        with open(path) as f:
            frontmatter_meta, _ = header_parser.parse(f)
            body_meta, _ = body_parser.parse(f)

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

    @staticmethod
    def _generate_frontmatter(metadata: dict[str, str]) -> str:
        """
        Generates the frontmatter string of the
        zettelkasten note

        :param metadata: the metadata of the note
        :return: the frontmatter string
        """

        frontmatter_metadata = metadata.copy()
        frontmatter_metadata['tags'] = ", ".join(frontmatter_metadata['tags'])
        frontmatter_metadata['date'] = (frontmatter_metadata['date']
                                        .strftime("%Y-%m-%dT%H:%M:%S"))
        yml_header = '\n'.join(
                ['---'] +
                [f'{key}: {el}' for key, el in frontmatter_metadata.items()] +
                ['---'])

        return yml_header

    @staticmethod
    def _generate_metadata(title: str, author: str) -> dict[str, str]:
        """
        Generates the metadata dictionary for
        a nrew zettelkasten note.

        :param title: the title of the note
        :param author: the author of the note
        :return: the metadata dictionary
        """

        date = datetime.now()
        zk_id = Note._generate_id(title, author, date)

        metadata = {
            'title': title,
            'author': author,
            'date': date,
            'zk_id': zk_id,
            'tags': [],
        }

        return metadata

    @staticmethod
    def _generate_id(title: str, author: str, date: datetime) -> str:
        """
        Generate the id for a singe note.

        :param title: the title of the note
        :param author: the author of the note
        :param date: the date the note was taken
        :return: the note ID in kebab-case
        """

        date_formatted = date.strftime("%Y%m%d%H%M%S")
        clean_title = "".join(list(map(lambda x: x
                                       if x not in punctuation
                                       else "", title)))
        clean_title = clean_title.lower().replace(" ", "-")
        zk_id = "-".join([date_formatted, clean_title])

        return zk_id
