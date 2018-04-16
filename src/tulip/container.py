import tulip

class Container(tulip.Widget):
    def __init__(self, children = []):
        super().__init__()
        self._children = []
        for child in children:
            self.add_child(child)
        self._focused_child = None
        self.last_render_visible = set()

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
        visible = set()
        for widget in widgets:
            widget_rows, widget_cols = widget.render(screen, y, x, i, j, rows, cols - total_cols)
            visible.add(widget)
            j = 0
            x += widget_cols
            total_cols += widget_cols
            max_rows = max(max_rows, widget_rows)
            if total_cols >= cols:
                break

        for widget in self.last_render_visible - visible:
            widget.visible = False
        for widget in visible - self.last_render_visible:
            widget.visible = True
        self.last_render_visible = visible
        print("===")

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
