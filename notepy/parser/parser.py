"""
Parsers for various elements of a note
"""
from typing import Sequence, Any
from abc import ABC, abstractmethod
from pathlib import Path
from io import TextIOWrapper
from datetime import datetime
from string import punctuation
import re


_IN_CONTEXT = True
_OUT_CONTEXT = False
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"
_INVALID_CHARS = punctuation.replace("_", "").replace("#", "")


class BaseParser(ABC):
    @abstractmethod
    def parse(self, target: str | Path | TextIOWrapper) -> (dict[str], TextIOWrapper):
        ...


class HeaderParser(BaseParser):
    """
    Class dedicated to parse the frontmatter of a note.

    :param parsing_obj: the values the parser should collect
    :param delimiter: the delimiter symbol that represents start
                      and end of the frontmatter
    :param special_names: list of names for which a dedicated
                          parser has been defined in the form
                          of _NAME_parser(self, value), where
                          NAME is a member of special_names
    """

    def __init__(self, parsing_obj: Sequence[str],
                 delimiter: str = '---',
                 special_names: Sequence[str] = ['date', 'tags']):
        self.parsing_obj = parsing_obj
        self.delimiter = delimiter
        self.special_names = special_names

    def parse(self, target: str | Path | TextIOWrapper) -> (dict[str], TextIOWrapper):
        """
        Main parsing function. It will open a file stream,
        parse the content, and return the parsed frontmatter
        and the remaining stream so to pass it to another parser.

        :param path: path to the note to parse
        :return: parsed items in form of a dictionary,
                 and the rest of the file stream
        """
        file_obj = open(Path(target).expanduser(), "r") if isinstance(
            target, (Path, str)) else target
        context = _OUT_CONTEXT
        parsing_obj = set(self.parsing_obj)
        parsed_obj = {}

        for line in file_obj:
            clean_line = line.strip()

            # check if we're inside frontmatter
            if clean_line == self.delimiter and not context:
                context = _IN_CONTEXT
                continue
            elif clean_line == self.delimiter and context:
                context = _OUT_CONTEXT
                break

            name, value = self._line_parser(clean_line, parsing_obj)
            # apply special parsing to defined special names
            if name in self.special_names:
                parser = getattr(self, f'_{name}_parser', HeaderParser._id)
                value = parser(value)

            parsed_obj[name] = value

        else:
            raise FrontmatterException("Frontmatter has not been closed.")

        return parsed_obj, file_obj

    def _line_parser(self, line: str, parsing_obj: set[str]) -> (str, Any):
        """
        Parse a line into key/value pairs.

        :param line: line to parse
        :return: (key, value)
        """
        split_line = line.split(': ')

        # error checking for no name/value pair
        if len(split_line) <= 1:
            # if the name has no values, e.g.: `tags:`, don't raise exception
            if line.endswith(':'):
                split_line = [line.removesuffix(':'), '']
            else:
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
        if name not in parsing_obj:
            error_text = (f"'{name}' is not a recognized value or is a duplicate."
                          f"\nRecognized values: {', '.join(self.parsing_obj)}")
            raise FrontmatterException(error_text)

        parsing_obj.discard(name)

        return name, value

    def _date_parser(self, date: str) -> datetime:
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

    def _tags_parser(self, tags: str) -> set[str]:
        """
        Tags parser.

        :param tags: string of tags separated by space.
                     Each tag must start with #.
        :return: iterable of tags.
        """
        # TODO: issue a warning for malformed tags

        # parse out every special char except # and _
        clean_tags = tags.translate(tags.maketrans(
            _INVALID_CHARS, ' ' * len(_INVALID_CHARS)))
        # split tags, clean out whitespace and remove words
        # not starting with #
        tmp_tags_list: list[str] = clean_tags.split(' ')
        tags_list = set([tag for tag in tmp_tags_list
                         if tag != '' and tag.startswith('#')])

        return tags_list

    def _id(self, obj: Any) -> Any:
        """
        Returns itself

        :param obj: an object
        :return: the same object
        """
        return obj


class BodyParser(BaseParser):
    """
    Parser for body of note.

    :param header1: identifier for header of note.
    :param link_del: identifier for link encapsulation
    """

    def __init__(self,
                 header1: str = "# ",
                 link_del: (str, str) = ("[[", "]]")
                 ):
        self.header1 = header1
        self.link_del = link_del

    def parse(self, target: str | Path | TextIOWrapper) -> (dict[Sequence[str]], TextIOWrapper):
        file_obj = open(Path(target).expanduser(), "r") if isinstance(
            target, (Path, str)) else target
        headers = []
        links = []
        body = []
        context = _OUT_CONTEXT

        for line in file_obj:
            clean_line = line.strip()
            body.append(clean_line)

            # first line needs to be a title
            if clean_line != "" and not clean_line.startswith(self.header1) and not context:
                raise BodyException("The body needs to start with a title")
            elif clean_line.startswith(self.header1) and not context:
                context = _IN_CONTEXT

            # parse for header 1
            if clean_line.startswith(self.header1):
                headers.append(clean_line)
                continue

            # parse for links
            line_links = self._link_parser(clean_line)
            links.extend(line_links)

        return {'header': headers, 'links': set(links), 'body': body}, file_obj

    def _link_parser(self, line: str) -> set[str]:
        """
        Parse a line for links.

        :param line: line to parse
        :return: set of links contained in the line
        """

        start_link = self.link_del[0]
        end_link = self.link_del[1]
        # find links with regex
        pattern = re.compile(f"{re.escape(start_link)}.*?{re.escape(end_link)}")
        # remove link pre- and suffixes
        line_links = [link.removeprefix(start_link).removesuffix(end_link)
                      for link in pattern.findall(line)]
        # remove empty link
        line_links = [link for link in line_links if link != ""]

        return line_links


class FrontmatterException(Exception):
    """This exception is raised when the header is not in the correct format"""


class BodyException(Exception):
    """This exception is raised when the body
     elements of a note are not in the correct format"""
