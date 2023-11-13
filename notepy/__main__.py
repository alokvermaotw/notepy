from notepy.cli.cli import Cli
from notepy.cli.cli_config import _COMMANDS


cli = Cli(prog="notepy", description="Zettelkasten manager", **_COMMANDS)
cli.run()
