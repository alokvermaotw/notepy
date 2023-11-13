from __future__ import annotations
from typing import Any
from dataclasses import dataclass, field, fields
from argparse import ArgumentParser
from notepy.zettelkasten.zettelkasten import Zettelkasten, Note
from pathlib import Path
# import tomllib


@dataclass
class Cli:
    zk: Zettelkasten
    note_obj: type[Note] = Note
    command_initialize: dict[str, Any]
    command_new: dict[str, Any]
    command_open: dict[str, Any]
    command_delete: dict[str, Any]
    command_print: dict[str, Any]
    command_commit: dict[str, Any]
    command_sync: dict[str, Any]
    command_list_notes: dict[str, Any]
    command_list_scrachpad: dict[str, Any]
    command_import_from_scratchpad: dict[str, Any]
    command_reindex_vault: dict[str, Any]

    def initialize(cls, path: Path) -> Cli:
        ...

    def _get_zk_method(self, command: str):
        zk_method = command.removeprefix("command_")
        # if not hasattr(zk_method, )

    def _get_commands(self) -> tuple[list[str], list[str]]:
        commands: list[str] = []
        flags: list[str] = []
        for comm in fields(self):
            if comm.startswith("command_"):
                commands.append(comm.name.removeprefix("command_"))
            elif comm.startswith("flag_"):
                flags.append(comm.name.removeprefix("flag_"))

        return commands, flags
