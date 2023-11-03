"""
SQLite statements to manage index
"""

CREATE_MAIN_TABLE_STMT = """
    CREATE TABLE IF NOT EXISTS zettelkasten(zk_id STRING NOT NULL,
    title STRING NOT NULL,
    author STRING NOT NULL,
    creation_date DATETIME NOT NULL,
    last_changed DATETIME NOT NULL,
    PRIMARY KEY(zk_id))
"""
CREATE_TAGS_TABLE_STMT = """
    CREATE TABLE IF NOT EXISTS tags(tag STRING NOT NULL,
    zk_id STRING NOT NULL,
    PRIMARY KEY(tag, zk_id),
    FOREIGN KEY(zk_id) REFERENCES zettelkasten(zk_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE)
"""
CREATE_LINKS_TABLE_STMT = """
    CREATE TABLE IF NOT EXISTS links(link STRING NOT NULL,
    zk_id STRING NOT NULL,
    PRIMARY KEY(link, zk_id),
    FOREIGN KEY(zk_id) REFERENCES zettelkasten(zk_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE)
"""
INSERT_MAIN_STMT = "INSERT INTO zettelkasten VALUES (?, ?, ?, ?, ?)"
INSERT_TAGS_STMT = "INSERT INTO tags VALUES (?, ?)"
INSERT_LINKS_STMT = "INSERT INTO links VALUES (?, ?)"
DELETE_MAIN_STMT = "DELETE FROM zettelkasten WHERE zk_id = ?"
DELETE_TAGS_STMT = "DELETE FROM tags WHERE zk_id = ?"
DELETE_LINKS_STMT = "DELETE FROM links WHERE zk_id = ?"
UPDATE_MAIN_STMT = """
    UPDATE zettelkasten SET
    title = ?,
    author = ?,
    last_changed = ?
    WHERE zk_id = ?
"""
LIST_STMT = "SELECT zk_id, title from zettelkasten;"
