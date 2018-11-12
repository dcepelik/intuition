import tulip
import math

class Pager(tulip.VContainer):
    def __init__(self, children=[]):
        super().__init__(children)
        self._vscroll = 0

    @property
    def vscroll(self):
        return self._vscroll

    @vscroll.setter
    def vscroll(self, s):
        self._vscroll = self._page_align(s)

    def _render(self, screen, y, x, i, j, rows, cols):
        return super()._render(screen, y, x, i + self.vscroll, j, rows, cols)

    def _avail_rows(self):
        if self.render_args:
            return self.render_args[5]
        return 0

    def _page_align(self, n):
        if self._avail_rows():
            return n - (n % self._avail_rows())
        return 0

    def next_page(self):
        rows, _ = self.size
        self.vscroll = max(0, min(rows - 1, self.vscroll + self._avail_rows()))

    def prev_page(self):
        self.vscroll = max(0, self.vscroll - self._avail_rows())

    def scroll_to_widget(self, w):
        self.vscroll = w.offset_to(self)[0]

    def num_pages(self):
        if self._avail_rows():
            return math.ceil(self.size[0] / self._avail_rows())
        return 0

    def page(self):
        if self._avail_rows():
            return 1 + int(self.vscroll / self._avail_rows())
        return 0
