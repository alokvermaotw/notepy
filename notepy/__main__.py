from argparse import ArgumentParser
from notepy.zettelkasten.zettelkasten import Zettelkasten, Note
from pathlib import Path
import json

with open(Path(__file__).parent / "cli/cli_config.json") as f:
    _COMMANDS = json.load(f)


def extract_command(parser, command):
    command_flags = _COMMANDS[command]
    for flag in command_flags:
        parser.add_argument(flag, **command_flags[flag])


def create_subparsers(global_parser, configuration, **kwargs):
    commands = [comm for comm in configuration if not comm.startswith("--")]
    # flags = [comm for comm in configuration if comm.startswith("--")]

    if not commands:
        return None

    subparsers = global_parser.add_subparsers(**kwargs)

    for comm in commands:
        options = configuration[comm]
        parser = subparsers.add_parser(comm, help=options.get("help", ""))
        subflags = options.get('flags', {})
        for flag in subflags:
            parser.add_argument(flag, **subflags[flag])


global_parser = ArgumentParser(prog='notepy',
                               description="Zettelkasten manager")
create_subparsers(global_parser, _COMMANDS, title="Commands", description="Command to interact with your vault")

args = global_parser.parse_args()
print(args.path)
