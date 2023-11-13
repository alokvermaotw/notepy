from notepy.cli.cli import Cli
from notepy.cli.cli_config import _COMMANDS


def run():
    cli = Cli(prog="notepy", description="Zettelkasten manager", **_COMMANDS)
    cli.run()


if __name__ == "__main__":
    run()
