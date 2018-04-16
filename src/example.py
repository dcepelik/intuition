#!/usr/bin/python3

import tulip
import flowers

screen = tulip.MockScreen(20, 80)

class SearchResultsWindow(tulip.RowLayout):
    pass

class ThreadLine(tulip.Row):
    def __init__(self, date, sender, subject):
        super().__init__()
        self.add_child(tulip.Text(date))
        self.add_child(tulip.Text('  '))
        self.add_child(tulip.Text(sender))
        self.add_child(tulip.Text('  '))
        self.add_child(tulip.Text(subject))
        self.focusable = True
        self.register_key_handler('m', self.do_m, 'do m, baby')

    def do_m(self, key):
        self.print_keys_help()

    def print_keys_help(self):
        for key, (handler, help_msg) in self.key_handlers.items():
            print("{}    {}".format(key, help_msg))

class ThreadView(tulip.ColumnLayout):
    def __init__(self):
        super().__init__()
        self.add_cell(tulip.Cell())
        self.add_cell(tulip.Cell())
        self.add_cell(tulip.Cell())
        self.add_cell(tulip.Cell())
        self.add_cell(tulip.Cell(weight=2))

threads = ThreadView()
pager = tulip.Pager([threads])

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

window = SearchResultsWindow()
window.add_cell(tulip.Cell())
window.add_cell(tulip.Cell(weight=1))
window.add_cell(tulip.Cell())
window.add_child(tulip.Column([window_list, pager, statusbar]))
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

window.find_first_leaf().focus()

while True:
    sys.stdout.write("\033[H\033[J")
    screen.clear()
    window.render(screen, 0, 0, 0, 0, screen.nrows, screen.ncols)
    print(screen)
    print("Focused:")
    window.find_focused_leaf().print_tree(1)
    ch = read_char()
    if ch == 'q':
        break
    elif ch == 'J':
        pager.next_page()
    elif ch == 'K':
        pager.prev_page()
    elif ch == 'j':
        print("Succ:")
        foc_succ = window.find_focused_leaf().find_focusable_successor()
        if foc_succ:
            foc_succ.focus()
    else:
        window.find_focused_leaf().keypress(ch)
    read_char()
