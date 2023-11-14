import os
from pathlib import Path
from typing import Optional
import subprocess

from notepy.wrappers.base_wrapper import BaseWrapper, WrapperException


class Editor(BaseWrapper):
    """
    Basic editor wrapper

    :param editor: binary path of the editor.
    """

    def __init__(self, editor: Optional[str] = None) -> None:
        editor_env = os.getenv("EDITOR")
        visual_env = os.getenv("VISUAL")

        if editor is not None:
            self.editor = editor
        elif editor_env:
            self.editor = editor_env
        elif visual_env:
            self.editor = visual_env
        else:
            raise EditorException("Please set the EDITOR or VISUAL variable, or use the '--editor' flag")

        super().__init__(self.editor)

    def edit(self, path: str | Path, cwd: str | Path = "~") -> None:
        """
        Edit the given path
        """

        path = Path(path).expanduser()
        cwd = Path(cwd).expanduser()
        command: tuple[str, Path] = (self.editor, path)
        process_result = subprocess.run(command,
                                        cwd=cwd)
        process_returncode = process_result.returncode
        if process_returncode != 0:
            error_message = (f'Command "{command}" returned a non-zero exit status '
                             f"{process_returncode}. Below is the full stderr:\n\n"
                             f"{process_result.stdout.decode('utf-8')}")
            raise EditorException(error_message)


class EditorException(WrapperException):
    pass
