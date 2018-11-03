import tulip

class Widget(tulip.KeypressMixin):
    def __init__(self):
        super().__init__()
        self.parent = None
        self.focusable = False
        self.last_render_y = None
        self.last_render_x = None
        self.last_render_rows = None
        self.last_render_cols = None
        self.last_render_seq = 0
        self.classes = []
        self._size = None

    @property
    def resulting_classes(self):
        if not self.parent:
            cls = self.classes
        else:
            cls = self.classes + self.parent.resulting_classes
        focused = []
        if self.is_focused and not self.focused_child:
            focused.append('focused')
        return cls + focused

    def add_class(self, name):
        self.classes.append(name)

    def remove_class(self, name):
        self.classes.remove(name)

    def toggle_class(self, name):
        if name in self.classes:
            self.remove_class(name)
        else:
            self.add_class(name)

    @property
    def size(self):
        if not self._size:
            self._size = self._measure()
        return self._size

    def render(self, screen, y, x, i, j, rows, cols):
        self.last_render_y = y
        self.last_render_x = x
        self.last_render_rows = rows
        self.last_render_cols = cols
        self.last_render_seq = screen.seq
        return self._render(screen, y, x, i, j, rows, cols)

    def invalidate(self):
        self._size = None

    def _measure(self):
        raise NotImlementedError('Class does not implement the _measure method')

    def _render(self, screen, y, x, i, j, rows, cols):
        raise NotImplementedError('Class does not implement the _render method')

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

    def find_predecessor(self):
        widget = self
        while widget.parent != None:
            sibling_idx = widget.parent._children.index(widget) - 1
            if sibling_idx >= 0:
                return widget.parent._children[sibling_idx]
            else:
                widget = widget.parent
        return None

    def find_focusable_successor(self):
        succ = self.find_successor()
        while succ and not succ.focusable:
            succ = succ.find_successor()
        return succ

    def find_focusable_predecessor(self):
        pred = self.find_predecessor()
        while pred and not pred.focusable:
            pred = pred.find_predecessor()
        return pred

    @property
    def focused_child(self):
        return None

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

    def find_last_leaf(self):
        return self

    def lookup(self, typ):
        if isinstance(self, typ):
            return self
        if self.parent:
            return self.parent.lookup(typ)
        raise RuntimeError("Required predecessor of type {} not found".format(typ))

class Box(Widget):
    def __init__(self, rows, cols):
        super().__init__()
        self.rows = rows
        self.cols = cols

    def _render(self, screen, y, x, i, j, rows, cols):
        return (self.rows, self.cols)

    def _measure(self):
        return (self.rows, self.cols)
