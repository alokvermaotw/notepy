"""
Small git wrapper to init, check status, add, commit and pull
"""

from __future__ import annotations
import subprocess
from typing import Optional
from pathlib import Path
from base_cli import BaseCli, CliException


class Git(BaseCli):
    """
    Wrapper for git cli

    :param path: path to the repo
    """

    def __init__(self, path: Path):
        super().__init__('git')
        self.path = path.expanduser()
        self.git_path = self.path.joinpath(".git")
        self._cmd_exists()
        self._is_repo()

    def _is_repo(self) -> None:
        """
        Check that the directory provided is a git repo.
        """
        if not self.path.is_dir():
            raise GitException(f"{self.path} is not a directory.")
        if not self.git_path.is_dir():
            raise GitException(f"{self.path} is not a git repository.")

    @classmethod
    def init(cls, path: Path) -> Git:
        """
        Initialize a new git repo in the directory provided.

        :param path: absolute path to the new git repo.
        :return: a Git wrapper
        """
        path = path.expanduser()
        git_path = path.joinpath(".git")
        if not path.is_dir():
            raise GitException(f"{path} is not a directory.")
        if git_path.is_dir():
            raise GitException(f"{path} is already a git repository.")

        subprocess.run(['git', 'init', path], check=True, capture_output=True)
        new_repo = cls(path)

        return new_repo

    def add(self):
        """
        Add changed files to staging area.
        """

    def commit(self, msg: Optional[str] = "commit notes"):
        """
        Commit the staging area.
        """

    def push(self):
        """
        Push to origin.
        """

    def add_origin(self, origin: str):
        """
        Add remote origin.
        """

    def check_origin(self) -> bool:
        """
        Check if origin is defined.
        """

    def __repr__(self) -> str:

        return str(self.path)

    def __str__(self) -> str:
        string = f"git repository at {self.path}\n\n"
        string += f"{self.status}"

        return string

    @property
    def status(self):
        """
        Check status of current git repo.
        """
        status = subprocess.run(['git', 'status'],
                                check=True,
                                capture_output=True,
                                encoding='utf-8',
                                cwd=self.path).stdout

        return status

    @status.setter
    def status(self, value):
        raise GitException("You cannot do this operation.")

    @status.deleter
    def status(self):
        raise GitException("You cannot do this operation.")


class GitException(CliException):
    """Error raised when git is involved"""
