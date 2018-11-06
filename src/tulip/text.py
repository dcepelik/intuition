import tulip

# Clean-up
class Text(tulip.Widget):
    def __init__(self, text='', classes=None):
        super().__init__()
        if text == None:
            raise ValueError("Text cannot be None")
        self._text = text

    def __repr__(self):
        return "Text (size={}, text={})".format(self.size, self.text)

    def _measure(self):
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

    def set_text(self, text):
        if self._text != text:
            self._text = text
            self.invalidate()

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self.set_text(text)

import math

class Paragraph(tulip.VContainer):
    def __init__(self, text):
        self.text = text
        self.reflow(math.inf)

    def reflow(self, max_cols):
        self.lines = []
        for line in self.text.split("\n"):
            if len(line) <= max_cols:
                self.lines.append(line)
            else:
                self.lines.append(line[:max_cols])
                self.lines.append("\u21B3" + line[max_cols:])

    def _render(self, screen, y, x, i, j, rows, cols):
        self.reflow(cols)
        return super()._render(screen, y, x, i, j, rows, cols)

    @property
    def rendered_widgets(self):
        return [Text(line) for line in self.lines]
