"""
Small git wrapper to init, check status, add, commit and pull
"""

from __future__ import annotations
import subprocess
from typing import Optional, Any, Protocol
from pathlib import Path
from notepy.wrappers.base_wrapper import BaseWrapper, WrapperException, run_and_handle
from shutil import rmtree


# TODO: implement branch management?
# TODO: implement `git branch {branch} --set-upstream-to=`?
# TODO: better error handling for when dir is deleted
class Git(BaseWrapper):
    """
    Wrapper for git cli

    :param path: path to the repo
    """

    def __init__(self, path: Path | str, branch: str = "master"):
        super().__init__('git')
        self.path = Path(path).expanduser()
        self.git_path = self.path / ".git"
        self.branch = branch
        self._check_repo()

    def _check_repo(self) -> None:
        """
        Check that the directory provided is a git repo.
        """
        if not self.path.is_dir():
            raise GitException(f"'{self.path}' is not a directory.")
        if not self.git_path.is_dir():
            raise GitException(f"'{self.path}' is not a git repository."
                               "Use `Git.init('path')` to initialize.")

    @classmethod
    def init(cls,
             path: Path | str,
             to_ignore: list[str] = []) -> Git:
        """
        Initialize a new git repo in the directory provided.

        :param path: absolute path to the new git repo.
        :return: a Git wrapper
        """
        path = Path(path).expanduser()
        git_path = path / ".git"

        # sanity checks
        if not path.is_dir():
            raise GitException(f"'{path}' is not a directory.")
        if git_path.is_dir():
            raise GitException(f"'{path}' is already a git repository.")
        elif git_path.is_file():
            raise GitException(f"'{git_path}' is not a directory.")

        # create gitignore
        gitignore = path / ".gitignore"
        gitignore.touch(exist_ok=True)
        with open(gitignore, "a") as f:
            for ignored in to_ignore:
                f.write(ignored+"\n")

        # initialize repository
        process = run_and_handle("git init", exception=GitException, cwd=path)
        process = run_and_handle("git add .", exception=GitException, cwd=path)
        process = run_and_handle("git commit -m 'First commit'",
                                 exception=GitException,
                                 cwd=path)
        del process

        new_repo = cls(path)

        return new_repo

    def add(self) -> None:
        """
        Add changed files to staging area.
        """
        process = run_and_handle("git add -A",
                                 exception=GitException,
                                 cwd=self.path)
        del process

    def commit(self, msg: Optional[str] = "commit notes") -> None:
        """
        Commit the staging area.
        """
        process = run_and_handle(f"git commit -m '{msg}'",
                                 exception=GitException,
                                 cwd=self.path)
        del process

    def has_changed(self) -> bool:
        """
        Determine if there are changes to commit
        """
        changed = False
        if "nothing to commit" not in self.status:
            changed = True

        return changed

    def push(self) -> None:
        """
        Push to origin.
        """
        if not self._origin_exists():
            raise GitException("""origin does not exist.""")

        process = run_and_handle(f'git push origin {self.branch}',
                                 exception=GitException,
                                 cwd=self.path,
                                 comment="Check that origin is correct")
        del process

    def pull(self) -> None:
        """
        Pull from origin
        """
        if not self._origin_exists():
            raise GitException("""Origin does not exist.""")

        process = run_and_handle(f'git pull origin {self.branch}',
                                 exception=GitException,
                                 cwd=self.path,
                                 comment="Check that origin is correct")
        del process

    def commit_on_change(self, msg: str = "commit notes") -> None:
        if self.has_changed():
            self.add()
            self.commit(msg)

    def save(self, msg: str = "commit notes") -> None:
        self.commit_on_change(msg)
        if self.origin:
            self.push()

    def _origin_exists(self) -> bool:
        """
        Check if origin is defined.
        """
        command = ['git', 'config', '--get', 'remote.origin.url']
        origin = subprocess.run(command,
                                cwd=self.path,
                                capture_output=True)

        origin_exists = True
        if origin.returncode == 1:  # error code given by this failed action
            origin_exists = False
        elif origin.returncode != 0:  # for any other: raise exception
            error_message = (f"Command '{' '.join(command)}' returned a non-zero exit status "
                             f"{origin.returncode}. Below is the full stderr:\n\n"
                             f"{origin.stdout.decode('utf-8')}")
            raise GitException(error_message)

        return origin_exists

    @property
    def status(self) -> str:
        """
        Check status of current git repo.
        """
        process = run_and_handle("git status",
                                 exception=GitException,
                                 cwd=self.path)
        status = process.stdout.decode('utf-8')

        return status

    @status.setter
    def status(self, value: Any) -> None:
        raise GitException("You cannot do this operation.")

    @status.deleter
    def status(self) -> None:
        raise GitException("You cannot do this operation.")

    @property
    def origin(self) -> str:
        """
        get origin URL.
        """
        command = ['git', 'config', '--get', 'remote.origin.url']
        process = subprocess.run(command,
                                 cwd=self.path,
                                 capture_output=True)

        if process.returncode == 1:  # error code given by this failed action
            origin = ""
        elif process.returncode != 0:  # for any other: raise exception
            error_message = (f"Command '{' '.join(command)}' returned a non-zero exit status "
                             f"{process.returncode}. Below is the full stderr:\n\n"
                             f"{process.stdout.decode('utf-8')}")
            raise GitException(error_message)
        else:
            origin = process.stdout.decode('utf-8').strip()

        return origin

    @origin.setter
    def origin(self, value: str) -> None:
        """
        Update origin

        :param value: the URL of origin.
        """
        if self._origin_exists():
            command = f'git remote set-url origin "{value}"'
        else:
            command = f'git remote add origin "{value}"'

        process = run_and_handle(command, exception=GitException, cwd=self.path)
        del process

    @origin.deleter
    def origin(self) -> None:
        """
        Delete origin
        """
        if not self._origin_exists():
            raise GitException("origin does not exist.")

        process = run_and_handle('git remote remove origin',
                                 exception=GitException,
                                 cwd=self.path)
        del process

    def __repr__(self) -> str:

        return str(self.path)

    def __str__(self) -> str:
        string = f"git repository at '{self.path}'\n\n"
        string += f"{self.status}"

        return string


