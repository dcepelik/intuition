class Screen:
    def __init__(self):
        self.seq = 1
        self.rendered_seq = 0

class MockScreen(Screen):
    def __init__(self, nrows, ncols):
        super().__init__()
        self.nrows = nrows
        self.ncols = ncols
        self.rows = None
        self.clear()

    def clear(self):
        self.rows = [''] * self.nrows

    def put(self, y, x, text, classes):
        if y < 0 or y >= self.nrows or x < 0 or x >= self.ncols:
            raise RuntimeError('attempted to put a string off the screen')
        self.rows[y] = self.rows[y][0:x].ljust(x) + text + self.rows[y][x:]

    def measure(self, widget):
        return widget.size

    @property
    def content(self):
        return '\n'.join(self.rows)

    def __repr__(self):
        return self.content

import os
from enum import IntEnum

class AnsiFormat(IntEnum):
    BOLD = 1
    DIM = 2
    UNDERLINED = 4
    REVERSE = 7

class AnsiColor(IntEnum):
    DEFAULT = 39
    BLACK = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36
    LIGHT_GRAY = 37
    DARK_GRAY = 90
    LIGHT_RED = 91
    LIGHT_GREEN = 92
    LIGHT_YELLOW = 93
    LIGHT_BLUE = 94
    LIGHT_MAGENTA = 95
    LIGHT_CYAN = 96
    WHITE = 97

class Theme:
    def __init__(self):
        self.classes = {}

    def set_class(self, name, fg = None, bg = None, fmt = None):
        self.classes[name] = (fg, bg, fmt)

    def get_style(self, classes):
        fg, bg, fmt = (AnsiColor.DEFAULT, AnsiColor.DEFAULT, None)
        for name in classes:
            if name in self.classes:
                cls_fg, cls_bg, cls_fmt = self.classes[name]
                if cls_fg:
                    fg = cls_fg
                if cls_bg:
                    bg = cls_bg
                if cls_fmt:
                    fmt = cls_fmt
        return (fg, bg, fmt)

class AnsiScreen(Screen):
    def __init__(self, nrows, ncols):
        super().__init__()
        self.nrows = nrows
        self.ncols = ncols
        self.rows = None
        self.theme = Theme()
        self.theme.set_class('red-text', fg = AnsiColor.RED)
        self.theme.set_class('focused', fmt = AnsiFormat.BOLD)
        self.theme.set_class('bluebg', bg = AnsiColor.BLUE, fg = AnsiColor.BLACK)
        self.clear()

    def clear(self):
        self.rows = [[] for _ in range(0, self.nrows)]

    @staticmethod
    def write_cmd(cmd):
        os.write(1, bytes('\x1b{}'.format(cmd), 'ascii'))

    @staticmethod
    def write_attr(attr):
        AnsiScreen.write_cmd('[{}m'.format(attr))

    @staticmethod
    def advance(ncols):
        AnsiScreen.write_cmd('[{}{}'.format(abs(ncols), 'D' if ncols < 0 else 'C'))

    @staticmethod
    def write(text):
        os.write(1, bytes(text, 'utf-8'))

    def set_attrs(self, fg, bg, fmt):
        AnsiScreen.write_attr(fg)
        AnsiScreen.write_attr(bg + 10)
        if fmt:
            AnsiScreen.write_attr(fmt)

    def reset_attrs(self):
        AnsiScreen.write_attr(0)

    def put(self, y, x, text, classes):
        if y < 0 or y >= self.nrows or x < 0 or x >= self.ncols:
            raise RuntimeError('attempted to put a string off the screen')
        self.rows[y].append((x, text, self.theme.get_style(classes)))

    def is_widget_visible(self, w):
        return self.rendered_seq == w.last_render_seq

    def render(self):
        for row in self.rows:
            xpos = 0
            for (x, text, attrs) in sorted(row, key=lambda x: x[0]):
                if xpos != x:
                    AnsiScreen.advance(x - xpos)
                    xpos = x
                self.set_attrs(*attrs)
                AnsiScreen.write(text)
                self.reset_attrs()
                xpos += len(text)
            AnsiScreen.write('\n')
        self.rendered_seq = self.seq
        self.seq += 1

#scr = AnsiScreen(0, 0)
#scr.set_attrs(AnsiColor.YELLOW, AnsiColor.DEFAULT, AnsiFormat.BOLD)
#print("Hello World!")
#scr.reset_attrs()
#print("Hello again!")
#
#scr2 = AnsiScreen(3, 10)
#scr2.put(0, 2, 'ahoj', ['red-text'])
#scr2.put(0, 5, 'nazdar', [])
#scr2.put(2, 7, 'zcau', ['red-text', 'focused'])
#scr2.render()
