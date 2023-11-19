import curses
from enum import IntEnum

from notepy.zettelkasten.zettelkasten import Zettelkasten


ESCAPE_DELAY = 50
POSITION_OFFSET = 2


class OddKeys(IntEnum):
    ESCAPE = 27
    ALT_ENTER_1 = 10
    ALT_ENTER_2 = 13


# TODO: add window to the right containing metadata information if there is enough space
# TODO: Strict checks on overflow horizontally and vertically
# TODO: Implement scroll for when results overflow window
# TODO: implement tag and link filtering
# TODO: left and right arrow catch

class Interactive:
    def __init__(self, zk: Zettelkasten):
        self.w = curses.initscr()
        self.zk = zk
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)

    def print_results(self, results, pos):
        curses.curs_set(False)
        template = "  {}"
        for i in range(POSITION_OFFSET, curses.LINES):
            text = self.pad_results(i, results, template)
            self.w.addstr(i, 0, text)
            self.w.refresh()
        curses.curs_set(True)

    def draw_cursor(self, pos, old_pos):
        self.w.addstr(old_pos+POSITION_OFFSET, 0, " ")
        self.w.addstr(pos+POSITION_OFFSET, 0, ">", curses.color_pair(1))

    @staticmethod
    def catch_key(c, text, pos):
        endit = False
        match c:
            case curses.KEY_BACKSPACE:
                text = text[:-1]
                pos = 0
            case curses.KEY_ENTER | OddKeys.ALT_ENTER_1 | OddKeys.ALT_ENTER_2:
                endit = True
            case curses.KEY_UP:
                pos -= 1
            case curses.KEY_DOWN:
                pos += 1
            case _:
                text += chr(c)
                pos = 0

        return text, pos, endit

    @staticmethod
    def check_pos(pos, results):
        if pos < 0:
            pos = len(results) - 1
        if pos > len(results) - 1:
            pos = 0

        return pos

    @staticmethod
    def parse_text(text):
        return text

    @staticmethod
    def pad_text(text):
        length = len(text)
        length_to_fill = curses.COLS - length if length < curses.COLS else 0
        padding = " " * (length_to_fill-1)

        padded_text = text + padding

        return padded_text[:curses.COLS-1]

    def pad_results(self, draw_pos, results, template):
        if draw_pos < len(results)+POSITION_OFFSET:
            title = results[draw_pos-POSITION_OFFSET][0]
            text = self.pad_text(template.format(title))
        else:
            text = self.pad_text(" ")

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
        self.draw_cursor(pos, 0)
        self.w.addstr(0, 0, text)
        # break the loop when pressing ESC or C-c
        while (c := self.w.getch()) != OddKeys.ESCAPE:
            old_pos = pos
            # update text and pos based on key pressed
            new_text, pos, endit = self.catch_key(c, text, pos)
            if endit:
                break

            # only redraw results if input changed
            if new_text != text:
                # parse the text to intercept tag or link filters
                text = self.parse_text(new_text)
                # update list of notes
                result_list = self.zk.list_notes(title=[f"%{text}%"])

                self.print_results(result_list, pos)

                # pad the text
                padded_text = self.pad_text(text)
                self.w.addstr(0, 0, padded_text)

            # enforce checks on pos
            pos = self.check_pos(pos, result_list)
            self.draw_cursor(pos, old_pos)
            # put the cursor at the end of input
            self.w.addstr(0, len(text), "")

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