class GitMixinProtocol(Protocol):
    """
    Protocol class for type-checker
    """
    @property
    def vault(self) -> Path: ...

    def _detect_git_repo(self, path: Path) -> Git | None: ...


# from: https://stackoverflow.com/questions/51930339/how-do-i-correctly-add-type-hints-to-mixin-classes,
# second answer.
class GitMixin:
    """
    Mixin for git support.
    Assumes that class that inherits has a path attribute.
    """

    def git_init(self: GitMixinProtocol,
                 to_ignore: list[str] = ['.last', '.tmp']) -> Git:
        """
        Initialize git repo

        :param to_ignore: list of names to add to .gitignore
        :return: Git object
        """
        git = Git.init(self.vault, to_ignore=to_ignore)

        return git

    def git_remove(self: GitMixinProtocol) -> None:
        """
        Remove repository.
        """
        if self._detect_git_repo(self.vault):
            git_path: Path = self.vault / ".git"
            gitignore_path: Path = self.vault / ".gitignore"
            gitignore_path.unlink(missing_ok=True)
            rmtree(str(git_path))
        else:
            raise GitException(f"'{self.vault}' is not a git repository.")

    def get_remote(self: GitMixinProtocol) -> str | None:
        """
        Show remote origin of a git repo.
        """
        if (git := self._detect_git_repo(self.vault)):
            return git.origin

        return None

    def set_remote(self: GitMixinProtocol, origin: str) -> None:
        """
        Add remote origin to a git repo.

        :param origin: URL of the remote.
        """
        if (git := self._detect_git_repo(self.vault)):
            git.origin = origin

    def remove_remote(self: GitMixinProtocol) -> None:
        """
        Delete remote origin from a git repo.
        """
        if (git := self._detect_git_repo(self.vault)):
            del git.origin

    def push_remote(self: GitMixinProtocol) -> None:
        """
        Push to remote
        """
        if (git := self._detect_git_repo(self.vault)):
            git.push()

    def pull_remote(self: GitMixinProtocol) -> None:
        """
        Push to remote
        """
        if (git := self._detect_git_repo(self.vault)):
            git.pull()

    def sync(self: GitMixinProtocol) -> None:
        """
        Synchronize with remote origin.
        """
        if (git := self._detect_git_repo(self.vault)):
            git.pull()
            git.push()

    def commit_and_sync(self: GitMixinProtocol,
                        msg: str = "commit notes",
                        commit: bool = True,
                        push: bool = True) -> None:
        """
        Commit and sync
        """
        if (git := self._detect_git_repo(self.vault)):
            if commit:
                git.commit_on_change(msg)
            if push:
                git.push()

    def _detect_git_repo(self, path: Path) -> Git | None:
        """
        Detect if a directory is also a git repo.

        :return: Git object
        """
        try:
            git = Git(path)
            return git
        except GitException:
            return None


# TODO: more granular exceptions?
class GitException(WrapperException):
    """Error raised when git is involved"""
