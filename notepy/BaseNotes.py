"""
Define two classes to model zettelkasten:
    - Zk: represents a single note
    - ZettelKasten: represents the whole repository
"""

from __future__ import annotations
from pathlib import Path
import argparse
import os
import sys
import subprocess
from datetime import datetime
from hashlib import md5
import sqlite3
from dataclasses import dataclass


@dataclass
class Zk:
    """
    This class models a single note in a larger
    zettelkasten system.
    """
    title: str
    author: str
    date: datetime
    zk_id: str
    tags: list[str]

    @classmethod
    def new(cls, title: str, author: str) -> Zk:
        metadata = cls._generate_metadata(title, author)
        zk = cls(**metadata)

        return zk

    def _generate_frontmatter(metadata: dict[str, str]) -> str:
        """
        Generates the frontmatter string of the
        zettelkasten note

        :param metadata: the metadata of the note
        :return: the frontmatter string
        """

        yml_header = '\n'.join(
                ['---'] +
                [f'{key}: {el}' for key, el in metadata.items()] +
                ['---'])

        return yml_header

    def _generate_metadata(title: str, author: str) -> dict[str, str]:
        """
        Generates the metadata dictionary for
        the current zettelkasten note.

        :param title: the title of the note
        :param author: the author of the note
        :return: the metadata dictionary
        """

        date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        zk_id_str = "_".join([date, author, title])
        zk_id = md5(zk_id_str.encode()).hexdigest()

        metadata = {
            'title': title,
            'author': author,
            'date': date,
            'zk_id': zk_id,
            'tags': ''
        }

        return metadata


class ZettelKasten:
    pass
