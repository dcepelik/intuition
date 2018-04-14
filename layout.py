from math import inf
from enum import Enum

INDENT_SIZE = 4

def print_indented(string, indent):
    print("{}{}".format(' ' * INDENT_SIZE * indent, string))

def swap_axes(yx):
    y, x = yx
    return (x, y)

def transpose_widget(widget_class):
    class TransposedWidgetClass(widget_class):
        @property
        def children(self):
            return [child.transpose() for child in super().children]

        def render(self, screen, y, x, i, j, rows, cols):
            return swap_axes(super().render(screen, x, y, j, i, cols, rows))

        @property
        def size(self):
            return swap_axes(super().size)

    return TransposedWidgetClass

class Widget:
    def __init__(self):
        self.parent = None

    def transpose(self):
        return TransposedWrapper(self)

    def render(self, screen, y, x, i, j, rows, cols):
        raise NotImplementedError('{} must implement the render() method'.format(
            self.__class__.__name__))

    def print_tree(self, indent = 0):
        print_indented("Widget `{} (size={})'".format(
            self.__class__.__name__, self.size if hasattr(self, 'size') else '?'), indent)

    def successor(self):
        widget = self
        while widget.parent != None:
            sibling_idx = widget.parent.children.index(widget) + 1
            if sibling_idx < len(widget.parent.children):
                return widget.parent.children[sibling_idx]
            else:
                widget = widget.parent
        return None

class Wrapper(Widget):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def transpose(self):
        return TransposedWrapper(self)

    @property 
    def children(self):
        return self.widget.children

    def render(self, screen, y, x, i, j, rows, cols):
        return self.widget.render(screen, y, x, i, j, rows, cols)

    @property
    def size(self):
        return self.widget.size

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
        return '\n'.join(self.rows) + '\n'

    def __repr__(self):
        return self.content

class Container(Widget):
    def __init__(self, children = None):
        super().__init__()
        self._children = children or []
        for child in self._children:
            child.parent = self

    @property
    def children(self):
        return self._children

    def add_child(self, child):
        self._children.append(child)
        child.parent = self

    def print_tree(self, indent = 0):
        super().print_tree(indent)
        for child in self.children:
            child.print_tree(indent + 1)

    def successor(self):
        return self.children[0]

import itertools

class HContainer(Container):
    """Renders widgets horizontally from left to right.
    """

    def render(self, screen, y, x, i, j, rows, cols):
        children = iter(self.children)
        for child in children:
            child_rows, child_cols = child.size
            if child_cols > j:
                children = itertools.chain([child], children)
                break
            j -= child_cols # TODO don't override `j'
            assert j >= 0

        max_rows = 0
        total_cols = 0
        for child in children:
            child_rows, child_cols = child.render(screen, y, x, i, j, rows, cols - total_cols)
            j = 0
            x += child_cols
            total_cols += child_cols
            max_rows = max(max_rows, child_rows)
            if total_cols >= cols:
                break

        return (max_rows, total_cols)

    @property
    def size(self):
        total_cols = 0
        max_rows = 0
        for child in self.children:
            child_rows, child_cols = child.size
            total_cols += child_cols
            max_rows = max(max_rows, child_rows)
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
        if not isinstance(self.parent, ColumnLayout):
            #raise ValueError('{} must be instance of ColumnLayout'.format(self.__class__.__name__))
            pass
        return self.parent

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
        super().print_tree(indent)
        self.widget.print_tree(indent + 1)

class Row(CellGroup, HContainer):
    def __init__(self, children = None):
        super().__init__(children or [])

    @property
    def children(self):
        return [HViewport(child, self.layout.cells[idx].width) for idx, child in enumerate(super().children)]

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
            for idx, content in enumerate(child.children):
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

class Pager(Widget):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget
        self.vscroll = 0
        self.hscroll = 0

    def render(self, screen, y, x, i, j, rows, cols):
        return self.widget.render(screen, y, x, i + self.vscroll, j + self.hscroll, rows, cols)

    @property
    def size(self):
        return self.widget.size
