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

import itertools

'''
Renders widgets horizontally from left to right, possibly using layout information
from a HLayout parent.
'''
class HContainer(Container):
    def widgets_in_area(self, i, j, rows, cols):
        children = iter(self.children)

        first_visible_idx = 0
        for child in children:
            child_rows, child_cols = child.natural_size
            if child_cols > j:
                children = itertools.chain([child], children)
                break
            j -= child_cols
            assert j >= 0
            first_visible_idx += 1
        offset_first_cols = j

        last_visible_idx = first_visible_idx
        max_rows = 0
        total_cols = 0
        for child in children:
            child_rows, child_cols = child.size_when_rendered(i, j, rows, cols - total_cols)
            j = 0
            total_cols += child_cols
            max_rows = max(max_rows, child_rows)
            if total_cols >= cols:
                break
            last_visible_idx += 1

        return (first_visible_idx, last_visible_idx, i, offset_first_cols, max_rows, total_cols)

    def size_when_rendered(self, i, j, rows, cols):
        _, _, _, _, rows, cols = self.widgets_in_area(i, j, rows, cols)
        return (rows, cols)

    @property
    def natural_size(self):
        total_cols = 0
        max_rows = 0
        for child in self.children:
            child_rows, child_cols = child.natural_size
            total_cols += child_cols
            max_rows = max(max_rows, child_rows)
        return (max_rows, total_cols)

class RotatedWidget:
    def __init__(self, widget):
        self.widget = widget

    def size_when_rendered(self, i, j, rows, cols):
        widget_rows, widget_cols = self.widget.size_when_rendered(j, i, cols, rows)
        return (widget_cols, widget_rows)

    @property
    def natural_size(self):
        rows, cols = self.widget.natural_size
        return (cols, rows)

'''
Renders widgets vertically from top to bottom, possibly using layout information
from a VLayout parent.
'''
class VContainer(Container):
    def rotated_children(self):
        for child in self.children:
            yield RotatedWidget(child)

    def widgets_in_area(self, i, j, rows, cols):
        hcont = HContainer(self.rotated_children())
        (first_visible_idx,
            last_visible_idx,
            offset_rows,
            offset_cols,
            max_rows,
            total_cols) = hcont.widgets_in_area(j, i, cols, rows)
        return (first_visible_idx, last_visible_idx, offset_cols, offset_rows, total_cols, max_rows)

    def size_when_rendered(self, i, j, rows, cols):
        _, _, _, _, rows, cols = self.widgets_in_area(i, j, rows, cols)
        return (rows, cols)

    @property
    def natural_size(self):
        rows, cols = HContainer(self.rotated_children()).natural_size
        return (cols, rows)
