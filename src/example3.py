#!/usr/bin/env python3

import tulip

screen = tulip.AnsiScreen(20, 80)

class MainWindow(tulip.RowLayout):
    pass

pager = tulip.Pager([])

window_list = tulip.HContainer()
window_list.add_child(tulip.Text('+inbox-killed  '))
window_list.add_child(tulip.Text('+spam'))

statusbar = tulip.ColumnLayout()
statusbar.add_cell(tulip.Cell(weight=1))
statusbar.add_cell(tulip.Cell(weight=1))
statusbar.add_cell(tulip.Cell(weight=1))
statusbar.add_child(tulip.Row([
    tulip.Text(':reply-all'),
    tulip.Text('1/20'),
    tulip.Text('1/405'),
]))

window = MainWindow()
window.add_cell(tulip.Cell())
window.add_cell(tulip.Cell(weight=1))
window.add_cell(tulip.Cell())
window.add_child(tulip.Column([window_list, pager, statusbar]))

window.render(screen, 0, 0, 0, 0, screen.nrows, screen.ncols)
screen.render()
