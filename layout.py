from math import inf
from enum import Enum

INDENT_SIZE = 2

def print_indented(string, indent):
    print("{}{}".format(' ' * INDENT_SIZE * indent, string))

def swap_axes(yx):
    y, x = yx
    return (x, y)

def transpose_widget(widget_class):
    class TransposedWidgetClass(widget_class):
        @property
        def rendered_widgets(self):
            return [child.transpose() for child in super().rendered_widgets]

        def render(self, screen, y, x, i, j, rows, cols):
            return swap_axes(super().render(screen, x, y, j, i, cols, rows))

        @property
        def size(self):
            return swap_axes(super().size)

    return TransposedWidgetClass

class Widget:
    def __init__(self):
        self.parent = None
        self.focusable = False

    def transpose(self):
        return TransposedWrapper(self)

    def render(self, screen, y, x, i, j, rows, cols):
        raise NotImplementedError('{} must implement the render() method'.format(
            self.__class__.__name__))

    def print_tree(self, indent = 0):
        print_indented("{} (size={})".format(
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
        raise RuntimeError("Requested predecessor of type {} not found".format(typ))

class Wrapper(Widget):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def transpose(self):
        return TransposedWrapper(self)

    @property 
    def rendered_widgets(self):
        return self.widget.rendered_widgets

    def render(self, screen, y, x, i, j, rows, cols):
        return self.widget.render(screen, y, x, i, j, rows, cols)

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

class TransposedWrapper(transpose_widget(Wrapper)):
    pass

class Text(Widget):
    def __init__(self, text):
        super().__init__()
        self.text = text

    @property
    def size(self):
        return (1, len(self.text)) if self.text else (0, 0)

    def render(self, screen, y, x, i, j, rows, cols):
        end = j + cols
        text = '' if i > 0 or rows == 0 else self.text[j:end]
        screen.put(y, x, text)
        cols = len(text)
        rows = 1 if cols else 0
        return (rows, cols)

    def print_tree(self, indent = 0):
        print_indented("Text ('{}')".format(self.text), indent)

class MockScreen:
    def __init__(self, nrows, ncols):
        self.nrows = nrows
        self.ncols = ncols
        self.rows = None
        self.clear()

    def clear(self):
        self.rows = [''] * self.nrows

    def put(self, y, x, text):
        if y < 0 or y >= self.nrows or x < 0 or x >= self.ncols:
            raise RuntimeError('attempted to put a string off the screen')
        self.rows[y] = self.rows[y][0:x].ljust(x) + text + self.rows[y][x:]

    @property
    def content(self):
        return '\n'.join(self.rows)

    def __repr__(self):
        return self.content

class Container(Widget):
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

    def render(self, screen, y, x, i, j, rows, cols):
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

class VContainer(transpose_widget(HContainer)):
    """Renders widgets vertically from top to bottom.
    """
    pass

class NewVContainer(Container):
    pass

class HAlign(Enum):
    LEFT = 1
    CENTER = 2
    RIGHT = 3

class VAlign(Enum):
    TOP = 1
    MIDDLE = 2
    BOTTOM = 3

class Cell:
    def __init__(self, weight=0, halign=HAlign.LEFT, min_width=0, max_width=inf,
        valign=VAlign.TOP, min_height=0, max_height=inf):
        self.weight = weight
        self.halign = halign
        self.min_width = min_width
        self.max_width = max_width
        self.valign = valign
        self.min_height = min_height
        self.max_height = max_height
        self.width = None
        self.height = None
        if min_width > max_width:
            raise ValueError('min_width must be less than or equal to max_width')
        if min_height > max_height:
            raise ValueError('min_height must be less than or equal to max_height')

    def transpose(self):
        return TransposedCell(self)

class TransposedCell:
    def __init__(self, cell):
        self.__dict__['cell'] = cell

    def transpose(self):
        return self.cell

    def transposed_attr_name(name):
        lookup = {
            'halign': 'valign',
            'min_width': 'min_height',
            'max_width': 'max_height',
            'valign': 'halign',
            'min_height': 'min_width',
            'max_height': 'max_width',
            'width': 'height',
            'height': 'width',
        }
        return lookup.get(name, name)

    def __hasattr__(self, name):
        return hasattr(self.cell, TransposedCell.transposed_attr_name(name))

    def __getattr__(self, name):
        return getattr(self.cell, TransposedCell.transposed_attr_name(name))

    def __setattr__(self, name, value):
        return setattr(self.cell, TransposedCell.transposed_attr_name(name), value)
        

class CellGroup:
    @property
    def layout(self):
        return self.lookup(Layout)

class HViewport(Widget):
    def __init__(self, widget, cols):
        super().__init__()
        self.widget = widget
        self.cols = cols

    def transpose(self):
        return HViewport(self.widget.transpose(), self.cols)

    @property
    def size(self):
        widget_rows, widget_cols = self.widget.size
        return (widget_rows, self.cols or widget_cols) # TODO or: a bit of a hack

    def render(self, screen, y, x, i, j, rows, cols):
        widget_rows, widget_cols = self.widget.render(screen, y, x, i, j, rows, self.cols)
        return (widget_rows, self.cols)

    def print_tree(self, indent = 0):
        self.widget.print_tree(indent)

class VViewport(transpose_widget(HViewport)):
    pass

class Row(CellGroup, HContainer):
    def __init__(self, children = None):
        super().__init__(children or [])

    @property
    def rendered_widgets(self):
        return [HViewport(widget, self.layout.cells[idx].width) for idx, widget in enumerate(super().rendered_widgets)]

class Layout:
    def __init__(self):
        super().__init__()
        self._cells = []

    @property
    def cells(self):
        return self._cells

    def add_cell(self, cell):
        self._cells.append(cell)

    #def add_child(self, child):
    #    if not isinstance(child, CellGroup):
    #        raise ValueError('child must be instance of CellGroup')
    #    super().add_child(child)

import math

class ColumnLayout(Layout, VContainer):
    def __init__(self):
        super().__init__()

    def find_max_over_columns(self):
        cell_max_cols = [0] * len(self.cells)
        for child in self._children:
            for idx, content in enumerate(child.rendered_widgets):
                _, cell_cols = content.size
                cell_max_cols[idx] = max(cell_max_cols[idx], cell_cols)
        return cell_max_cols

    def calculate_size_of_cells(self, cols):
        cell_max_cols = self.find_max_over_columns()
        cells_total = sum(cell_max_cols)
        for idx, cell in enumerate(self.cells):
            cell.width = 0 if cell.weight > 0 else cell_max_cols[idx]
            cell.width = max(cell.min_width, min(cell.max_width, cell.width))
            cell.width = min(cell.width, cols)
        avail_cols = cols - sum(cell.width for cell in self.cells)
        if avail_cols > 0:
            sum_weight = sum(cell.weight for cell in self.cells)
            for cell in self.cells:
                if cell.weight > 0:
                    cell.width += int(avail_cols * (float(cell.weight) / sum_weight))

    @property
    def size(self):
        cell_max_cols = self.find_max_over_columns()
        cols = sum(cell_max_cols)
        rows = 0
        # TODO Did I mean rendered_widgets?
        for child in self._children:
            child_rows, _ = child.size
            rows += child_rows
        return (rows, cols)

    def render(self, screen, y, x, i, j, rows, cols):
        self.calculate_size_of_cells(cols)
        return super().render(screen, y, x, i, j, rows, cols)

class Column(transpose_widget(Row)):
    pass

class RowLayout(transpose_widget(ColumnLayout)):
    pass

class Pager(VContainer):
    def __init__(self, children):
        super().__init__(children)
        self.vscroll = 0
        self.hscroll = 0
        self.last_render_rows = None

    def render(self, screen, y, x, i, j, rows, cols):
        self.last_render_rows = rows
        return super().render(screen, y, x, i + self.vscroll, j + self.hscroll, rows, cols)

    def next_page(self):
        rows, _ = self.size
        self.vscroll = max(0, min(self.vscroll + self.last_render_rows, rows - 1))

    def prev_page(self):
        self.vscroll = max(self.vscroll - self.last_render_rows, 0)
