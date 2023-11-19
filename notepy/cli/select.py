import curses
from curses import wrapper
from notepy.zettelkasten.zettelkasten import Zettelkasten
from enum import IntEnum

zk = Zettelkasten(vault="/home/ld/Desktop/Repos/experiment_design",
                  author="Lorenzo Drumond")

# print(zk.list_notes(title=["%go i%"]))

ESCAPE = 27
ALT_ENTER_1 = 10
ALT_ENTER_2 = 13


class OddKeys(IntEnum):
    ESCAPE = 27
    ALT_ENTER_1 = 10
    ALT_ENTER_2 = 13


def pretty_print(results, stdscr, pos=0):
    curses.curs_set(False)
    template = "  {}"
    template_fill = curses.COLS - len(template) if len(template) < curses.COLS else 0
    template = template+" "*(template_fill-1)
    text = [template.format(title) for title, _ in results]
    length = len(results)
    fill = curses.LINES - length if length < curses.LINES else 0
    text += [" "*(curses.COLS-1) for _ in range(fill)]
    for i in range(2, curses.LINES):
        # title, zk_id = results[i]
        # stdscr.addstr(i, 0, f"{title}, {zk_id}")
        stdscr.addstr(i, 0, text[i-2])
        if i == pos+2 and text[i-2].strip():
            stdscr.addstr(i, 0, ">")
        stdscr.refresh()
    curses.curs_set(True)


def main(stdscr):
    # clear screen
    stdscr.clear()
    curses.curs_set(True)
    curses.set_escdelay(50)
    text = ""
    result_list = zk.list_notes(title=[f"%{text}%"])
    pretty_print(result_list, stdscr)
    stdscr.addstr(0, 0, text)
    pos = 0
    try:
        while (c := stdscr.getch()) != OddKeys.ESCAPE:
            match c:
                case curses.KEY_BACKSPACE:
                    text = text[:-1]
                    pos = 0
                case curses.KEY_ENTER | OddKeys.ALT_ENTER_1 | OddKeys.ALT_ENTER_2:
                    break
                case curses.KEY_UP:
                    pos -= 1
                    if pos < 0:
                        pos = 0
                case curses.KEY_DOWN:
                    pos += 1
                case _:
                    text += chr(c)
                    pos = 0
            result_list = zk.list_notes(title=[f"%{text}%"])
            if pos > len(result_list)-1:
                pos = len(result_list)-1
            pretty_print(result_list, stdscr, pos)
            fill_text = curses.COLS - len(text) if len(text) < curses.COLS else 0
            fill = " " * (fill_text-1)
            stdscr.addstr(0, 0, text+fill)
            stdscr.addstr(0, len(text), "")
        if len(result_list) > 0 and c != OddKeys.ESCAPE:
            return result_list[pos][1]
    except KeyboardInterrupt:
        pass


a = wrapper(main)
print(a)
