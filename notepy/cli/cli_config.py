from pathlib import Path
from collections.abc import MutableMapping
from typing import Any


_COMMANDS: MutableMapping[str, Any] = {
    "command_initialize": {
        "help": "Initialize the vault.",
        "flags": {
            "--git_init": {
                "help": "Initialize a git repository.",
                "action": "store_true"
            },
            "--git_origin": {
                "default": [""],
                "help": "Remote origin for git repository.",
                "nargs": 1,
                "type": str
            },
            "--force": {
                "help": "Force creation of vault, overwriting existing files and directories.",
                "action": "store_true"
            }
        }
    },
    "command_new": {
        "help": "Create a new note.",
        "flags": {
            "title": {
                "help": "Title of the new note.",
                "nargs": 1,
                "type": str
            },
            "--no-confirmation": {
                "help": "Whether to ask for confirmation before saving.",
                "action": "store_false"
            }
        }
    },
    "command_edit": {
        "help": "Open an existing note by ID.",
        "flags": {
            "zk_id": {
                "help": "ID of the note to open.",
                "nargs": 1,
                "type": int
            },
            "--no-confirmation": {
                "help": "Whether to ask for confirmation before saving.",
                "action": "store_false"
            }
        }
    },
    "command_delete": {
        "help": "Delete a note by ID.",
        "flags": {
            "zk_id": {
                "help": "ID of the note(s) to delete.",
                "nargs": "+",
                "type": int,
            },
            "--no-confirmation": {
                "help": "Whether to ask for confirmation before saving.",
                "action": "store_false"
            }
        }
    },
    "command_print": {
        "help": "Print the note by ID.",
        "flags": {
            "zk_id": {
                "help": "ID of the note to print.",
                "nargs": 1,
                "type": int,
            }
        }
    },
    "command_list": {
        "help": "List all the notes.",
        "flags": {
            "--title": {
                "help": "filter the list by these titles.",
                "nargs": "+",
                "type": str,
                "default": None
            },
            "--id": {
                "help": "filter the list by these ids.",
                "nargs": "+",
                "type": str,
                "default": None
            },
            "--author-name": {
                "help": "filter the list by these authors.",
                "nargs": "+",
                "type": str,
                "default": None
            },
            "--tags": {
                "help": "filter the list by these tags.",
                "nargs": "+",
                "type": str,
                "default": None
            },
            "--links": {
                "help": "filter the list by these links.",
                "nargs": "+",
                "type": str,
                "default": None
            },
            # "--creation-date": {
            #     "help": "filter the list by creation date",
            #     "nargs": "+",
            #     "type": str,
            #     "default": None
            # },
            # "--access-date": {
            #     "help": "filter the list by access date",
            #     "nargs": "+",
            #     "type": str,
            #     "default": None
            # },
            "--sort-by": {
                "help": "sort the list by criteria in ascending order.",
                "nargs": 1,
                "type": str,
                "default": [None],
                "choices": ["title", "author", "zk_id", "tag", "link"]
            },
            "--descending": {
                "help": "How to sort the results.",
                "action": "store_true"
            },
            "--no-color": {
                "help": "Output without color.",
                "action": "store_true"
            },
            "--show": {
                "help": "Which attributes to show",
                "type": str,
                "nargs": "+",
                "default": ["title", "zk_id"],
                "choices": ["title", "author", "zk_id", "creation_date", "access_date", "tag", "link"]
            },
            "--no-header": {
                "help": "Do not show header",
                "action": "store_true"
            }
        }
    },
    "command_reindex": {
        "help": "Reindex the vault.",
        "flags": {
            "--no-multi-core": {
                "help": "Run the reindexing concurrently",
                "action": "store_false"
            }
        }
    },
    "command_next": {
        "help": "Create new note continuing from last one.",
        "flags": {
            "title": {
                "help": "Title of the new note.",
                "nargs": 1,
                "type": str
            },
            "--zk_id": {
                "help": "ID of the note to continue from.",
                "nargs": 1,
                "type": int,
                "default": [None]
            },
            "--no-confirmation": {
                "help": "Whether to ask for confirmation.",
                "action": "store_false"
            }
        }
    },
    "flag_vault": {
        "default": ".",
        "type": Path,
        "help": "Location of the vault."
    },
    "flag_author": {
        "default": [""],
        "type": str,
        "nargs": 1,
        "help": "Author name."
    },
    "flag_autocommit": {
        "action": "store_true",
        "help": "Whether to commit the git repo at every action."
    },
    "flag_autosync": {
        "action": "store_true",
        "help": "Whether to push to remote origin at every action."
    },
    "flag_editor": {
        "default": [None],
        "type": str,
        "nargs": 1,
        "help": "Editor to use."
    }
}
