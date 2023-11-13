from pathlib import Path
from collections.abc import MutableMapping


_COMMANDS: MutableMapping = {
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
                "help": "ID of the note to delete.",
                "nargs": 1,
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
        "help": "List all the notes."
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
    }
}
