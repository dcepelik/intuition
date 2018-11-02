import tulip

class Text(tulip.Widget):
    def __init__(self, text, classes=None):
        super().__init__()
        self.text = text
        if classes:
            for c in classes:
                self.add_class(c)

    @property
    def size(self):
        return (1, len(self.text)) if self.text else (0, 0)

    def _render(self, screen, y, x, i, j, rows, cols):
        end = j + cols
        text = '' if i > 0 or rows == 0 else self.text[j:end]
        screen.put(y, x, text, self.resulting_classes)
        cols = len(text)
        rows = 1 if cols else 0
        return (rows, cols)

    def print_tree(self, indent = 0):
        tulip.print_indented("Text ('{}')".format(self.text), indent)
