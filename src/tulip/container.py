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

    def _render(self, screen, yx, ij, rows_cols, a, b):
        rstart = 0
        for idx, widget in enumerate(self.rendered_widgets):
            size = widget.size
            if size[b] > ij[b]:
                rstart = idx
                break
            ij[b] -= size[b]
            assert ij[b] >= 0

        total_size = [0, 0]
        for widget in self.rendered_widgets[rstart:]:
            size = widget.render(screen, yx[0], yx[1], ij[0], ij[1], rows_cols[0], rows_cols[1])
            yx[b] += size[b]
            ij[b] = 0
            total_size[a] = max(total_size[a], size[a])
            total_size[b] += size[b]
            rows_cols[b] -= size[b]
            if rows_cols[b] <= 0:
                break
        return (total_size[0], total_size[1])

    def _size(self, a, b):
        total_size = [0, 0]
        for widget in self.rendered_widgets:
            size = widget.size
            total_size[a] = max(total_size[a], size[a])
            total_size[b] += size[b]
        return (total_size[0], total_size[1])

class HContainer(Container):
    """Renders widgets horizontally from left to right.
    """

    def _render(self, screen, y, x, i, j, rows, cols):
        return super()._render(screen, [y, x], [i, j], [rows, cols], 0, 1)

    @property
    def size(self):
        return super()._size(0, 1)

class VContainer(Container):
    """Renders widgets vertically from top to bottom.
    """
    
    def _render(self, screen, y, x, i, j, rows, cols):
        return super()._render(screen, [y, x], [i, j], [rows, cols], 1, 0)

    @property
    def size(self):
        return super()._size(1, 0)
