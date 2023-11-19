import curses
from notepy.zettelkasten.zettelkasten import Zettelkasten
from enum import IntEnum


ESCAPE_DELAY = 50
POSITION_OFFSET = 2


class OddKeys(IntEnum):
    ESCAPE = 27
    ALT_ENTER_1 = 10
    ALT_ENTER_2 = 13


# TODO: add window to the right containing metadata information if there is enough space
# TODO: Strict checks on overflow horizontally and vertically
# TODO: Implement scroll for when results overflow window

class Interactive:
    def __init__(self, zk: Zettelkasten, no_color: bool = False):
        self.w = curses.initscr()
        self.no_color = no_color
        self.zk = zk
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)

    def print_results(self, results):
        curses.curs_set(False)
        template = "  {}"
        template = self.pad_text(template)
        text = self.pad_results([template.format(title) for title, _ in results])
        for i in range(POSITION_OFFSET, curses.LINES):
            if self.no_color:
                self.w.addstr(i, 0, text[i-POSITION_OFFSET])
            else:
                self.w.addstr(i, 0, text[i-POSITION_OFFSET], curses.color_pair(1))
            self.w.refresh()
        curses.curs_set(True)

    def draw_cursor(self, pos, old_pos):
        self.w.addstr(old_pos+POSITION_OFFSET, 0, " ")
        if self.no_color:
            self.w.addstr(pos+POSITION_OFFSET, 0, ">")
        else:
            self.w.addstr(pos+POSITION_OFFSET, 0, ">", curses.color_pair(2))

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

    @staticmethod
    def pad_results(results):
        length = len(results)
        length_to_fill = curses.LINES - length if length < curses.LINES else 0
        results += [" "*(curses.COLS-1) for _ in range(length_to_fill)]

        return results

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
        self.print_results(result_list)
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

                self.print_results(result_list)

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
