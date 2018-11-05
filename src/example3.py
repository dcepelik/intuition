#!/usr/bin/env python3

import tulip
import re
import time
import notmuch
import shutil

cols, rows = shutil.get_terminal_size()
screen = tulip.AnsiScreen(rows - 1, cols)

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
threads_ui.add_cell(tulip.Cell(halign=tulip.HAlign.RIGHT))
threads_ui.add_cell(tulip.Cell())
threads_ui.add_cell(tulip.Cell())
threads_ui.add_cell(tulip.Cell(weight=2))

sel = set()

def hook_name_is_mine(name):
    return name == 'David Čepelík' or name == 'David Cepelik'

def hook_my_short_name():
    return 'me'

def filter_authors(authors):
    r = []
    and_me = False
    for a in authors:
        if hook_name_is_mine(a):
            and_me = True
        else:
            r.append(re.split('[ @]', a)[0])
    return ([hook_my_short_name()] if and_me else []) + sorted(r)

def ago(unix):
    now = int(time.time())
    d = now - unix
    minute = 60
    hour = 60 * minute
    day = 24 * hour
    week = 7 * day
    month = 30 * day
    year = 365 * day
    if d > 3 * month:
        return '{}m'.format(int(d / month))
    if d > week:
        return '{}w'.format(int(d / week))
    if d > day:
        return '{}d'.format(int(d / day))
    if d > 2 * hour:
        return '{}h'.format(int(d / hour))
    if d > minute:
        return '{}m'.format(int(d / minute))
    return 'now'

class ThreadWidget(tulip.Row):
    def __init__(self, children=[]):
        super().__init__(children)
        self.selected = False
        self.sel_mark = tulip.Text('').add_class('sel_mark')

    def before_render(self):
        self.sel_mark.set_text("{} ".format(hook_tick_char()) if self.selected else '')

database = notmuch.Database()
query = 'tag:inbox and not tag:killed'
threads = database.create_query(query).search_threads()
for t in threads:
    tags = tulip.Text(' '.join(['+' + u for u in t.get_tags()]) or '')
    tags.add_class('tags')
    subj = tulip.Text(t.get_subject() or '(no subject)')
    subj.add_class('subject')
    total = t.get_total_messages()
    authors = re.split('[|,] ?', t.get_authors())
    authors = filter_authors(authors)
    authors_ui = tulip.Text(', '.join(authors))
    authors_ui.add_class('authors')
    thread_ui = ThreadWidget([
        tulip.Text(ago(t.get_newest_date())),
        tulip.Box(0, 1),
        authors_ui,
    ])

    if total > 1:
        thread_ui.add_child(tulip.Text(' ('))
        thread_ui.add_child(tulip.Text(str(total)))
        thread_ui.add_child(tulip.Text(') '))
    else:
        thread_ui.add_child(tulip.Box(0, 0))
        thread_ui.add_child(tulip.Box(0, 0))
        thread_ui.add_child(tulip.Box(0, 0))
    thread_ui.add_child(thread_ui.sel_mark)

    thread_ui.add_child(tulip.HContainer([
        subj,
        tulip.Box(0, 1),
        tags,
    ]))
    thread_ui.focusable = True
    threads_ui.add_child(thread_ui)

def hook_tick_char():
    return '+' #"\u2713"

pager = tulip.Pager([threads_ui])

query_ui = tulip.Text('').add_class('query')
window_list = tulip.HContainer()
window_list.add_child(query_ui)

msgcount = tulip.Text('')
pgcount = tulip.Text('')
statusbar = tulip.ColumnLayout()
statusbar.add_cell(tulip.Cell(weight=1))
statusbar.add_cell(tulip.Cell(weight=1, halign=tulip.HAlign.CENTER))
statusbar.add_cell(tulip.Cell(weight=1, halign=tulip.HAlign.RIGHT))
statusbar.add_child(tulip.Row([
    tulip.Text(':reply-all'),
    pgcount,
    msgcount,
]))

errlist = tulip.HContainer()

window = MainWindow()
window.add_cell(tulip.Cell())
window.add_cell(tulip.Cell(weight=1))
window.add_cell(tulip.Cell())
window.add_cell(tulip.Cell())
window.add_child(tulip.Column([window_list, pager, statusbar, errlist]))

f = window.nlr_first_focusable()
if f:
    f.focus()

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

def charname(c):
    if not c.isspace():
        return c
    if c == "\r":
        return 'Return'
    if c == ' ':
        return 'Space'

import cProfile, pstats, io
from pstats import SortKey
pr = cProfile.Profile()

while True:
    cur = threads_ui.find_focused_leaf()
    query_ui.set_text(query)
    if cur:
        if sel:
            msgcount.set_text('Msg {}/{} ({}{})'.format(1 + cur.index(), len(threads_ui._children), len(sel), hook_tick_char()))
        else:
            msgcount.set_text('Msg {}/{}'.format(1 + cur.index(), len(threads_ui._children)))
        pgcount.set_text('Page {}/{}'.format(pager.page(), pager.num_pages()))
    screen.clear()
    def render():
        window.render(screen, 0, 0, 0, 0, screen.nrows, screen.ncols)
    def error(msg):
        errlist.add_child(tulip.Text("E: {}".format(msg)).add_class('error'))
    render()
    screen.render()
    errlist.clear_children()
    ch = read_char()
    def next_msg():
        f = cur.nlr_next_focusable()
        if f:
            f.focus()
            render()
            if not f.is_visible():
                pager.next_page()
        else:
            error("No messages below")
    if ch == 'q':
        break
    elif ch == 'j':
        next_msg()
    elif ch == 'k':
        f = cur.nlr_prev_focusable()
        if f:
            f.focus()
            render()
            if not f.is_visible():
                pager.prev_page()
        else:
            error("No messages above")
    elif ch == 'J':
        pager.next_page()
        render()
        if cur and not cur.is_visible():
            v = pager.nlr_next_visible()
            while v and not v.focusable: # TODO idiomatically
                v = v.nlr_next_visible()
            if v:
                v.focus()
    elif ch == 'K':
        pager.prev_page()
        render()
        if cur and not cur.is_visible():
            v = pager.nlr_next_visible()
            while v and not v.focusable:
                v = v.nlr_next_visible()
            if v:
                v.focus()
    elif ch == 'g':
        l = pager.nlr_first_focusable()
        if l:
            l.focus()
            pager.scroll_to_widget(l)
    elif ch == 'G':
        l = pager.nlr_last_focusable()
        if l:
            l.focus()
            pager.scroll_to_widget(l)
    elif ch == 'z':
        pager.scroll_to_widget(cur)
    elif ch == '@':
        pass
    elif ch == ' ':
        cur.selected = not cur.selected
        if cur.selected:
            sel.add(cur)
        else:
            sel.remove(cur)
        next_msg()
    elif ch == 'v':
        for t in threads_ui._children:
            t.selected = not t.selected
            if t.selected:
                sel.add(t)
            else:
                sel.remove(t)
    else:
        error("Key {} not bound".format(charname(ch)))
