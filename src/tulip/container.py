import tulip

class Container(tulip.Widget):
    def __init__(self, children = []):
        super().__init__()
        self._children = []
        for child in children:
            self.add_child(child)
        self._focused_child = None
        self.visible_widgets = set()

    @property
    def rendered_widgets(self):
        return self._children

    @property
    def focused_child(self):
        return self._focused_child

    @focused_child.setter
    def focused_child(self, new):
        if self._focused_child:
            self._focused_child.handle_focus_changed(False)
        new.handle_focus_changed(True)
        self._focused_child = new

    def add_child(self, child):
        self._children.append(child)
        child.parent = self

    def print_tree(self, indent = 0):
        super().print_tree(indent)
        for child in self._children:
            child.print_tree(indent + 1)

    def find_successor(self):
        return self._children[0]

    def find_focused_leaf(self):
        if self.focused_child:
            return self.focused_child.find_focused_leaf()
        return self

    def find_first_leaf(self):
        if len(self._children):
            return self._children[0].find_first_leaf()
        return None

    def _render_generic(self, screen, y, x, i, j, rows, cols, a, b):
        """Renders widgets either horizontally or vertically (depending on a and b).
        """

        yx = [y, x]
        ij = [i, j]
        rows_cols = [rows, cols]
        rstart = 0

        # skip widgets which are out of the visible area
        for idx, widget in enumerate(self.rendered_widgets):
            if widget.size[b] > ij[b]:
                rstart = idx
                break
            ij[b] -= widget.size[b]
            assert ij[b] > 0

        # render widgets which fall into the visible area (idx >= rstart), calculate total size
        total_size = [0, 0]
        for widget in self.rendered_widgets[rstart:]:
            rsize = widget.render(screen, *yx, *ij, *rows_cols)
            yx[b] += rsize[b]
            ij[b] = 0
            total_size[a] = max(total_size[a], rsize[a])
            total_size[b] += rsize[b]
            rows_cols[b] -= rsize[b]
            if rows_cols[b] <= 0:
                break
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

class HContainer(Container):
    """Renders widgets horizontally from left to right.
    """

    def _render(self, screen, y, x, i, j, rows, cols):
        return super()._render_generic(screen, y, x, i, j, rows, cols, 0, 1)

    @property
    def size(self):
        return super()._measure_generic(0, 1)

class VContainer(Container):
    """Renders widgets vertically from top to bottom.
    """
    
    def _render(self, screen, y, x, i, j, rows, cols):
        return super()._render_generic(screen, y, x, i, j, rows, cols, 1, 0)

    @property
    def size(self):
        return super()._measure_generic(1, 0)
