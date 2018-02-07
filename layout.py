#!/usr/bin/env python

from math import inf
from enum import Enum

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

class Text:
    def __init__(self, text):
        self.text = text

    @property
    def natural_size(self):
        return (1, len(self.text)) if self.text else (0, 0)

    def size_when_rendered(self, i, j, rows, cols):
        # if i > 0 or rows == 0, this line of text is invisible
        cols = 0 if i > 0 or rows == 0 else min(len(self.text[j:]), cols)
        # if there's no widht, there's no height
        rows = 1 if cols > 0 else 0
        return (rows, cols)

class Container:
    def __init__(self, children = []):
        self.children = children

    def add_child(self, child):
        self.children.append(child)

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

'''
Renders widgets horizontally from left to right, possibly using layout information
from a HLayout parent.
'''
class HContainer(Container):
    def widgets_in_area(self, i, j, rows, cols):
        # determine first_visible_idx
        first_visible_idx = 0
        for idx, child in enumerate(self.children):
            child_rows, child_cols = child.natural_size
            if child_cols > j:
                # (part of) this widget will be rendered
                break
            j -= child_cols
            assert i >= 0
            first_visible_idx += 1

        offset_first_cols = j

        # determine last_visible_idx
        max_rows = 0
        total_cols = 0
        last_visible_idx = first_visible_idx
        for idx, child in enumerate(self.children[first_visible_idx:]):
            child_rows, child_cols = child.size_when_rendered(i, j, rows, cols - total_cols)
            j = 0
            total_cols += child_cols
            max_rows = max(max_rows, child_rows)
            if total_cols >= cols:
                # this is the last visible widget
                break
            last_visible_idx += 1

        last_visible_idx = min(last_visible_idx, len(self.children) - 1)
        return (first_visible_idx, last_visible_idx, i, offset_first_cols, max_rows, total_cols)

    def size_when_rendered(self, i, j, rows, cols):
        _, _, _, _, max_rows, total_cols = self.widgets_in_area(i, j, rows, cols)
        return (max_rows, total_cols)

    @property
    def natural_size(self):
        total_cols = 0
        max_rows = 0
        for child in self.children:
            child_rows, child_cols = child.natural_size
            total_cols += child_cols
            max_rows = max(max_rows, child_rows)
        return (max_rows, total_cols)

'''
Renders widgets vertically from top to bottom, possibly using layout information
from a VLayout parent.
'''
class VContainer(Container):
    pass

vlayout = VLayout()
vlayout.add_cell(Cell())
vlayout.add_cell(Cell())

first_column = VContainer([
    Text("Hello"),
    Text("World")
])

second_column = VContainer([
    VContainer([
        Text("Single line"),
        Text("Hello World!")
    ]),
    VContainer([
        Text("And another line!")
    ])
])

vlayout.add_child(first_column)
vlayout.add_child(second_column)
