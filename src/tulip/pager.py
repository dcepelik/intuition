import tulip
import math

class Pager(tulip.VContainer):
    def __init__(self, children):
        super().__init__(children)
        self.vscroll = 0

    def _render(self, screen, y, x, i, j, rows, cols):
        return super()._render(screen, y, x, i + self.vscroll, j, rows, cols)

    def next_page(self):
        rows, _ = self.size
        self.vscroll = max(0, min(self.vscroll + self.rendered_size[0], rows - self.rendered_size[0]))

    def prev_page(self):
        self.vscroll = max(self.vscroll - self.rendered_size[0], 0)

    def scroll_to_widget(self, w):
        self.vscroll = w.offset_to(self)[0]

    def num_pages(self):
        if self.rendered_size[0]:
            return math.ceil(self.size[0] / self.rendered_size[0])
        return 0

    def page(self):
        if self.rendered_size[0]:
            return 1 + int(self.vscroll / self.rendered_size[0])
        return 0
