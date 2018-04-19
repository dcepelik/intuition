from math import inf
from enum import Enum
import tulip

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

class HViewport(tulip.Widget):
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

    def _render(self, screen, y, x, i, j, rows, cols):
        widget_rows, widget_cols = self.widget.render(screen, y, x, i, j, rows, self.cols)
        return (widget_rows, self.cols)

    def print_tree(self, indent = 0):
        self.widget.print_tree(indent)

class Row(CellGroup, tulip.HContainer):
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

import math

class ColumnLayout(Layout, tulip.VContainer):
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

    def _render(self, screen, y, x, i, j, rows, cols):
        self.calculate_size_of_cells(cols)
        return super()._render(screen, y, x, i, j, rows, cols)

class Column(tulip.transpose_widget(Row)):
    pass

class RowLayout(tulip.transpose_widget(ColumnLayout)):
    pass
