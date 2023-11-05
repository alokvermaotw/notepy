import sqlite3
from notepy.zettelkasten.notes import Note
from datetime import datetime
from collections.abc import Sequence


"""
SQLite statements to manage index
"""

_CREATE_MAIN_TABLE_STMT = """
    CREATE TABLE IF NOT EXISTS zettelkasten(zk_id STRING NOT NULL,
    title STRING NOT NULL,
    author STRING NOT NULL,
    creation_date DATETIME NOT NULL,
    last_changed DATETIME NOT NULL,
    PRIMARY KEY(zk_id))
"""
_CREATE_TAGS_TABLE_STMT = """
    CREATE TABLE IF NOT EXISTS tags(tag STRING NOT NULL,
    zk_id STRING NOT NULL,
    PRIMARY KEY(tag, zk_id),
    FOREIGN KEY(zk_id) REFERENCES zettelkasten(zk_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE)
"""
_CREATE_LINKS_TABLE_STMT = """
    CREATE TABLE IF NOT EXISTS links(link STRING NOT NULL,
    zk_id STRING NOT NULL,
    PRIMARY KEY(link, zk_id),
    FOREIGN KEY(zk_id) REFERENCES zettelkasten(zk_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE)
"""
_DROP_MAIN_TABLE_STMT = "DROP TABLE IF EXISTS zettelkasten;"
_DROP_TAGS_TABLE_STMT = "DROP TABLE IF EXISTS tags;"
_DROP_LINKS_TABLE_STMT = "DROP TABLE IF EXISTS links;"
_INSERT_MAIN_STMT = "INSERT INTO zettelkasten VALUES (?, ?, ?, ?, ?)"
_INSERT_TAGS_STMT = "INSERT INTO tags VALUES (?, ?)"
_INSERT_LINKS_STMT = "INSERT INTO links VALUES (?, ?)"
_DELETE_MAIN_STMT = "DELETE FROM zettelkasten WHERE zk_id = ?"
_DELETE_TAGS_STMT = "DELETE FROM tags WHERE zk_id = ?"
_DELETE_LINKS_STMT = "DELETE FROM links WHERE zk_id = ?"
_UPDATE_MAIN_STMT = """
    UPDATE zettelkasten SET
    title = ?,
    author = ?,
    last_changed = ?
    WHERE zk_id = ?
"""
_LIST_STMT = "SELECT zk_id, title from zettelkasten;"


class DBManager:
    """
    Database manager for the index of a zettelkasten.

    :param connection: the connection to the index
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def create_tables(self) -> None:
        """
        Create the index for a newly initialized zk.
        """
        with self.connection as conn:
            conn.execute(_CREATE_MAIN_TABLE_STMT)
            conn.execute(_CREATE_TAGS_TABLE_STMT)
            conn.execute(_CREATE_LINKS_TABLE_STMT)

    def drop_tables(self) -> None:
        """
        Drop all the tables.
        """
        with self.connection as conn:
            conn.execute(_DROP_MAIN_TABLE_STMT)
            conn.execute(_DROP_TAGS_TABLE_STMT)
            conn.execute(_DROP_LINKS_TABLE_STMT)

    def update_note_to_index(self, note: Note) -> None:
        """
        Add to the index the updated metadata of the note.

        :param note: the updated note.
        """
        current_date = datetime.now()
        main_payload = (note.title,
                        note.author,
                        current_date,
                        note.zk_id)
        tags_payload = [(tag, note.zk_id) for tag in note.tags]
        links_payload = [(link, note.zk_id) for link in note.links]

        try:
            with self.connection as conn:
                conn.execute(_UPDATE_MAIN_STMT, main_payload)
                # update tags and links
                conn.execute(_DELETE_TAGS_STMT, (note.zk_id,))
                conn.execute(_DELETE_LINKS_STMT, (note.zk_id,))
                conn.executemany(_INSERT_TAGS_STMT, tags_payload)
                conn.executemany(_INSERT_LINKS_STMT, links_payload)
        # TODO: investigate sqlite3 exceptions
        except sqlite3.IntegrityError as e:
            raise DBManagerException("SQL error") from e

    # TODO: make it so payload is note-agnostic
    def add_to_index(self, note: Note) -> None:
        """
        Add a new note to the vault

        :param note: note to process.
        """
        main_payload = (note.zk_id,
                        note.title,
                        note.author,
                        note.date,
                        note.date)
        tags_payload = [(tag, note.zk_id) for tag in note.tags]
        links_payload = [(link, note.zk_id) for link in note.links]

        try:
            with self.connection as conn:
                conn.execute(_INSERT_MAIN_STMT, main_payload)
                conn.executemany(_INSERT_TAGS_STMT, tags_payload)
                conn.executemany(_INSERT_LINKS_STMT, links_payload)
        except sqlite3.IntegrityError as e:
            raise DBManagerException("SQL error") from e

    def delete_from_index(self, zk_id: int) -> None:
        """
        Delete note from index.

        :param note: note to delete.
        """
        try:
            with self.connection as conn:
                conn.execute(_DELETE_MAIN_STMT, (zk_id,))
        except sqlite3.IntegrityError as e:
            raise DBManagerException("SQL error") from e

    def list(self) -> Sequence[tuple[int, str]]:
        """
        List zk_id, title of the notes in the database.
        """
        with self.connection as conn:
            results = conn.execute(_LIST_STMT).fetchall()

        return results


class DBManagerException(Exception):
    """Errors related to the index database"""
