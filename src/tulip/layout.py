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

class CellGroup:
    def __init__(self):
        super().__init__()
        self._layout = None

    @property
    def layout(self):
        # TODO Not necessary?
        if not self._layout:
            self._layout = self.lookup(Layout)
        return self._layout

class Viewport(tulip.Widget):
    def __init__(self, widget, rows=None, cols=None, halign=HAlign.LEFT):
        super().__init__()
        self.widget = widget
        self.rows = rows
        self.cols = cols
        self.halign = halign

    def _measure(self):
        widget_rows, widget_cols = self.widget.size
        return (self.rows if self.rows is not None else widget_rows, self.cols if self.cols is not None else widget_cols) # TODO or: a bit of a hack

    def _render(self, screen, y, x, i, j, rows, cols):
        widget_rows, widget_cols = self.widget.size
        r = self.rows if self.rows is not None else rows
        c = self.cols if self.cols is not None else cols
        s = 0
        if self.halign == HAlign.CENTER:
            s = int(0.5 * (c - widget_cols))
        elif self.halign == HAlign.RIGHT:
            s = c - widget_cols
        if s > 0:
            x += s
        else:
            j += s
        widget_rows, widget_cols = self.widget.render(screen, y, x, i, j, r, c)
        return (self.rows if self.rows is not None else widget_rows, self.cols if self.cols is not None else widget_cols)

    def print_tree(self, indent = 0):
        tulip.print_indented("Viewport (rows={}, cols={}) of:".format(self.rows, self.cols), indent)
        self.widget.print_tree(indent + 1)

class Row(tulip.HContainer, CellGroup):
    def __init__(self, children = None):
        super().__init__(children or [])

    @property
    def rendered_widgets(self):
        widgets = []
        for idx, w in enumerate(super().rendered_widgets):
            c = self.layout.cells[idx]
            widgets.append(Viewport(w, cols=c.width, halign=c.halign))
        return widgets

class Column(tulip.VContainer, CellGroup):
    def __init__(self, children = None):
        super().__init__(children or [])

    @property
    def rendered_widgets(self):
        return [Viewport(widget, rows=self.layout.cells[idx].height) for idx, widget in enumerate(super().rendered_widgets)]

class Layout:
    def __init__(self):
        super().__init__()
        self._cells = []

    @property
    def cells(self):
        return self._cells

    def add_cell(self, cell):
        self._cells.append(cell)

    def _max_cell_size_generic(self, b, skip, u):
        a = 1 - b
        sum_a = 0
        sum_a2 = 0
        cell_size = [0] * len(self.cells)
        for cell_group in self._children:
            sum_a += cell_group.size[a]
            if sum_a < skip:
                continue
            sum_a2 += cell_group.size[a]
            for idx, cell_content in enumerate(cell_group._children):
                cell_size[idx] = max(cell_size[idx], cell_content.size[b])
            if sum_a2 >= u:
                break
        return cell_size

    def _set_cell_sizes_generic(self, target_size, b, skip, u):
        max_cell_size = self._max_cell_size_generic(b, skip, u)
        cells_total = sum(max_cell_size)
        for idx, cell in enumerate(self.cells):
            cell_size = [None, None]
            cell_max_size = [cell.max_height, cell.max_width]
            cell_min_size = [cell.min_height, cell.min_width]
            cell_size[b] = 0 if cell.weight > 0 else max_cell_size[idx]
            cell_size[b] = max(cell_min_size[b], min(cell_max_size[b], cell_size[b]))
            cell_size[b] = min(cell_size[b], target_size)
            cell.height = cell_size[0]
            cell.width = cell_size[1]
        avail_size = target_size - sum((cell.height, cell.width)[b] for cell in self.cells)
        if avail_size > 0:
            sum_weight = sum(cell.weight for cell in self.cells)
            # why the hell is `cell` defined in this scope?
            for cell in self.cells:
                cell_size = [cell.height, cell.width]
                if cell.weight > 0:
                    cell_size[b] += int(avail_size * (float(cell.weight) / sum_weight))
                    cell.height = cell_size[0]
                    cell.width = cell_size[1]

    def _measure_generic(self, a, b):
        sum_max_b = sum(self._max_cell_size_generic(b, 0, inf))
        sum_a = sum(child.size[a] for child in self._children)
        return (sum_a, sum_max_b)


class ColumnLayout(Layout, tulip.VContainer):
    def __init__(self):
        super().__init__()

    def _render(self, screen, y, x, i, j, rows, cols):
        self._set_cell_sizes_generic(cols, 1, i, rows)
        return super()._render(screen, y, x, i, j, rows, cols)

    def _measure(self):
        return self._measure_generic(0, 1)

class RowLayout(Layout, tulip.HContainer):
    def __init__(self):
        super().__init__()

    def _render(self, screen, y, x, i, j, rows, cols):
        self._set_cell_sizes_generic(rows, 0, j, cols)
        return super()._render(screen, y, x, i, j, rows, cols)

    def _measure(self):
        return self._measure_generic(1, 0)
