"""
Small git wrapper to init, check status, add, commit and pull
"""

from __future__ import annotations
import subprocess
from typing import Optional
from pathlib import Path


# TODO: add content of stdout to error messages
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

        try:
            # TODO: add .gitignore for .index.db
            subprocess.run(['git', 'init', path],
                           check=True, capture_output=True)
            subprocess.run(['git', 'add', '.'], check=True,
                           capture_output=True, cwd=path)
            subprocess.run(['git', 'commit', '-m', 'First commit'],
                           capture_output=True, cwd=path, check=True)
        except subprocess.CalledProcessError as e:
            raise GitException(f"""Something went wrong: {e}""")

        new_repo = cls(path)

        return new_repo

    def add(self) -> None:
        """
        Add changed files to staging area.
        """
        try:
            subprocess.run([self.cmd, 'add', '-A'], check=True,
                           cwd=self.path, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise GitException(f"""Something went wrong: {e}""")

    def commit(self, msg: Optional[str] = "commit notes") -> None:
        """
        Commit the staging area.
        """
        try:
            subprocess.run([self.cmd, 'commit', '-m', msg],
                           check=True, cwd=self.path, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise GitException(f"""Something went wrong: {e}""")

    def push(self) -> None:
        """
        Push to origin.
        """
        try:
            if self._check_origin():
                subprocess.run([self.cmd, 'push'], check=True,
                               cwd=self.path, capture_output=True)
            else:
                raise GitException("""origin does not exist.""")
        except subprocess.CalledProcessError as e:
            raise GitException(f"""Something went wrong: {e}.
                Check that origin is correct.""")

    def add_origin(self, origin: str) -> None:
        """
        Add remote origin.
        """
        if self._check_origin():
            raise GitException("""origin already exists.""")
        try:
            subprocess.run([self.cmd, 'remote', 'add', 'origin',
                           origin], check=True, cwd=self.path, capture_output=True)
            subprocess.run([self.cmd, 'push', 'origin', 'master', '--set-upstream'],
                           check=True, capture_output=True, cwd=self.path)
        except subprocess.CalledProcessError as e:
            raise GitException(f"""Something went wrong: {e}.
                Check that origin is correct""")

    def _check_origin(self) -> bool:
        """
        Check if origin is defined.
        """
        origin = subprocess.run([self.cmd,
                                 'config',
                                 '--get',
                                 'remote.origin.url'], cwd=self.path, capture_output=True)

        origin_exists = True
        if origin.returncode == 1:  # error code given by this failed action
            origin_exists = False
        elif origin.returncode != 0:  # for any other: raise exception
            origin.check_returncode()

        return origin_exists

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
        status = subprocess.run([self.cmd, 'status'],
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
