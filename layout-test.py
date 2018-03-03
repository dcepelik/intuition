import unittest
from layout import *

class SoupUITestCase(unittest.TestCase):
    def assertScreenContent(self, screen, rows):
        num_missing = screen.nrows - len(rows)
        if num_missing > 0:
            rows += [''] * num_missing
        self.assertEqual(rows, screen.rows)
        screen.clear()

class TextTest(SoupUITestCase):
    def test_size(self):
        self.assertEqual(Text('').size, (0, 0))
        self.assertEqual(Text('hello').size, (1, 5))
    
    def test_render(self):
        text = Text('hello')
        screen = MockScreen(1, 10)

        self.assertEqual(text.render(screen, 0, 0, 0, 0, 1, 10), (1, 5))
        self.assertScreenContent(screen, ['hello'])

        self.assertEqual(text.render(screen, 0, 0, 0, 0, 0, 10), (0, 0))
        self.assertScreenContent(screen, [''])

        self.assertEqual(text.render(screen, 0, 0, 0, 4, 1, 1), (1, 1))
        self.assertScreenContent(screen, ['o'])

class FixedSizeWidget(Widget):
    @property
    def size(self):
        return (2, 4)

    def render(self):
        return self.size

class TransposedWidgetTest(SoupUITestCase):
    def test_size(self):
        fixed = FixedSizeWidget()
        transposed = TransposedWidget(fixed)
        self.assertEqual(transposed.size, (4, 2))

class HContainerTest(SoupUITestCase):
    def test_size(self):
        self.assertEqual(HContainer([]).size, (0, 0))
        self.assertEqual(HContainer([Text('lorem'), Text('ipsum')]).size, (1, 10))
        self.assertEqual(HContainer([Text(''), Text('hello')]).size, (1, 5))
        self.assertEqual(HContainer([Text(''), Text('')]).size, (0, 0))

    def test_renders_basic_hcont(self):
        screen = MockScreen(1, 10)
        self.assertEqual(HContainer([]).render(screen, 0, 0, 0, 0, 100, 100), (0, 0))
        self.assertScreenContent(screen, [''])

        self.assertEqual(HContainer([Text('hello')]).render(screen, 0, 0, 0, 0, 100, 100), (1, 5))
        self.assertScreenContent(screen, ['hello'])

    def test_renders_partial_hcont(self):
        screen = MockScreen(5, 16)
        hcont = HContainer([
            Text('skipped'),
            Text('hello'),
            Text('world'),
            Text('not rendered')
        ])

        self.assertEqual(hcont.render(screen, 0, 0, 0, 8, 1, 5), (1, 5))
        self.assertScreenContent(screen, ['ellow'])

        self.assertEqual(hcont.render(screen, 0, 0, 0, 0, 1, 1), (1, 1))
        self.assertScreenContent(screen, ['s'])

        self.assertEqual(hcont.render(screen, 1, 1, 0, 1, 1, 10), (1, 10))
        self.assertScreenContent(screen, ['', ' kippedhell'])

        self.assertEqual(HContainer([Text('hello')]).render(screen, 0, 0, 1, 0, 10, 10), (0, 0))
        self.assertScreenContent(screen, [])

class VContainerTest(SoupUITestCase):
    def test_size(self):
        self.assertEqual(VContainer([Text('')]).size, (0, 0))
        self.assertEqual(VContainer([Text('hello')]).size, (1, 5))
        vcont = VContainer([
            Text('hello world'),
            Text('this is'),
            Text('soupui')
        ])
        self.assertEqual(vcont.size, (3, 11))

    def test_render(self):
        screen = MockScreen(10, 10)

        self.assertEqual(VContainer([Text('hello')]).render(screen, 0, 0, 0, 0, 1, 5), (1, 5))
        self.assertScreenContent(screen, ['hello'])

        self.assertEqual(VContainer([Text('hello'), Text('world')]).render(screen, 0, 0, 0, 0, 10, 5), (2, 5))
        self.assertScreenContent(screen, ['hello', 'world'])

        vcont = VContainer([
            Text('a'),
            Text('bbbbbb'),
            Text('ccc'),
            Text('ddddd')
        ])
        self.assertEqual(vcont.render(screen, 0, 0, 0, 1, 4, 10), (3, 5))
        self.assertScreenContent(screen, ['bbbbb', 'cc', 'dddd'])

        self.assertEqual(vcont.render(screen, 0, 0, 0, 3, 4, 10), (2, 3))
        self.assertScreenContent(screen, ['bbb', 'dd'])

class ColumnLayoutTest(SoupUITestCase):
    def test_render(self):
        layout = ColumnLayout()
        layout.add_cell(Cell())
        layout.add_cell(Cell())
        layout.add_cell(Cell())
        layout.add_cell(Cell())
        layout.add_child(Row([Text('1'), Text('2'), Text('veryveryverylong'), Text('4')]))
        layout.add_child(Row([HViewport(Text('4'), 2), Text('world'), Text('6'), Text('7')]))
        layout.add_child(Row([Text('hello'), Text('5'), Text('6'), Text('7')]))

        screen = MockScreen(10, 40)
        self.assertEqual(layout.render(screen, 0, 0, 0, 0, 10, 40), (3, 27))

        self.assertScreenContent(screen, [
            '1    2    veryveryverylong4',
            '4    world6               7',
            'hello5    6               7'
        ])

class TransposedCellTest(SoupUITestCase):
    def test_transpose(self):
        cell = Cell(min_width=4, max_height=2, valign=VAlign.BOTTOM)
        tcell = cell.transpose()
        self.assertEqual(tcell.max_width, cell.max_height)
        self.assertEqual(tcell.halign, cell.valign)
        tcell.width = 20
        self.assertEqual(tcell.width, cell.height)
        self.assertEqual(tcell.height, cell.width)

class RowLayoutTest(SoupUITestCase):
    def test_render(self):
        layout = RowLayout()
        layout.add_cell(Cell())
        layout.add_cell(Cell())
        layout.add_child(Column([VContainer([Text('aaaaa'), Text('aaaaa')]), Text('bbbbb')]))
        layout.add_child(Column([Text('ccccc'), VContainer([Text('ddddd'), Text('ddddd')])]))

        screen = MockScreen(10, 40)
        self.assertEqual(layout.render(screen, 0, 0, 0, 0, 10, 40), (4, 10))

        self.assertScreenContent(screen, [
            'aaaaaccccc',
            'aaaaa',
            'bbbbbddddd',
            '     ddddd'
        ])

    def test_weighted_render(self):
        layout = RowLayout()
        layout.add_cell(Cell(weight=1))
        layout.add_cell(Cell(weight=1))
        layout.add_child(Column([Text('aaa'), Text('bbb')]))
        layout.add_child(Column([VContainer([Text('ccc'), Text('ccc')]), Text('ddd')]))

        screen = MockScreen(6, 40)
        self.assertEqual(layout.render(screen, 0, 0, 0, 0, screen.nrows, screen.ncols), (6, 6))
        self.assertScreenContent(screen, [
            'aaaccc',
            '   ccc',
            '',
            'bbbddd',
            '',
        ])
