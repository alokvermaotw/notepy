from abc import ABC
import subprocess
from shlex import split
from pathlib import Path


# TODO: add possibility to run in background (or use threads)
# one problem arising is that pushing to git remote takes time.
def run_and_handle(command: str,
                   exception: type[Exception],
                   cwd: Path | str = ".",
                   comment: str = "") -> subprocess.CompletedProcess[bytes]:
    """
    Utility function for easy CalledProcessError handling. It calls a command
    and manages exceptions by calling GitException, together with the stderr
    of the process.

    :param command: the command to execute.
    :param cwd: the working directory of the environment for the command.
    :param comment: optional comment to add to the exception message.
    :return: the completed process object.
    """
    split_cmd = split(command)
    process_result = subprocess.run(split_cmd,
                                    cwd=cwd,
                                    stderr=subprocess.STDOUT,
                                    stdout=subprocess.PIPE)

    process_returncode = process_result.returncode
    if process_returncode != 0:
        error_message = (f'Command "{command}" returned a non-zero exit status '
                         f"{process_returncode}. Below is the full stderr:\n\n"
                         f"{process_result.stdout.decode('utf-8')}")
        error_message = error_message + \
            f"\n\n{comment}" if comment else error_message
        raise exception(error_message)

    return process_result


class BaseWrapper(ABC):
    """
    Base wrapper for CLI utilities.

    :param cmd: the CLI command to wrap.
    """

    def __init__(self, cmd: str):
        self.cmd = cmd
        self._cmd_exists()

    def _cmd_exists(self) -> None:
        """
        Check that the command is present on the system.
        """
        try:
            subprocess.run(['which', self.cmd], capture_output=True, check=True)
        except FileNotFoundError:
            raise WrapperException('`which` is not present on your system. '
                                   'Please install it before anything else.')
        except subprocess.CalledProcessError:
            raise WrapperException(f"'{self.cmd}' is not present on your system.")


class WrapperException(Exception):
    """Exception to raise whenever some CLI wrapper throws"""
