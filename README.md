# Tulip

Welcome to the home page of Tulip, the truly light-weight TUI library for Python.

## ABOUT

I'm sick and tired of *all* TUI frameworks for Python. This is my take at the topic.

## FEATURES

  - **Very new and thus not mature enough**
  - KISS architecture with powerful abstractions
  - Extremely compact (~ 500 SLOC)
  - Only renders widgets which are visible at the moment (not as simple as it seems)
  - Lazy construction of widgets
  - Clean interface to the terminal, not coupled with `curses`
  - We even have some tests!

### Widget set

Only a few built-in widgets at the moment:

  - `HContainer` and `VContainer` for horizontal and vertical placement of widgets
  - `RowLayout` and `ColumnLayout` for table-like placement of widgets
  - `Pager` for "scrollable" content

## ARCHITECTURE

A `Widget` is a base class representing a renderable object. It defines a minimal
interface all widgets must implement:

  - `size(self)` returns the size of the widget as a `(rows, cols)` tuple.
  - `render(self, screen, y, x, i, j, rows, cols)` renders (a part of) the
    widget to position `(y, x)` on the `screen`. The part of the widget to
    be rendered is given by the other parameters, where `(j, i)` is the top-left
    corner of the rendered rectangle which is `rows` by `cols` characters:

<div style="text-align: center">
<img width=1000 src="https://github.com/dcepelik/tulip/blob/master/img/render.svg" alt="How rendering works" />

</div>

The partial rendering support makes it possible to render things efficiently.
For example if the rendered widget is a huge container with hundreds of children,
only those children which are in the rectangle described by `i, j, rows` and `cols`
will be rendered. Also, the widgets may not exist prior to rendering and only
those which are actually needed will be instantiated. (If the instantiation
is expensive and involves reading a file, for example, this becomes very useful.)

There's one more smart idea behind Tulip. Consider the `HContainer` and `VContainer`
containers: the first renders things horizontally (left-to-right), the latter
renders things vertically (top-to-bottom):

<div style="text-align: center">
<img width=700 src="https://github.com/dcepelik/tulip/blob/master/img/hcont-and-vcont.svg" alt="HContainer and VContainer" />
</div>

If you were to write the source code for both, you would quickly notice that
`HContainer` and `VContainer` do basically the same thing:

  - `render` places widgets next to each other either horizontally or vertically,
  - `size` is maximum in one direction and the sum of sizes of widgets in the other
    direction.

There are several ways to capture this symmetry in the code. The way I chose to
look at it is that the `VContainer` is the same thing as the `HContainer`,
except transposed. There's a function called `transpose_widget` which takes
a widget class and creates a thin wrapper around it which performs the
transposition. In the code, it's as simple as this:

```python
class VContainer(tulip.transpose_widget(HContainer)):
    pass
```

The transposition is simple, too:

```python
def transpose_widget(widget_class):
    class TransposedWidgetClass(widget_class):
        @property
        def rendered_widgets(self):
            return [child.transpose() for child in super().rendered_widgets]

        def _render(self, screen, y, x, i, j, rows, cols):
            return swap_axes(super()._render(screen, x, y, j, i, cols, rows))

        @property
        def size(self):
            return swap_axes(super().size)

    return TransposedWidgetClass
```

## MORE TO COME

Stay tuned!
