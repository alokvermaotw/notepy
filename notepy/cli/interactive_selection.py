import curses
from enum import IntEnum
import re

from notepy.zettelkasten.zettelkasten import Zettelkasten


ESCAPE_DELAY = 50
POSITION_OFFSET = 2


class OddKeys(IntEnum):
    ESCAPE = 27
    ALT_ENTER_1 = 10
    ALT_ENTER_2 = 13


# TODO: add window to the right containing metadata information if there is enough space
# TODO: implement tag and link filtering
# TODO: implement multiselection
# TODO: comment!
class Interactive:
    def __init__(self, zk: Zettelkasten):
        self.w = curses.initscr()
        self.zk = zk
        self.cursor_pos = 0
        self.relative_cursor = 0
        self.relative_start = 0
        self.prev_relative_start = 0
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)

    def print_results(self, results, pos):
        curses.curs_set(False)
        template = "  {}"
        for i in range(POSITION_OFFSET, curses.LINES):
            text = self.pad_results(i+self.relative_start, results, template)
            self.w.addstr(i, 0, text)
            self.w.refresh()
        curses.curs_set(True)

    @staticmethod
    def check_cursor_pos(text, pos):
        length = len(text)
        if pos < 0:
            pos = 0
        if pos > length:
            pos = length

        return pos

    def catch_key(self, c, text, pos):
        endit = False
        redraw = False
        match c:
            case curses.KEY_ENTER | OddKeys.ALT_ENTER_1 | OddKeys.ALT_ENTER_2:
                endit = True
            case curses.KEY_UP:
                pos -= 1
            case curses.KEY_DOWN:
                pos += 1
            case curses.KEY_RESIZE:
                curses.resize_term(*self.w.getmaxyx())
                redraw = True
            case curses.KEY_BACKSPACE:
                cursor_pos = self.check_cursor_pos(text, self.cursor_pos-1)
                new_text = text[:cursor_pos] + text[cursor_pos+1:] if self.cursor_pos > 0 else text
                self.cursor_pos = cursor_pos
                if text != new_text:
                    pos = 0
                    self.relative_start = 0
                text = new_text
            case curses.KEY_DC:
                new_text = text[:self.cursor_pos] + text[self.cursor_pos+1:] if self.cursor_pos <= len(text) else text
                if text != new_text:
                    pos = 0
                    self.relative_start = 0
                text = new_text
            case curses.KEY_LEFT:
                # check cursor position
                self.cursor_pos = (self.cursor_pos-1) % (len(text)+1)
            case curses.KEY_RIGHT:
                # check cursor position
                self.cursor_pos = (self.cursor_pos+1) % (len(text)+1)
            case _:
                text = text[:self.cursor_pos] + chr(c) + text[self.cursor_pos:]
                text = text[:curses.COLS-1]
                if self.cursor_pos < curses.COLS-1:
                    self.cursor_pos += 1
                pos = 0
                self.relative_start = 0

        return text, pos, endit, redraw

    def check_pos(self, pos, results):
        length = len(results)
        redraw = False
        current_position = pos - self.relative_start + POSITION_OFFSET
        if current_position > curses.LINES:
            self.relative_start = pos - curses.LINES + POSITION_OFFSET
        if pos < 0:
            pos = length - 1
            if length >= curses.LINES - POSITION_OFFSET:
                self.relative_start = length - (curses.LINES - POSITION_OFFSET)
                redraw = True
            else:
                self.relative_start = 0
        elif pos > length - 1:
            pos = 0
            self.relative_start = 0
            redraw = True
        elif pos - self.relative_start >= curses.LINES - POSITION_OFFSET:
            self.relative_start += 1
            redraw = True
        elif pos - self.relative_start < 0:
            self.relative_start -= 1
            redraw = True

        return pos, redraw

    def draw_pointer(self, pos, old_pos):
        if (cancel_pos := old_pos-self.prev_relative_start+POSITION_OFFSET) < curses.LINES:
            self.w.addstr(cancel_pos, 0, " ")
        self.prev_relative_start = self.relative_start
        self.w.addstr(pos-self.relative_start+POSITION_OFFSET, 0, ">", curses.color_pair(1))

    @staticmethod
    def parse_text(text: str) -> tuple[str, list[str], list[str]]:
        tag_pattern = re.compile(r"#[^ ]*", re.IGNORECASE)
        link_pattern = re.compile(r"\[\[.*?\]\]")
        raw_tags = re.findall(tag_pattern, text)
        raw_links = re.findall(link_pattern, text)
        tags = []
        links = []
        for tag in raw_tags:
            text = text.replace(tag, "")
            tags.append("#%" + tag[1:] + "%")
        for link in raw_links:
            text = text.replace(link, "")
            links.append("%"+link.removeprefix('[[').removesuffix(']]')+"%")
        tags = tags if tags else None
        links = links if links else None
        return text.strip(), tags, links

    @staticmethod
    def pad_text(text):
        length = len(text)
        length_to_fill = curses.COLS - length if length < curses.COLS else 0
        padding = " " * (length_to_fill-1)

        padded_text = text + padding

        return padded_text[:curses.COLS-1]

    @staticmethod
    def pad_results(draw_pos, results, template):
        if draw_pos < len(results)+POSITION_OFFSET:
            title = results[draw_pos-POSITION_OFFSET][0]
            text = Interactive.pad_text(template.format(title))
        else:
            text = Interactive.pad_text(" ")

        return text

    def _main(self):
        # clear screen
        self.w.clear()
        # show cursor
        curses.curs_set(True)
        # set esc delay to 50 milliseconds
        curses.set_escdelay(ESCAPE_DELAY)
        # initial text
        text = ""
        # show all the notes at start
        result_list = self.zk.list_notes(title=[f"%{text}%"])
        # inital position of the cursor
        pos = 0
        self.print_results(result_list, pos)
        self.draw_pointer(pos, 0)
        self.w.addstr(0, 0, text, curses.color_pair(2))
        # break the loop when pressing ESC or C-c
        while (c := self.w.getch()) != OddKeys.ESCAPE:
            old_pos = pos
            # update text and pos based on key pressed
            new_text, pos, endit, redraw_key = self.catch_key(c, text, pos)
            if endit:
                break

            # enforce checks on pos
            pos, redraw_pos = self.check_pos(pos, result_list)
            # only redraw results if input changed
            if new_text != text or redraw_pos or redraw_key:
                # parse the text to intercept tag or link filters
                parsed_text, tags, links = self.parse_text(new_text)
                text = new_text
                # update list of notes
                result_list = self.zk.list_notes(title=[f"%{parsed_text}%"],
                                                 tags=tags,
                                                 links=links)

                self.print_results(result_list, pos)

                # pad the text
                padded_text = self.pad_text(text)
                self.w.addstr(0, 0, padded_text, curses.color_pair(2))

            self.draw_pointer(pos, old_pos)
            # put the cursor at the end of input
            self.w.move(0, self.cursor_pos)

        # if escape was pressed and there are results, return
        # the note ID.
        if len(result_list) > 0 and c != OddKeys.ESCAPE:
            return result_list[pos][1]

    def run(self):
        try:
            curses.noecho()
            curses.cbreak()
            self.w.keypad(True)

            return self._main()

        except KeyboardInterrupt:
            pass
        finally:
            curses.nocbreak()
            self.w.keypad(False)
            curses.echo()
            curses.endwin()
