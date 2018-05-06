class Theme:
    pass

class SwappedAxesScreen:
    def __init__(self, screen):
        self.screen = screen

    def put(self, y, x, text, classes):
        self.screen.put(x, y, text, classes)

    def measure(self, widget):
        rows, cols = self.screen.measure(widget)
        return (cols, rows)

class MockScreen:
    def __init__(self, nrows, ncols):
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
