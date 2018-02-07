import unittest
from layout import *

class TextTest(unittest.TestCase):
    def test_natural_size(self):
        self.assertEqual(Text('').natural_size, (0, 0))
        self.assertEqual(Text('hello').natural_size, (1, 5))
    
    def test_size_when_rendered(self):
        text = Text('hello')

        # everything
        self.assertEqual(text.size_when_rendered(0, 0, 1, 5), (1, 5))
        # `ell'
        self.assertEqual(text.size_when_rendered(0, 1, 1, 3), (1, 3))
        # nothing (cols == 0)
        self.assertEqual(text.size_when_rendered(0, 2, 1, 0), (0, 0))
        # nothing (cols == 0)
        self.assertEqual(text.size_when_rendered(0, 0, 1, 0), (0, 0))
        # nothing (rows == 0)
        self.assertEqual(text.size_when_rendered(0, 0, 0, 100), (0, 0))
        # nothing (first line skipped)
        self.assertEqual(text.size_when_rendered(1, 0, 1, 100), (0, 0))
        # nothing (too many columns skipped)
        self.assertEqual(text.size_when_rendered(0, 10, 1, 100), (0, 0))

class HContainerTest(unittest.TestCase):
    def test_widgets_in_area(self):
        hcont = HContainer([
            Text('first'),
            Text('second'),
            Text('third')
        ])

        # everything
        self.assertEqual(hcont.widgets_in_area(0, 0, 1, 100), (0, 2, 0, 0, 1, 16))
        # `f' in `first'
        self.assertEqual(hcont.widgets_in_area(0, 0, 1, 1), (0, 0, 0, 0, 1, 1))
        # nothing (first row skipped)
        self.assertEqual(hcont.widgets_in_area(1, 0, 1, 100), (0, 2, 1, 0, 0, 0))
        # nothing (rows == cols == 0)
        self.assertEqual(hcont.widgets_in_area(0, 0, 0, 0), (0, 0, 0, 0, 0, 0))
        # `s' in `second'
        self.assertEqual(hcont.widgets_in_area(0, 5, 1, 1), (1, 1, 0, 0, 1, 1))
        # `e' in `second'
        self.assertEqual(hcont.widgets_in_area(0, 6, 1, 1), (1, 1, 0, 1, 1, 1))
        # `t' in `third'
        self.assertEqual(hcont.widgets_in_area(0, 11, 1, 1), (2, 2, 0, 0, 1, 1))
        # `d' in `third'
        self.assertEqual(hcont.widgets_in_area(0, 15, 1, 100), (2, 2, 0, 4, 1, 1))

    def test_natural_size(self):
        self.assertEqual(HContainer([]).natural_size, (0, 0))
        self.assertEqual(HContainer([Text('lorem'), Text('ipsum')]).natural_size, (1, 10))
        self.assertEqual(HContainer([Text(''), Text('hello')]).natural_size, (1, 5))
        self.assertEqual(HContainer([Text(''), Text('')]).natural_size, (0, 0))
