#!/usr/bin/python3

import layout

screen = layout.MockScreen(20, 80)

class SearchResultsWindow(layout.RowLayout):
    pass

class ThreadLine(layout.Row):
    def __init__(self, date, sender, subject):
        super().__init__()
        self.add_child(layout.Text(date))
        self.add_child(layout.Text('  '))
        self.add_child(layout.Text(sender))
        self.add_child(layout.Text('  '))
        self.add_child(layout.Text(subject))
        self.focusable = True

class ThreadView(layout.ColumnLayout):
    def __init__(self):
        super().__init__()
        self.add_cell(layout.Cell())
        self.add_cell(layout.Cell())
        self.add_cell(layout.Cell())
        self.add_cell(layout.Cell())
        self.add_cell(layout.Cell(weight=2))

threads = ThreadView()
pager = layout.Pager([threads])

window_list = layout.HContainer()
window_list.add_child(layout.Text('+inbox-killed  '))
window_list.add_child(layout.Text('+spam'))

statusbar = layout.ColumnLayout()
statusbar.add_cell(layout.Cell(weight=1))
statusbar.add_cell(layout.Cell(weight=1))
statusbar.add_cell(layout.Cell(weight=1))
statusbar.add_child(layout.Row([
    layout.Text(':reply-all'),
    layout.Text('1/20'),
    layout.Text('1/405'),
]))

window = SearchResultsWindow()
window.add_cell(layout.Cell())
window.add_cell(layout.Cell(weight=1))
window.add_cell(layout.Cell())
window.add_child(layout.Column([window_list, pager, statusbar]))
#print(pager.parent)

for i in range(0, 30):
    threads.add_child(ThreadLine("Date", "Sender", "Subject #{}".format(i)))

import sys, tty, termios

def read_char():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

window.first_leaf.focus()

while True:
    sys.stdout.write("\033[H\033[J")
    screen.clear()
    window.render(screen, 0, 0, 0, 0, screen.nrows, screen.ncols)
    print(screen)
    print("Focused:")
    window.focused_leaf.print_tree(1)
    ch = read_char()
    if ch == 'q':
        break
    elif ch == 'J':
        pager.next_page()
    elif ch == 'K':
        pager.prev_page()
    elif ch == 'j':
        print("Succ:")
        foc_succ = window.focused_leaf.focusable_successor()
        if foc_succ:
            foc_succ.focus()
