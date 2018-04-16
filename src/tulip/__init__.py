INDENT_SIZE = 2

def print_indented(string, indent):
    print("{}{}".format(' ' * INDENT_SIZE * indent, string))

from tulip.keypress import KeypressMixin
from tulip.widget import Widget, TransposedWrapper, transpose_widget
from tulip.container import Container, HContainer, VContainer
from tulip.screen import MockScreen
from tulip.layout import Cell, CellGroup, Row, ColumnLayout, Column, RowLayout
from tulip.pager import Pager
from tulip.text import Text
