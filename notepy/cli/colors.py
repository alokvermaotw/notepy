from enum import Enum
from typing import Protocol


class Show(Protocol):
    def __str__(self) -> str:
        ...


class Colors(Enum):
    BLACK_FG = "\033[30m"
    RED_FG = "\033[31m"
    GREEN_FG = "\033[32m"
    YELLOW_FG = "\033[33m"
    BLUE_FG = "\033[34m"
    MAGENTA_FG = "\033[35m"
    CYAN_FG = "\033[36m"
    WHITE_FG = "\033[37m"
    BLACK_BG = "\033[40m"
    RED_BG = "\033[41m"
    GREEN_BG = "\033[42m"
    YELLOW_BG = "\033[43m"
    BLUE_BG = "\033[44m"
    MAGENTA_BG = "\033[45m"
    CYAN_BG = "\033[46m"
    WHITE_BG = "\033[47m"
    RESET = "\033[0m"

    def colorize(self, text: Show) -> str:
        return self.value + str(text) + Colors.RESET.value


def color(text: Show,
          COLOUR: str,
          context: str = "FG",
          no_color: bool = False) -> str:
    if context not in ["FG", "BG"]:
        raise ValueError("context can only be 'FG' or 'BG'.")
    if not no_color:
        color_name = "_".join([COLOUR, context])
        return Colors[color_name].colorize(text)
    return str(text)
