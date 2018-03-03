#!/usr/bin/python3

import layout

class SearchResultsWindow(layout.VContainer):
    pass

class ThreadLine(layout.Row):
    def __init__(self, date, sender, subject):
        super().__init__()
        self.add_child(layout.Text(date))
        self.add_child(layout.Text('  '))
        self.add_child(layout.Text(sender))
        self.add_child(layout.Text('  '))
        self.add_child(layout.Text(subject))

class ThreadView(layout.ColumnLayout):
    def __init__(self):
        super().__init__()
        self.add_cell(layout.Cell())
        self.add_cell(layout.Cell())
        self.add_cell(layout.Cell())
        self.add_cell(layout.Cell())
        self.add_cell(layout.Cell(weight=2))

threads = ThreadView()
pager = layout.Pager(threads)

window = SearchResultsWindow()
window.add_child(pager)
window.add_child(layout.Text("Status line"))

for i in range(0, 30):
    threads.add_child(ThreadLine("Date", "Sender", "Subject #{}".format(i)))

screen = layout.MockScreen(20, 80)
pager.vscroll += 19
split_view = layout.VContainer()
window.render(screen, 0, 0, 0, 0, screen.nrows, screen.ncols)
print(screen)
