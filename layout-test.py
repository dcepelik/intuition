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
