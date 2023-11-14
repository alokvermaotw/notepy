from __future__ import annotations
from typing import Any, Protocol
from collections.abc import MutableMapping

from dataclasses import dataclass, fields
from argparse import ArgumentParser, Namespace
from enum import Enum

from notepy.zettelkasten.zettelkasten import Zettelkasten
from notepy.zettelkasten import zettelkasten as zk
from notepy.wrappers.base_wrapper import WrapperException
from notepy.wrappers.editor_wrapper import EditorException
# import tomllib


class Show(Protocol):
    def __str__(self) -> str:
        ...


class Colors(Enum):
    BLACK_FG = "\033[30m"
    RED_FG = "\033[31m"
    GREEN_FG = "\033[32m"
    YELLOW_FG = "\033[33m"
    BLUE_FG = "\033[34m"
    MAGENTA_FG = "\033[35m"
    CYAN_FG = "\033[36m"
    WHITE_FG = "\033[37m"
    BLACK_BG = "\033[40m"
    RED_BG = "\033[41m"
    GREEN_BG = "\033[42m"
    YELLOW_BG = "\033[43m"
    BLUE_BG = "\033[44m"
    MAGENTA_BG = "\033[45m"
    CYAN_BG = "\033[46m"
    WHITE_BG = "\033[47m"
    RESET = "\033[0m"


def color(text: Show, COLOUR: str, context: str = "FG") -> str:
    if context not in ["FG", "BG"]:
        raise ValueError("context can only be 'FG' or 'BG'.")
    return (f"{getattr(Colors, COLOUR+'_'+context).value}"
            f"{text}"
            f"{Colors.RESET.value}")


class SubcommandsMixin:
    @staticmethod
    def initialize(args: Namespace) -> None:
        try:
            my_zk = Zettelkasten.initialize(args.vault,
                                            args.author[0],
                                            args.git_init,
                                            args.git_origin[0],
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
            my_zk = SubcommandsMixin._create_zettelkasten(args)
            my_zk.new(args.title[0],
                      author=args.author[0],
                      confirmation=args.no_confirmation)
        except zk.TitleClashError as e:
            print(e)
        except zk.ZettelkastenException as e:
            print(e)
        except WrapperException as e:
            print(e)
        except EditorException as e:
            print(e)

    @staticmethod
    def edit(args: Namespace) -> None:
        try:
            my_zk = SubcommandsMixin._create_zettelkasten(args)
            my_zk.update(args.zk_id[0],
                         confirmation=args.no_confirmation)
        except zk.ZettelkastenException as e:
            print(e)
        except WrapperException as e:
            print(e)
        except EditorException as e:
            print(e)

    @staticmethod
    def delete(args: Namespace) -> None:
        try:
            my_zk = SubcommandsMixin._create_zettelkasten(args)
            my_zk.delete(args.zk_id[0],
                         confirmation=args.no_confirmation)
        except zk.ZettelkastenException as e:
            print(e)

    @staticmethod
    def print(args: Namespace) -> None:
        try:
            my_zk = SubcommandsMixin._create_zettelkasten(args)
            print(my_zk.print_note(args.zk_id[0]))
        except zk.ZettelkastenException as e:
            print(e)

    @staticmethod
    def list(args: Namespace) -> None:
        try:
            my_zk = SubcommandsMixin._create_zettelkasten(args)
            results = my_zk.list_notes()
            for id, title in results:
                print(f"{color(title, 'CYAN')} "
                      f"(ID: {color(id, 'YELLOW')})")
        except zk.ZettelkastenException as e:
            print(e)

    @staticmethod
    def reindex(args: Namespace) -> None:
        try:
            my_zk = SubcommandsMixin._create_zettelkasten(args)
            if args.no_multi_core:
                my_zk.multiprocess_index_vault()
            else:
                my_zk.index_vault()

            print("Reindexing terminated successfully.")
        except zk.ZettelkastenException as e:
            print(e)

    @staticmethod
    def next(args: Namespace) -> None:
        try:
            my_zk = SubcommandsMixin._create_zettelkasten(args)
            my_zk.next(args.title[0],
                       args.zk_id[0],
                       args.no_confirmation)
        except zk.ZettelkastenException as e:
            print(e)
        except WrapperException as e:
            print(e)
        except EditorException as e:
            print(e)

    @staticmethod
    def _create_zettelkasten(args: Namespace) -> Zettelkasten:
        my_zk = Zettelkasten(vault=args.vault,
                             author=args.author[0],
                             autocommit=args.autocommit,
                             autosync=args.autosync,
                             editor=args.editor[0])

        return my_zk

    @staticmethod
    def not_implemented(args: Namespace) -> None:
        print("Function not implemented.")


@dataclass
class Cli(SubcommandsMixin):
    """
    Provide interface abstraction
    """
    prog: str
    description: str
    command_initialize: MutableMapping[str, Any]
    command_new: MutableMapping[str, Any]
    command_edit: MutableMapping[str, Any]
    command_delete: MutableMapping[str, Any]
    command_print: MutableMapping[str, Any]
    command_list: MutableMapping[str, Any]
    command_reindex: MutableMapping[str, Any]
    command_next: MutableMapping[str, Any]
    flag_vault: MutableMapping[str, Any]
    flag_author: MutableMapping[str, Any]
    flag_autocommit: MutableMapping[str, Any]
    flag_autosync: MutableMapping[str, Any]
    flag_editor: MutableMapping[str, Any]

    def __post_init__(self) -> None:
        # define global parser
        self.global_parser = ArgumentParser(prog=self.prog,
                                            description=self.description)
        commands, flags = self._get_commands()

        # add the normal global flags
        if flags:
            for flag in flags:
                flag_config = getattr(self, "flag_"+flag)
                self.global_parser.add_argument("--"+flag,
                                                **flag_config)

        # add the subcommands
        if commands:
            self.subparsers = self.global_parser.add_subparsers()
            for command in commands:
                self._create_subparsers(command)

    def _get_commands(self) -> tuple[list[str], list[str]]:
        """
        Get subcommands and flags from the dataclass fields.

        If the field starts with `command_` it means it's
        a subcommand. If it starts with `flag_`, it is a flag.
        """
        commands: list[str] = []
        flags: list[str] = []
        for comm in fields(self):
            if comm.name.startswith("command_"):
                commands.append(comm.name.removeprefix("command_"))
            elif comm.name.startswith("flag_"):
                flags.append(comm.name.removeprefix("flag_"))

        return commands, flags

    def _create_subparsers(self, command: str) -> None:
        """
        Create a subparser given the command.

        :param command: command to create a subparser for.
        """
        # get the command configuration: help, flags, etc.
        command_config = getattr(self, "command_"+command)
        parser = self.subparsers.add_parser(command,
                                            help=command_config.get("help", ""))

        # get the command's sub-flags
        subflags = command_config.get('flags', {})
        for flag in subflags:
            parser.add_argument(flag, **subflags[flag])

        # set the default action when invoking this sub-command.
        default_func = getattr(self, command, self.not_implemented)
        parser.set_defaults(func=default_func)

    def parse(self, *args: Any, **kwargs: Any) -> Namespace:
        cli_args: Namespace = self.global_parser.parse_args(*args, **kwargs)

        return cli_args

    def run(self, *args: Any, **kwargs: Any) -> None:
        cli_args = self.parse(*args, **kwargs)
        if hasattr(cli_args, 'func'):
            cli_args.func(cli_args)

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        cli_args = self.parse(*args, **kwargs)
        cli_args.func(cli_args)
