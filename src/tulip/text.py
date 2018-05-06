import tulip

class Text(tulip.Widget):
    def __init__(self, text):
        super().__init__()
        self.text = text

    @property
    def size(self):
        return (1, len(self.text)) if self.text else (0, 0)

    def _render(self, screen, y, x, i, j, rows, cols):
        end = j + cols
        text = '' if i > 0 or rows == 0 else self.text[j:end]
        screen.put(y, x, text, [])
        cols = len(text)
        rows = 1 if cols else 0
        return (cols, rows) if isinstance(screen, tulip.SwappedAxesScreen) else (rows, cols) # TODO

    def print_tree(self, indent = 0):
        tulip.print_indented("Text ('{}')".format(self.text), indent)
