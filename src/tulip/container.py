import tulip

class Container(tulip.Widget):
    def __init__(self, children = []):
        super().__init__()
        for child in children:
            self.add_child(child)

    @property
    def rendered_widgets(self):
        return self._children

    def add_child(self, child):
        self._children.append(child)
        child.parent = self
        self.invalidate()

    def clear_children(self):
        self._children.clear()
        self.invalidate()

    def invalidate(self):
        super().invalidate()
        if self.parent:
            self.parent.invalidate()

    def _render_generic(self, screen, y, x, i, j, rows, cols, a, b):
        """Renders widgets either horizontally or vertically (depending on a and b).
        """

        yx = [y, x]
        ij = [i, j]
        rows_cols = [rows, cols]
        self.visible_start = 0

        # skip widgets which are out of the visible area
        for widget in self.rendered_widgets:
            if widget.size[b] > ij[b]:
                break
            self.visible_start += 1
            ij[b] -= widget.size[b]
            assert ij[b] >= 0

        screen.layer += 1
        # render widgets which fall into the visible area, calculate total size
        total_size = [0, 0]
        self.visible_stop = self.visible_start
        for widget in self.rendered_widgets[self.visible_start:]:
            rsize = widget.render(screen, *yx, *ij, *rows_cols)
            self.visible_stop += 1
            yx[b] += rsize[b]
            ij[b] = 0
            total_size[a] = max(total_size[a], rsize[a])
            total_size[b] += rsize[b]
            rows_cols[b] -= rsize[b]
            if rows_cols[b] <= 0:
                break
        screen.layer -= 1

        screen.draw_rectangle(y, x, total_size[0], total_size[1], self.resulting_classes)
        return tuple(total_size)

    def _measure_generic(self, a, b):
        """Returns size when rendered horizontally or vertically (depending on a and b).
        """

        total_size = [0, 0]
        for widget in self.rendered_widgets:
            size = widget.size
            total_size[a] = max(total_size[a], size[a])
            total_size[b] += size[b]
        return tuple(total_size)

    def _child_offset_generic(self, w, b):
        o = [0, 0]
        for c in self._children:
            if c == w:
                break
            o[b] += c.size[b]
        return tuple(o)

    def child_index(self, w):
        return self._children.index(w)

class HContainer(Container):
    """Renders widgets horizontally from left to right.
    """

    def _render(self, screen, y, x, i, j, rows, cols):
        return super()._render_generic(screen, y, x, i, j, rows, cols, 0, 1)

    def _measure(self):
        return super()._measure_generic(0, 1)

    def child_offset(self, w):
        return self._child_offset_generic(w, 1)

class VContainer(Container):
    """Renders widgets vertically from top to bottom.
    """
    
    def _render(self, screen, y, x, i, j, rows, cols):
        return super()._render_generic(screen, y, x, i, j, rows, cols, 1, 0)

    def _measure(self):
        return super()._measure_generic(1, 0)

    def child_offset(self, w):
        return self._child_offset_generic(w, 0)
