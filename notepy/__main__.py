from argparse import ArgumentParser
from notepy.zettelkasten.zettelkasten import Zettelkasten, Note
from notepy.cli.cli import Cli
from pathlib import Path
import json

with open(Path(__file__).parent / "cli/cli_config.json") as f:
    _COMMANDS = json.load(f)

cli = Cli(prog="notepy", description="Zettelkasten manager", **_COMMANDS)
cli.parse()
