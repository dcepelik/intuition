#!/usr/bin/env python3

import tulip
import ago
import notmuch

screen = tulip.AnsiScreen(18, 120)

class MainWindow(tulip.RowLayout):
    @property
    def _measure(self):
        print(super()._size_generic(1, 0))
        return super().size

threads_ui = tulip.ColumnLayout()
threads_ui.add_cell(tulip.Cell(halign=tulip.HAlign.RIGHT))
threads_ui.add_cell(tulip.Cell())
threads_ui.add_cell(tulip.Cell(weight=1))
threads_ui.add_cell(tulip.Cell())
threads_ui.add_cell(tulip.Cell())
threads_ui.add_cell(tulip.Cell())
threads_ui.add_cell(tulip.Cell(weight=2))

database = notmuch.Database()
threads = database.create_query('tag:inbox and not tag:killed').search_threads()
for t in threads:
    tags = tulip.Text(' '.join(['+' + u for u in t.get_tags()]) or '')
    subj = tulip.Text(t.get_subject() or 'no subject')
    subj.add_class('focused')
    thread_ui = tulip.Row([
        tulip.Text(ago.human(t.get_newest_date(), precision=1, abbreviate=True)),
        tulip.Box(0, 1),
        tulip.Text(t.get_authors()),
        tulip.Text(' ('),
        tulip.Text(str(t.get_total_messages())),
        tulip.Text(') '),
        tulip.HContainer([
            tags,
            tulip.Box(0, 1),
            subj,
        ]),
    ])
    thread_ui.focusable = True
    threads_ui.add_child(thread_ui)

pager = tulip.Pager([threads_ui])

window_list = tulip.HContainer()
window_list.add_child(tulip.Text('+inbox-killed  '))
window_list.add_child(tulip.Text('+spam'))

statusbar = tulip.ColumnLayout()
statusbar.add_cell(tulip.Cell(weight=1))
statusbar.add_cell(tulip.Cell(weight=1, halign=tulip.HAlign.CENTER))
statusbar.add_cell(tulip.Cell(weight=1, halign=tulip.HAlign.RIGHT))
statusbar.add_child(tulip.Row([
    tulip.Text(':reply-all'),
    tulip.Text('1p/20'),
    tulip.Text('1m/405'),
]))

window = MainWindow()
window.add_cell(tulip.Cell())
window.add_cell(tulip.Cell(weight=1))
window.add_cell(tulip.Cell())
window.add_child(tulip.Column([window_list, pager, statusbar]))

window.find_first_leaf().focus()
#window.print_tree()

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

import cProfile, pstats, io
from pstats import SortKey
pr = cProfile.Profile()

while True:
    pr.enable()
    sys.stdout.write("\033[H\033[J")
    sys.stdout.flush()
    screen.clear()
    window.render(screen, 0, 0, 0, 0, screen.nrows, screen.ncols)
    screen.render()
    cur = window.find_focused_leaf()
    if screen.is_widget_visible(cur):
        print("F Visible")
    else:
        print("F Invisible")
    print('---')
    #print("Focused:")
    #for i, tl in enumerate(threads._children):
    #    print("#{}: {}".format(i, tl.visible))
    #window.find_focused_leaf().print_tree(1)
    pr.disable()
    ch = read_char()
    if ch == 'q':
        break
    elif ch == 'J':
        pager.next_page()
    elif ch == 'K':
        pager.prev_page()
    elif ch == 'j':
        foc_succ = cur.find_focusable_successor()
        if foc_succ:
            foc_succ.focus()
        else:
            l = window.find_first_leaf()
            if not l.focusable:
                l = l.find_focusable_successor()
            if l:
                l.focus()
    elif ch == 'k':
        foc_pred = cur.find_focusable_predecessor()
        if foc_pred:
            foc_pred.focus()
        else:
            l = window.find_last_leaf()
            if not l.focusable:
                l = l.find_focusable_predecessor()
            if l:
                l.focus()
    else:
        window.find_focused_leaf().keypress(ch)

s = io.StringIO()
sortby = SortKey.CUMULATIVE
ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
ps.print_stats()
print(s.getvalue())
