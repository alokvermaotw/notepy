from __future__ import annotations
from typing import Any
from dataclasses import dataclass, fields
from argparse import ArgumentParser, Namespace
from notepy.zettelkasten.zettelkasten import Zettelkasten
from notepy.zettelkasten import zettelkasten as zk
from pathlib import Path
# import tomllib


class CliMixin:
    @staticmethod
    def initialize(args: Namespace) -> None:
        try:
            my_zk = Zettelkasten.initialize(args.vault,
                                            args.author[0],
                                            args.git_init,
                                            args.git_origin,
                                            autocommit=args.autocommit,
                                            autosync=args.autosync,
                                            force=args.force)
            print(f"Vault initialized in '{args.vault}'")
            del my_zk
        except zk.ZettelkastenException:
            print(f"{args.vault} has already been initialized! Use "
                  f"`--force` to force re-initialization.")

    @staticmethod
    def new(args: Namespace) -> None:
        try:
            my_zk = CliMixin._create_zettelkasten(args)
            my_zk.new(args.title[0],
                      author=args.author[0],
                      confirmation=args.no_confirmation)
        except zk.TitleClashError as e:
            print(e)
        except zk.ZettelkastenException as e:
            print(e)
        except:
            raise

    @staticmethod
    def edit(args: Namespace) -> None:
        try:
            my_zk = CliMixin._create_zettelkasten(args)
            my_zk.update(args.zk_id[0],
                         confirmation=args.no_confirmation)
        except zk.ZettelkastenException as e:
            print(e)
        except:
            raise

    @staticmethod
    def delete(args: Namespace) -> None:
        try:
            my_zk = CliMixin._create_zettelkasten(args)
            my_zk.delete(args.zk_id[0],
                         confirmation=args.no_confirmation)
        except zk.ZettelkastenException as e:
            print(e)
        except:
            raise

    @staticmethod
    def print(args: Namespace) -> None:
        try:
            my_zk = CliMixin._create_zettelkasten(args)
            my_zk.print_note(args.zk_id[0])
        except zk.ZettelkastenException as e:
            print(e)
        except:
            raise

    @staticmethod
    def list(args: Namespace) -> None:
        try:
            my_zk = CliMixin._create_zettelkasten(args)
            results = my_zk.list_notes()
            for id, title in results:
                print(f"{title} (ID: {id})")
        except zk.ZettelkastenException as e:
            print(e)
        except:
            raise

    @staticmethod
    def reindex(args: Namespace) -> None:
        try:
            my_zk = CliMixin._create_zettelkasten(args)
            if args.no_multi_core:
                my_zk.multiprocess_index_vault()
            else:
                my_zk.index_vault()

            print("Reindexing terminated successfully.")
        except zk.ZettelkastenException as e:
            print(e)
        except:
            raise

    @staticmethod
    def _create_zettelkasten(args: Namespace) -> Zettelkasten:
        my_zk = Zettelkasten(vault=args.vault,
                             author=args.author[0],
                             autocommit=args.autocommit,
                             autosync=args.autosync)

        return my_zk

    @staticmethod
    def not_implemented(args: Namespace) -> None:
        print("Function not implemented.")


@dataclass
class Cli(CliMixin):
    prog: str
    description: str
    command_initialize: dict[str, Any]
    command_new: dict[str, Any]
    command_edit: dict[str, Any]
    command_delete: dict[str, Any]
    command_print: dict[str, Any]
    command_list: dict[str, Any]
    command_reindex: dict[str, Any]
    flag_vault: Path
    flag_author: str
    flag_autocommit: bool
    flag_autosync: bool

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

    def _get_commands(self) -> tuple[list[str], list[str]]:
        commands: list[str] = []
        flags: list[str] = []
        for comm in fields(self):
            if comm.name.startswith("command_"):
                commands.append(comm.name.removeprefix("command_"))
            elif comm.name.startswith("flag_"):
                flags.append(comm.name.removeprefix("flag_"))

        return commands, flags

    def _create_subparsers(self, command: str) -> None:
        command_config = getattr(self, "command_"+command)
        parser = self.subparsers.add_parser(command,
                                            help=command_config.get("help", ""))

        subflags = command_config.get('flags', {})
        for flag in subflags:
            parser.add_argument(flag, **subflags[flag])

        default_func = getattr(self, command, self.not_implemented)
        parser.set_defaults(func=default_func)

    def parse(self, *args, **kwargs) -> Namespace:
        args: Namespace = self.global_parser.parse_args(*args, **kwargs)

        return args

    def run(self, *args, **kwargs) -> None:
        args = self.parse(*args, **kwargs)
        args.func(args)

    def __call__(self, *args, **kwargs) -> None:
        args = self.parse(*args, **kwargs)
        args.func(args)
