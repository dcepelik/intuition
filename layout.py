#!/usr/bin/env python

from math import inf
from enum import Enum

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

class Widget:
    def transpose(self):
        return TransposedWidget(self)

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

class Container:
    def __init__(self, children = []):
        self._children = children

    @property
    def children(self):
        return self._children

    def add_child(self, child):
        self._children.append(child)

class Layout(Container):
    def __init__(self):
        super().__init__()
        self.cells = []

    def add_cell(self, cell):
        self.cells.append(cell)

    def add_child(self, child):
        if len(child.children) != len(self.cells):
            raise ValueError('number of items does not match number of cells in layout')
        super().add_child(child)

    def render(self, y0, bbox):
        # 1. measure all cells
        # 2. set their sizes according to the rules
        # 3. render them
        pass

class HLayout(Layout):
    def add_child(self, child):
        if not isinstance(child, HContainer):
            raise ValueError('child of HLayout must be instance of HContainer')
        super().add_child(child)

    def render(self, ystart, bbox):
        start, stop, offset = self.calculate_visible

class VLayout(Layout):
    def add_child(self, child):
        if not isinstance(child, VContainer):
            raise ValueError('child of VLayout must be instance of VContainer')
        super().add_child(child)

import itertools

'''
Renders widgets horizontally from left to right, possibly using layout information
from a HLayout parent.
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
Renders widgets vertically from top to bottom, possibly using layout information
from a VLayout parent.
'''
class VContainer(TransposeWidgetMixin, HContainer):
    pass

