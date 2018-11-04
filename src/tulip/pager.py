import tulip

class Pager(tulip.VContainer):
    def __init__(self, children):
        super().__init__(children)
        self.vscroll = 0
        self.follow_focus = True
        self.refocus = False

    def _render(self, screen, y, x, i, j, rows, cols):
        f = self.find_focused_leaf()
        if self.refocus:
            self.refocus = False
            super()._render(screen, y, x, i + self.vscroll, j, rows, cols)
            if not f.is_visible():
                n = self.nlr_next_visible()
                while n and not n.focusable:
                    n = n.nlr_next_visible()
                if n:
                    n.focus()
        elif self.follow_focus:
            if f and not f.is_visible():
                self.scroll_to_widget(f)
                self.refocus = False
        return super()._render(screen, y, x, i + self.vscroll, j, rows, cols)

    def next_page(self):
        rows, _ = self.size
        self.refocus = True
        self.vscroll = max(0, min(self.vscroll + self.last_render_rows, rows - 1))

    def prev_page(self):
        self.refocus = True
        self.vscroll = max(self.vscroll - self.last_render_rows, 0)

    def scroll_to_widget(self, w):
        self.refocus = True
        self.vscroll = w.offset_to(self)[0]
