import tulip

focusable_p = lambda w: w.focusable

class Widget(tulip.KeypressMixin):
    def __init__(self):
        super().__init__()
        self.parent = None
        self._children = []
        self._focused_child = None
        self.visible_start = 0 # recalc on clear children!
        self.visible_stop = 0
        self.render_args = None
        self.rendered_size = (0, 0)
        self.focusable = False
        self._classes = []
        self._size = None
        self._hidden = False

    def __repr__(self):
        return "{} (size={})".format(self.__class__.__name__, self.size)

    def _measure(self):
        raise NotImplementedError()

    def _render(self, screen, y, x, i, j, rows, cols):
        raise NotImplementedError()

    def print_tree(self, indent = 0):
        tulip.print_indented(self, indent)
        for child in self._children:
            child.print_tree(indent + 1)

    def add_class(self, name):
        self._classes.append(name)
        self.invalidate()
        return self

    def remove_class(self, name):
        self._classes.remove(name)
        self.invalidate()
        return self

    @property
    def resulting_classes(self):
        if not self.parent:
            return self._classes
        return self._classes + self.parent.resulting_classes

    @property
    def hidden(self):
        return self._hidden

    @property
    def hidden_r(self):
        return self._hidden if not self.parent else self._hidden or self.parent.hidden_r

    @hidden.setter
    def hidden(self, h):
        if self._hidden != h:
            self._hidden = h
            self.invalidate()

    def show(self):
        self.hidden = False
        return self

    def hide(self):
        self.hidden = True
        return self

    @property
    def size(self):
        if self._hidden:
            self._size = (0, 0)
        elif not self._size:
            self.on_before_render() # TODO
            self._size = self._measure()
        return self._size

    def invalidate(self):
        self._size = None

    def on_before_render(self):
        pass

    def on_after_render(self):
        pass

    def render(self, screen, y, x, i, j, rows, cols):
        self.render_args = (screen, y, x, i, j, rows, cols)
        if not self._hidden:
            self.on_before_render()
            self.rendered_size = self._render(screen, y, x, i, j, rows, cols)
            self.on_after_render()
        else:
            self.rendered_size = (0, 0)
        return self.rendered_size

    def redraw(self):
        if self.render_args:
            return self.render(*self.render_args)

    def first_leaf(self):
        if self._children:
            return self._children[0].first_leaf()
        return self

    def last_leaf(self):
        if self._children:
            return self._children[-1].last_leaf()
        return self

    def focused_leaf(self):
        if self._focused_child:
            return self._focused_child.focused_leaf()
        return self

    @property
    def visible_children(self):
        v = self._children[self.visible_start:self.visible_stop]
        return list(filter(lambda w: not w.hidden, v))

    def last_visible(self):
        return self.visible_children[-1] if self.visible_children else self

    def sibling(self, d):
        if self.parent:
            s = self.index() + d
            if s >= 0 and s < len(self.parent._children):
                return self.parent._children[s]

    def visible_sibling(self, d):
        if self.parent:
            idx = self.index()
            while True:
                idx += d
                if idx < self.parent.visible_start or idx >= self.parent.visible_stop:
                    break
                s = self.parent._children[idx]
                if not s:
                    break
                if not s.hidden:
                    return s

    def next(self):
        if self._children:
            return self._children[0]
        w = self
        while w:
            s = w.sibling(1)
            if s:
                return s
            w = w.parent

    def prev(self):
        s = self.sibling(-1)
        if s:
            return s.last_leaf()
        return self.parent

    def next_visible(self):
        if self.visible_children:
            return self.visible_children[0]
        w = self
        while w:
            s = w.visible_sibling(1)
            if s:
                return s
            w = w.parent

    def prev_visible(self):
        s = self.visible_sibling(-1)
        if s:
            return s.last_visible()
        return self.parent

    def _make_walk_p(f):
        def g(self, p):
            w = self
            while w:
                w = f(w)
                if w and p(w):
                    return w
        return g

    next_p = _make_walk_p(next)
    prev_p = _make_walk_p(prev)
    next_visible_p = _make_walk_p(next_visible)
    prev_visible_p = _make_walk_p(prev_visible)

    def next_focusable(self):
        return self.next_p(focusable_p)

    def prev_focusable(self):
        return self.prev_p(focusable_p)

    def first_focusable(self):
        if self.focusable:
            return self
        return self.next_focusable()

    def last_focusable(self):
        l = self.last_leaf()
        if not l:
            return None
        if l.focusable:
            return l
        return l.prev_focusable()

    def lookup(self, cls):
        if isinstance(self, cls):
            return self
        if self.parent:
            return self.parent.lookup(cls)
        raise RuntimeError("Required {} predecessor not found".format(cls))

    def focus(self):
        w = self
        got_focus = []
        lost_focus = []
        while w.parent:
            got_focus.append(w)
            if w.parent._focused_child != w:
                while got_focus:
                    got_focus.pop().on_got_focus()
                lost_focus.clear()
                s = w.parent._focused_child
                while s:
                    lost_focus.append(s)
                    s = s._focused_child
                w.parent._focused_child = w
            w = w.parent
        while lost_focus:
            lost_focus.pop().on_lost_focus()
        w = self._focused_child
        while w:
            w.on_got_focus()
            w = w._focused_child

    def subtree(self):
        yield self
        for c in self._children:
            yield from c.subtree()

    def srch(self, cls, once_per_subtree=False):
        if isinstance(self, cls):
            yield self
            if once_per_subtree:
                return
        for w in self._children:
            yield from w.srch(cls, once_per_subtree)

    def on_got_focus(self):
        self.add_class('focus-path')
        if not self._focused_child and 'focused' not in self._classes:
            self.add_class('focused')

    def on_lost_focus(self):
        self.remove_class('focus-path')
        if 'focused' in self._classes:
            self.remove_class('focused')

    @property
    def is_focused(self):
        return not self.parent or (self.parent._focused_child == self and self.parent.is_focused)

    def is_visible(self):
        if self.hidden_r:
            return False
        if not self.render_args:
            return False
        if not self.parent:
            return True
        i = self.index()
        if i >= self.parent.visible_start and i < self.parent.visible_stop:
            return self.parent.is_visible() if self.parent else True
        return False

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

class Air(Widget):
    def __init__(self, rows, cols):
        super().__init__()
        self.rows = rows
        self.cols = cols

    def _render(self, screen, y, x, i, j, rows, cols):
        return (self.rows, self.cols)

    def _measure(self):
        return (self.rows, self.cols)

class Empty(Air):
    def __init__(self):
        super().__init__(0, 0)
