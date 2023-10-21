from typing import Sequence, Any
from abc import ABC, abstractmethod
from pathlib import Path
from io import TextIOWrapper
from datetime import datetime
from string import punctuation


_IN_CONTEXT = True
_OUT_CONTEXT = False
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"
_INVALID_CHARS = punctuation.replace("_", "").replace("#", "")


class BaseParser(ABC):
    @abstractmethod
    def parse(self, path: Path) -> (dict[str], TextIOWrapper):
        ...


class HeaderParser(BaseParser):
    """
    Class dedicated to parse the frontmatter of a note.

    Note: special_names is a list of names for which
          a dedicated parser has been defined in the form of
          _NAME_parser(self, value), where NAME is a member of
          special_names.
    """

    def __init__(self, parsingObj: Sequence[str],
                 delimiter: str = '---',
                 special_names: list[str] = ['date', 'tags']):
        self.parsingObj = parsingObj
        self.delimiter = delimiter
        self.special_names = special_names

    def parse(self, path: Path) -> (dict[str], TextIOWrapper):
        """
        Main parsing function. It will open a file stream,
        parse the content, and return the parsed frontmatter
        and the remaining stream so to pass it to another parser.

        :param path: path to the note to parse
        :return: parsed items in form of a dictionary,
                 and the rest of the file stream
        """
        fileObj = open(path, "r")
        context = _OUT_CONTEXT
        parsingObj = set(self.parsingObj)
        parsedObj = {}

        for line in fileObj:
            clean_line = line.strip()

            # check if we're inside frontmatter
            if clean_line == self.delimiter and not context:
                context = _IN_CONTEXT
                continue
            elif clean_line == self.delimiter and context:
                context = _OUT_CONTEXT
                break

            name, value = self._line_parser(clean_line, parsingObj)
            # apply special parsing to defined special names
            if name in self.special_names:
                parser = getattr(self, f'_{name}_parser', HeaderParser._id)
                value = parser(value)

            parsedObj[name] = value

        else:
            raise FrontmatterException("Frontmatter has not been closed.")

        return parsedObj, fileObj

    def _line_parser(self, line: str, parsingObj: set[str]) -> (str, Any):
        """
        Parse a line into key/value pairs.

        :param line: line to parse
        :return: (key, value)
        """
        split_line = line.split(': ')

        # error checking for no name/value pair
        if len(split_line) <= 1:
            error_text = ("The following line is missing a colon "
                          f"followed by whitespace:\n{line}")
            raise FrontmatterException(error_text)

        # error checking for too many colons (no newline allowed)
        if len(split_line) >= 3:
            error_text = ("The following line has too many colons:"
                          f"\n{line}\n\nYou can have only one colon "
                          "followed by whitespace.")
            raise FrontmatterException(error_text)

        # check if name is correct
        name, value = split_line
        name = name.strip()
        value = value.strip()
        if name not in parsingObj:
            error_text = (f"'{name}' is not a recognized value or is a duplicate."
                          f"\nRecognized values: {', '.join(self.parsingObj)}")
            raise FrontmatterException(error_text)

        parsingObj.discard(name)

        return name, value

    def _date_parser(self, date: str):
        """
        Date value parser.

        :param date: date in string format %Y-%m-%dT%H:%M:%S
        :return: corresponding datetime value.
        """
        try:
            parsed_date = datetime.strptime(date, _DATE_FORMAT)
        except ValueError as e:
            raise FrontmatterException(
                f"There is an error in the date format: {e}")

        return parsed_date

    def _tags_parser(self, tags: str) -> list[str]:
        """
        Tags parser.

        :param tags: string of tags separated by space.
                     Each tag must start with #.
        :return: list of tags.
        """
        # TODO: issue a warning for malformed tags

        # parse out every special char except # and _
        clean_tags = tags.translate(tags.maketrans(
            _INVALID_CHARS, ' ' * len(_INVALID_CHARS)))
        # split tags, clean out whitespace and remove words
        # not starting with #
        tmp_tags_list: list[str] = clean_tags.split(' ')
        tags_list = [tag for tag in tmp_tags_list
                     if tag != '' and tag.startswith('#')]

        return tags_list

    def _id(self, obj: Any) -> Any:
        """
        Returns itself

        :param obj: an object
        :return: the same object
        """
        return obj


class BodyParser:
    ...


class FrontmatterException(Exception):
    """This exception is raised when the header is not in the correct format"""
