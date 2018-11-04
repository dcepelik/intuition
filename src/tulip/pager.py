import tulip

class Pager(tulip.VContainer):
    def __init__(self, children):
        super().__init__(children)
        self.vscroll = 0
        self.follow_focus = True

    def _render(self, screen, y, x, i, j, rows, cols):
        if self.follow_focus:
            f = self.find_focused_leaf()
            if f and not screen.is_widget_visible(f):
                self.scroll_to_widget(f)
        return super()._render(screen, y, x, i + self.vscroll, j, rows, cols)

    def next_page(self):
        rows, _ = self.size
        self.vscroll = max(0, min(self.vscroll + self.last_render_rows, rows - 1))

    def prev_page(self):
        self.vscroll = max(self.vscroll - self.last_render_rows, 0)

    def scroll_to_widget(self, w):
        self.vscroll = w.offset_to(self)[0]
