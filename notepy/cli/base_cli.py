from abc import ABC, abstractmethod
import subprocess


class BaseCli(ABC):
    """
    Base wrapper for CLI utilities.

    :param cmd: the CLI command to wrap.
    """

    def __init__(self, cmd: str):
        self.cmd = cmd
        self._cmd_exists()

    def _cmd_exists(self):
        """
        Check that the command is present on the system.
        """
        try:
            subprocess.run(self.cmd, capture_output=True, check=True)
        except FileNotFoundError:
            raise CliException(f'{self.cmd} is not present on your system.')
        except subprocess.CalledProcessError:
            pass


class CliException(Exception):
    """Exception to rise whenever some CLI wrapper throws"""
