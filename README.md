# Tulip

Welcome to the home page of Tulip, the truly light-weight TUI library for Python.

## ABOUT

I'm sick and tired of *all* TUI frameworks for Python. My turn!

## FEATURES

  - **Very new and thus not mature enough!**
  - Keep It Simple, Stupid!
  - Extremely compact (< 1k SLOC)
  - Reasonably efficient rendering of widgets
  - Clean interface to the terminal, not coupled with `curses`
  - Lazy construction of widgets
  - (Even comes with some tests!)

### Widget set

Only a few built-in widgets at the moment:

  - `HContainer` and `VContainer` for horizontal and vertical placement of widgets
  - `RowLayout` and `ColumnLayout` for table-like placement of widgets, with basic cell content alignment
  - `Pager` for "scrollable" content

## ARCHITECTURE

A `Widget` is a base class representing something which can be rendered. It
defines a minimal interface all widgets must implement:

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

There's only one smart idea behind Tulip: considering the `HContainer` and
`VContainer` containers, the first renders things horizontally (left-to-right),
the latter renders things vertically (top-to-bottom). Look:

<div style="text-align: center">
<img width=700 src="https://github.com/dcepelik/tulip/blob/master/img/hcont-and-vcont.svg" alt="HContainer and VContainer" />
</div>

If you were to write the source code for both, you would quickly notice that
`HContainer` and `VContainer` do basically the same thing:

  - `render` places widgets next to each other either horizontally or vertically,
  - `size` is maximum in one direction and the sum of sizes of widgets in the other
    direction.

I've taken about three attempts at capturing this symmetry; the best solution
is the simplest one: having a set of `*_generic` functions which take an extra
parameter or two (typically called `a` and `b`); by choosing values for these
parameters, you'll achieve horizontal or vertical behavior. If you see these
in the source, that's all they do.

## MORE TO COME

Stay tuned!
