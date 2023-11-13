from __future__ import annotations
from typing import Any
from collections.abc import Collection
from dataclasses import dataclass, fields
from argparse import ArgumentParser
from notepy.zettelkasten.zettelkasten import Zettelkasten, Note
from pathlib import Path
# import tomllib


@dataclass
class Cli:
    prog: str
    description: str
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
    flag_vault: Path
    flag_author: str
    flag_note_obj: type[Note] = Note
    flag_delimiter: str = "---"
    flag_header: str = "# "
    flag_link_del: tuple[str, str] = ('[[', ']]')
    flag_special_values: Collection[str] = ('date', 'tags', 'zk_id')
    flag_autocommit: bool = True
    flag_autosync: bool = False

    def __post_init__(self):
        self.global_parser = ArgumentParser(prog=self.prog,
                                            description=self.description)
        commands, flags = self._get_commands()

        if flags:
            for flag in flags:
                flag_config = getattr(self, "flag_"+flag)
                self.global_parser.add_argument("--"+flag,
                                                **flag_config)

        if commands:
            self.subparsers = self.global_parser.add_subparsers()
            for command in commands:
                self._create_subparsers(command)
        ...

    def _get_commands(self) -> tuple[list[str], list[str]]:
        commands: list[str] = []
        flags: list[str] = []
        for comm in fields(self):
            if comm.name.startswith("command_"):
                commands.append(comm.name.removeprefix("command_"))
            elif comm.name.startswith("flag_"):
                flags.append(comm.name.removeprefix("flag_"))

        return commands, flags

    def _create_subparsers(self, command):
        command_config = getattr(self, "command_"+command)
        parser = self.subparsers.add_parser(command,
                                            help=command_config.get("help", ""))
        subflags = command_config.get('flags', {})
        for flag in subflags:
            parser.add_argument(flag, **subflags[flag])

        # parser.set_defaults(func=)

    def parse(self, *args, **kwargs):
        self.global_parser.parse_args()

    def __call__(self, *args, **kwargs):
        self.parse(**args, **kwargs)
