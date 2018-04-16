import tulip

class Container(tulip.Widget):
    def __init__(self, children = None):
        super().__init__()
        self._children = children or []
        for child in self._children:
            child.parent = self
        self.focused_child = None

    @property
    def rendered_widgets(self):
        return self._children

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

import itertools

class HContainer(Container):
    """Renders widgets horizontally from left to right.
    """

    def _render(self, screen, y, x, i, j, rows, cols):
        widgets = iter(self.rendered_widgets)
        for widget in widgets:
            widget_rows, widget_cols = widget.size
            if widget_cols > j:
                widgets = itertools.chain([widget], widgets)
                break
            j -= widget_cols # TODO don't override `j'
            assert j >= 0

        max_rows = 0
        total_cols = 0
        for widget in widgets:
            widget_rows, widget_cols = widget.render(screen, y, x, i, j, rows, cols - total_cols)
            j = 0
            x += widget_cols
            total_cols += widget_cols
            max_rows = max(max_rows, widget_rows)
            if total_cols >= cols:
                break

        return (max_rows, total_cols)

    @property
    def size(self):
        total_cols = 0
        max_rows = 0
        for widget in self.rendered_widgets:
            widget_rows, widget_cols = widget.size
            total_cols += widget_cols
            max_rows = max(max_rows, widget_rows)
        return (max_rows, total_cols)

class VContainer(tulip.transpose_widget(HContainer)):
    """Renders widgets vertically from top to bottom.
    """
    pass
