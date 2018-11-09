class Screen:
    def __init__(self):
        pass

class MockScreen(Screen):
    def __init__(self, nrows, ncols):
        super().__init__()
        self.nrows = nrows
        self.ncols = ncols
        self.rows = None
        self.clear()
        self.layer = 0

    def clear(self):
        self.rows = [''] * self.nrows

    def put(self, y, x, text, classes):
        if y < 0 or y >= self.nrows or x < 0 or x >= self.ncols:
            raise RuntimeError('attempted to put a string off the screen')
        self.rows[y] = self.rows[y][0:x].ljust(x) + text + self.rows[y][x:]

    def draw_rectangle(self, y0, x, rows, cols, classes):
        pass

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

class ColorName(IntEnum):
    BLACK = 0
    RED = 1
    GREEN = 2
    YELLOW = 3
    BLUE = 4
    MAGENTA = 5
    CYAN = 6
    LIGHT_GRAY = 7
    DARK_GRAY = 8
    LIGHT_RED = 9
    LIGHT_GREEN = 10
    LIGHT_YELLOW = 11
    LIGHT_BLUE = 12
    LIGHT_MAGENTA = 13
    LIGHT_CYAN = 14
    WHITE = 15

class Color:
    def setfg(self):
        self._set(True)

    def setbg(self):
        self._set(False)

class Ansi256(Color):
    def __init__(self, n):
        self.n = n

    def __repr__(self):
        return "Ansi256({})".format(self.n)

    def _set(self, fg):
        AnsiScreen.write_attr("{};5;{}".format(38 if fg else 48, self.n))

class TrueColor(Color):
    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b

    def __repr__(self):
        return "TrueColor({}, {}, {})".format(self.r, self.g, self.b)

    def _set(self, fg):
        AnsiScreen.write_attr("{};2;{};{};{}".format(38 if fg else 48, self.r, self.g, self.b))

class Theme:
    def __init__(self):
        self.classes = {}

    def set_class(self, name, fg = None, bg = None, fmt = None):
        self.classes[name] = (fg, bg, fmt)

    def get_style(self, classes):
        fg, bg, fmt = None, None, None
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
        self.layer = 16 
        self.theme = Theme()
        self.theme.set_class('error', fg = Ansi256(ColorName.RED), fmt = AnsiFormat.BOLD)
        self.theme.set_class('focused', fmt = AnsiFormat.BOLD)
        self.theme.set_class('qgroup', fg = Ansi256(ColorName.YELLOW))
        self.theme.set_class('qgroup-2', fg = Ansi256(ColorName.RED))
        self.theme.set_class('check', fg = Ansi256(ColorName.YELLOW), fmt = AnsiFormat.BOLD)
        self.theme.set_class('bluebg', bg = Ansi256(ColorName.BLUE), fg = Ansi256(ColorName.BLACK))
        self.theme.set_class('tags', fg = Ansi256(220))
        self.theme.set_class('subject', fg = Ansi256(ColorName.WHITE))
        self.theme.set_class('authors', fg = Ansi256(ColorName.WHITE))
        self.theme.set_class('query', fg = Ansi256(ColorName.WHITE))
        #self.theme.set_class('msg-author', fmt = AnsiFormat.BOLD)
        #self.theme.set_class('msg-author_addr', fg = Ansi256(ColorName.BLACK))
        self.theme.set_class('quote', fg = Ansi256(ColorName.BLUE))
        self.theme.set_class('msg-header', fg = Ansi256(ColorName.BLACK), bg = Ansi256(85))
        self.theme.set_class('msg-headers', fg = Ansi256(ColorName.BLACK), bg = Ansi256(157))
        #self.theme.set_class('header-name')
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
        if fg:
            fg.setfg()
        if bg:
            bg.setbg()
        if fmt:
            AnsiScreen.write_attr(fmt)

    def reset_attrs(self):
        AnsiScreen.write_attr(0)

    def put(self, y, x, text, classes):
        if y < 0 or y >= self.nrows or x < 0 or x >= self.ncols:
            raise RuntimeError('attempted to put a string off the screen')
        self.rows[y].append((x, self.layer, text, self.theme.get_style(classes)))

    def draw_rectangle(self, y0, x, rows, cols, classes):
        for y in range(y0, y0 + rows):
            self.put(y, x, ' ' * cols, classes)

    def render(self):
        #self.write("\033[H\033[J")
        for row in self.rows:
            xpos = 0
            for (x, _, text, attrs) in sorted(row, key=lambda x: (x[1], x[0])):
                #if xpos != x:
                #    AnsiScreen.advance(x - xpos)
                #    xpos = x
                AnsiScreen.write_cmd('[{}G'.format(1 + x))
                self.set_attrs(*attrs)
                AnsiScreen.write(text)
                self.reset_attrs()
                #xpos += len(text)
            AnsiScreen.write('\n')

#scr = AnsiScreen(0, 0)
#scr.set_attrs(Ansi256(ColorName.YELLOW), Ansi256(ColorName.DEFAULT), AnsiFormat.BOLD)
#print("Hello World!")
#scr.reset_attrs()
#print("Hello again!")
#
#scr2 = AnsiScreen(3, 10)
#scr2.put(0, 2, 'ahoj', ['red-text'])
#scr2.put(0, 5, 'nazdar', [])
#scr2.put(2, 7, 'zcau', ['red-text', 'focused'])
#scr2.render()
