import tulip

class Widget(tulip.KeypressMixin):
    def __init__(self):
        super().__init__()
        self.parent = None
        self.focusable = False
        self.last_render_screen = None
        self.last_render_y = None
        self.last_render_x = None
        self.last_render_i = None
        self.last_render_j = None
        self.last_render_rows = None
        self.last_render_cols = None
        self.last_render_l = 0
        self.last_render_r = 0
        self.classes = []
        self._size = None
        self.focused_child = None
        self._hidden = False

    def __repr__(self):
        return "{} (size={})".format(self.__class__.__name__, self.size if hasattr(self, 'size') else '?')

    def print_tree(self, indent = 0):
        tulip.print_indented(self, indent)

    @property
    def resulting_classes(self):
        if not self.parent:
            return self.classes
        return self.classes + self.parent.resulting_classes

    def add_class(self, name):
        self.classes.append(name)
        return self

    def remove_class(self, name):
        self.classes.remove(name)
        return self

    @property
    def hidden(self):
        return self._hidden

    @hidden.setter
    def hidden(self, h):
        if self._hidden != h:
            self._hidden = h
            self.invalidate()

    def hide(self):
        self.hidden = True

    def show(self):
        self.hidden = False

    @property
    def size(self):
        if self._hidden:
            return (0, 0)
        if not self._size:
            self.before_render() # TODO
            self._size = self._measure()
        return self._size

    def invalidate(self):
        self._size = None

    def before_render(self):
        pass

    def after_render(self):
        pass

    def render(self, screen, y, x, i, j, rows, cols):
        if self._hidden:
            return (0, 0)
        self.before_render()
        self.last_render_screen = screen
        self.last_render_y = y
        self.last_render_x = x
        self.last_render_i = i
        self.last_render_j = j
        self.last_render_rows = rows
        self.last_render_cols = cols
        r = self._render(screen, y, x, i, j, rows, cols)
        self.after_render()
        return r

    def redraw(self):
        if self.last_render_screen:
            return self.render(self.last_render_screen,
                self.last_render_y,
                self.last_render_x,
                self.last_render_i,
                self.last_render_j,
                self.last_render_rows,
                self.last_render_cols)

    def _measure(self):
        raise NotImlementedError('Class does not implement the _measure method')

    def _render(self, screen, y, x, i, j, rows, cols):
        raise NotImplementedError('Class does not implement the _render method')

    def _nlr_walk_range(self, d, l, r):
        w = self
        while w.parent != None:
            s = w.index() + d
            if s >= l(w.parent) and s <= r(w.parent):
                return w.parent._children[s]
            else:
                w = w.parent
        return None

    def _nlr_walk(self, d):
        return self._nlr_walk_range(d, lambda w: 0, lambda w: len(w._children) - 1)

    def _nlr_walk_visible(self, d):
        return self._nlr_walk_range(d, lambda w: w.last_render_l, lambda w: w.last_render_r - 1)

    def _nlr_walk_focusable(self, d):
        w = self
        while True:
            w = w._nlr_walk(d)
            if not w or w.focusable:
                break
        return w

    def nlr_next(self):
        return self._nlr_walk(1)

    def nlr_next_visible(self):
        return self._nlr_walk_visible(1)

    def nlr_prev(self):
        return self._nlr_walk(-1)

    def nlr_prev_visible(self):
        return self._nlr_walk_visible(-1)

    def nlr_next_focusable(self):
        return self._nlr_walk_focusable(1)

    def nlr_prev_focusable(self):
        return self._nlr_walk_focusable(-1)

    def nlr_first_focusable(self):
        if self.focusable:
            return self
        return self.nlr_next_focusable()

    def nlr_last_focusable(self):
        l = self.find_last_leaf()
        if not l:
            return None # TODO Why this happens?
        if l.focusable:
            return l
        return l.nlr_prev_focusable()

    def focus(self):
        w = self
        got_focus = []
        lost_focus = []
        while w.parent:
            got_focus.append(w)
            if w.parent.focused_child != w:
                while got_focus:
                    g = got_focus.pop()
                    g.on_got_focus()
                    g.on_focus_changed()
                lost_focus.clear()
                s = w.parent.focused_child
                while s:
                    lost_focus.append(s)
                    s = s.focused_child
                w.parent.focused_child = w
            w = w.parent
        while lost_focus:
            lost_focus.pop().on_lost_focus()
        while got_focus:
            got_focus.pop().on_focus_changed()

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

    def is_visible(self):
        if not self.parent:
            return True
        i = self.index()
        if i >= self.parent.last_render_l and i < self.parent.last_render_r:
            return True
        return False

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

    def offset_to(self, p):
        w = self
        o = [0, 0]
        while w.parent and w != p:
            r, c = w.parent.child_offset(w)
            o[0] += r
            o[1] += c
            w = w.parent
        return tuple(o)

    def index(self):
        if self.parent:
            return self.parent.child_index(self)
        return None

class Box(Widget):
    def __init__(self, rows, cols):
        super().__init__()
        self.rows = rows
        self.cols = cols

    def _render(self, screen, y, x, i, j, rows, cols):
        return (self.rows, self.cols)

    def _measure(self):
        return (self.rows, self.cols)
