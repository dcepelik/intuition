INDENT_SIZE = 2

def print_indented(string, indent):
    print("{}{}".format(' ' * INDENT_SIZE * indent, string))

from tulip.keypress import KeypressMixin, UnhandledKeyError
from tulip.widget import Widget, Box, Empty
from tulip.container import Container, HContainer, VContainer
from tulip.screen import MockScreen, AnsiScreen
from tulip.layout import Cell, CellGroup, Row, ColumnLayout, Column, RowLayout, HAlign, VAlign
from tulip.pager import Pager
from tulip.text import Text, Paragraph
