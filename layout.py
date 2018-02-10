#!/usr/bin/env python

from math import inf
from enum import Enum

class Widget:
    def __init__(self):
        self.parent = None

    def transpose(self):
        return TransposedWidget(self)

    def render(self, screen, y, x, i, j, rows, cols):
        raise NotImplementedError('widgets must implement the render() method')

def swap_axes(yx):
    y, x = yx
    return (x, y)

# TODO Rename `Transposed' stuff to something else like XYWidget
class TransposedWidget(Widget):
    def __init__(self, widget):
        self.widget = widget

    def transpose(self):
        return self.widget

    @property
    def size(self):
        return swap_axes(self.widget.size)

    def render(self, screen, y, x, i, j, rows, cols):
        return swap_axes(self.widget.render(screen, x, y, j, i, cols, rows))

class TransposeWidgetMixin:
    @property
    def children(self):
        for child in self._children:
            yield child.transpose()

    def render(self, screen, y, x, i, j, rows, cols):
        return swap_axes(super().render(screen, x, y, j, i, cols, rows))

    @property
    def size(self):
        return swap_axes(super().size)

class Text(Widget):
    def __init__(self, text):
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

class Container(Widget):
    def __init__(self, children = []):
        self._children = children

    @property
    def children(self):
        return self._children

    def add_child(self, child):
        self._children.append(child)
        child.parent = self

class MockScreen():
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

import itertools

'''
Renders widgets horizontally from left to right.
'''
class HContainer(Container):
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

'''
Renders widgets vertically from top to bottom.
'''
class VContainer(TransposeWidgetMixin, HContainer):
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
    def __init__(self, weight=1, halign=HAlign.LEFT, min_width=0, max_width=inf,
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

class CellGroup(Container):
    pass

class HViewport(Widget):
    def __init__(self, widget, cols):
        super().__init__()
        self.widget = widget
        self.cols = cols

    @property
    def size(self):
        widget_rows, _ = self.widget.size
        return (widget_rows, self.cols)

    def render(self, screen, y, x, i, j, rows, cols):
        widget_rows, widget_cols = self.widget.render(screen, y, x, i, j, rows, self.cols)
        return (widget_rows, self.cols)

class Row(CellGroup, HContainer):
    @property
    def layout(self):
        if not isinstance(self.parent, ColumnLayout):
            raise ValueError('Row must be instance of ColumnLayout')
        return self.parent

    @property
    def children(self):
        for idx, child in enumerate(super().children):
            yield HViewport(child, self.layout.cells[idx].width)

class Layout(Container):
    def __init__(self):
        super().__init__()
        self.cells = []

    def add_cell(self, cell):
        self.cells.append(cell)

    def add_child(self, child):
        if not isinstance(child, CellGroup):
            raise ValueError('child must be instance of CellGroup')
        super().add_child(child)

import math

class ColumnLayout(Layout):
    def __init__(self):
        super().__init__()

    def calculate_cells_sizes(self, cols):
        cell_max_cols = [0] * len(self.cells)
        for child in self.children:
            for idx, content in enumerate(child._children): # HACK!
                _, cell_cols = content.size
                cell_max_cols[idx] = max(cell_max_cols[idx], cell_cols)

        cells_total = sum(cell_max_cols)
        for idx, cell in enumerate(self.cells):
            cell.width = math.floor((cell_max_cols[idx] / cells_total) * cols)

    def render(self, screen, y, x, i, j, rows, cols):
        self.calculate_cells_sizes(cols)
        VContainer(self.children).render(screen, y, x, i, j, rows, cols)
        print(screen)

#class VLayout(Layout):
#    def add_child(self, child):
#        if not isinstance(child, VContainer):
#            raise ValueError('child of VLayout must be instance of VContainer')
#        super().add_child(child)
