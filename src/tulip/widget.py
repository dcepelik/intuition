import tulip

def swap_axes(yx):
    y, x = yx
    return (x, y)

class Widget(tulip.KeypressMixin):
    def __init__(self):
        super().__init__()
        self.parent = None
        self.focusable = False
        self.last_render_y = None
        self.last_render_x = None
        self.last_render_rows = None
        self.last_render_cols = None
        self.classes = []
        self._visible = False

    @property
    def resulting_classes(self):
        if not self.parent:
            return self.classes
        return self.classes + self.parent.resulting_classes

    def add_class(self, name):
        self.classes.append(name)

    def remove_class(self, name):
        self.classes.remove(name)

    def transpose(self):
        return TransposedWrapper(self)

    def render(self, screen, y, x, i, j, rows, cols):
        self.last_render_y = y
        self.last_render_x = x
        self.last_render_rows = rows
        self.last_render_cols = cols
        return self._render(screen, y, x, i, j, rows, cols)

    def _render(self, screen, y, x, i, j, rows, cols):
        raise NotImplementedError('{} must implement the _render() method'.format(
            self.__class__.__name__))

    # TODO shout when size not defined

    def print_tree(self, indent = 0):
        tulip.print_indented("{} (size={})".format(
            self.__class__.__name__, self.size if hasattr(self, 'size') else '?'), indent)

    def find_successor(self):
        widget = self
        while widget.parent != None:
            sibling_idx = widget.parent._children.index(widget) + 1
            if sibling_idx < len(widget.parent._children):
                return widget.parent._children[sibling_idx]
            else:
                widget = widget.parent
        return None

    def find_focusable_successor(self):
        succ = self.find_successor()
        while succ and not succ.focusable:
            succ = succ.find_successor()
        return succ

    def focus(self):
        if self.parent:
            self.parent.focused_child = self
            self.parent.focus()

    def handle_focus_changed(self, focused):
        pass

    @property
    def is_focused(self):
        if self.parent:
            return self.parent.focused_child == self and self.parent.is_focused
        return True

    def find_focused_leaf(self):
        return self

    def find_first_leaf(self):
        return self

    def lookup(self, typ):
        if isinstance(self, typ):
            return self
        if self.parent:
            return self.parent.lookup(typ)
        raise RuntimeError("Required predecessor of type {} not found".format(typ))

    @property
    def visible(self):
        if not self.parent:
            return self._visible
        return self._visible and self.parent.visible

    @visible.setter
    def visible(self, visible):
        self._visible = visible

class Wrapper:
    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def transpose(self):
        return TransposedWrapper(self)

    @property 
    def rendered_widgets(self):
        return self.widget

    def _render(self, screen, y, x, i, j, rows, cols):
        return self.widget.render(screen, y, x, i, j, rows, cols)

    def render(self, screen, y, x, i, j, rows, cols):
        return self._render(screen, y, x, i, j, rows, cols)

    @property
    def size(self):
        return self.widget.size

    def print_tree(self, indent = 0):
        return self.widget.print_tree(indent)

    @property
    def find_first_leaf(self):
        return self.widget.find_first_leaf

    def find_focused_leaf(self):
        return self.widget.find_focused_leaf()

    def focus(self):
        self.widget.focus()

    @property
    def visible(self):
        return self.widget.visible

    @visible.setter
    def visible(self, visible):
        self.widget.visible = visible

    @property
    def resulting_classes(self):
        return self.widget.resulting_classes

def transpose_widget(widget_class):
    class TransposedWidgetClass(widget_class):
        @property
        def rendered_widgets(self):
            return [child.transpose() for child in super().rendered_widgets]

        def _render(self, screen, y, x, i, j, rows, cols):
            return swap_axes(super()._render(screen, x, y, j, i, cols, rows))

        @property
        def size(self):
            return swap_axes(super().size)

    return TransposedWidgetClass

class TransposedWrapper(transpose_widget(Wrapper)):
    pass
