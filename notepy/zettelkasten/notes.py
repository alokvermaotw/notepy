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
    tags: list[str]
    links: list[str]
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

    @staticmethod
    def _generate_frontmatter(metadata: dict[str, str]) -> str:
        """
        Generates the frontmatter string of the
        zettelkasten note

        :param metadata: the metadata of the note
        :return: the frontmatter string
        """

        frontmatter_metadata = metadata.copy()
        frontmatter_metadata['tags'] = ''
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
        the current zettelkasten note.

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
