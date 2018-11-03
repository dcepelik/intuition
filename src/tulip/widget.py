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
        self.focused_child = None

    @property
    def resulting_classes(self):
        if not self.parent:
            return self.classes
        return self.classes + self.parent.resulting_classes

    def add_class(self, name):
        self.classes.append(name)

    def remove_class(self, name):
        self.classes.remove(name)

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
        w = self
        while w.parent != None:
            s = w.parent._children.index(w) + 1
            if s < len(w.parent._children):
                return w.parent._children[s]
            else:
                w = w.parent
        return None

    def find_predecessor(self):
        w = self
        while w.parent != None:
            s = w.parent._children.index(w) - 1
            if s >= 0:
                return w.parent._children[s]
            else:
                w = w.parent
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

    def focus(self):
        w = self
        got_focus = []
        lost_focus = []
        while w.parent:
            got_focus.append(w)
            if w.parent.focused_child != w:
                while got_focus:
                    got_focus.pop().on_got_focus()
                lost_focus.clear()
                s = w.parent.focused_child
                while s:
                    lost_focus.append(s)
                    s = s.focused_child
                w.parent.focused_child = w
            w = w.parent
        while lost_focus:
            lost_focus.pop().on_lost_focus()

    def on_got_focus(self):
        self.add_class('focus-path')
        if not self.focused_child:
            self.add_class('focused')

    def on_lost_focus(self):
        self.remove_class('focus-path')
        if 'focused' in self.classes:
            self.classes.remove('focused')

    def on_focus_changed(self):
        pass

    @property
    def is_focused(self):
        return not self.parent or (self.parent.focused_child == self and self.parent.is_focused)

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
