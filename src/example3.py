#!/usr/bin/env python3

import tulip
import re
import time
import notmuch
import shutil

cols, rows = shutil.get_terminal_size()
screen = tulip.AnsiScreen(rows - 1, cols)

def hook_check_mark():
    return '+' #"\u2713"

class MainWindow(tulip.RowLayout):
    @property
    def _measure(self):
        print(super()._size_generic(1, 0))
        return super().size

class ThreadList(tulip.ColumnLayout):
    def __init__(self, search):
        super().__init__()
        self.search = search
        self.add_cell(tulip.Cell(halign=tulip.HAlign.RIGHT))
        self.add_cell(tulip.Cell())
        self.add_cell(tulip.Cell(weight=1))
        self.add_cell(tulip.Cell())
        self.add_cell(tulip.Cell(halign=tulip.HAlign.RIGHT))
        self.add_cell(tulip.Cell())
        self.add_cell(tulip.Cell())
        self.add_cell(tulip.Cell(weight=2))

def hook_thread_subject(t):
    return t.get_subject()

class ThreadView2(tulip.Row):
    def __init__(self, nm_thread):
        super().__init__()
        self.nm_thread = nm_thread
        self.focusable = True
        self.selected = False
        self.ui_date = tulip.Text().add_class('time')
        self.ui_authors = tulip.Text().add_class('date')
        self.ui_total_lparen = tulip.Text(' (')
        self.ui_total = tulip.Text()
        self.ui_total_rparen = tulip.Text(') ')
        self.ui_check = tulip.Text(hook_check_mark() + ' ').add_class('check')
        self.ui_subj = tulip.Text().add_class('subject')
        self.ui_tags = tulip.Text().add_class('tags')
        self.add_child(self.ui_date)
        self.add_child(tulip.Box(0, 1))
        self.add_child(self.ui_authors)
        self.add_child(self.ui_total_lparen)
        self.add_child(self.ui_total)
        self.add_child(self.ui_total_rparen)
        self.add_child(self.ui_check)
        self.add_child(tulip.HContainer([self.ui_subj, tulip.Box(0, 1), self.ui_tags]))

    def toggle_select(self):
        self.selected = not self.selected

    def before_render(self):
        self.ui_date.text = hook_thread_date(self.nm_thread)
        self.ui_authors.text = hook_thread_authors(self.nm_thread)
        total = hook_thread_total_msgs(self.nm_thread)
        self.ui_total.text = str(total)
        self.ui_total_lparen.hidden = self.ui_total_rparen.hidden = self.ui_total.hidden = total < 2
        self.ui_check.hidden = not self.selected
        self.ui_subj.text = hook_thread_subject(self.nm_thread) or hook_no_subject_text()
        self.ui_tags.text = hook_thread_tags(self.nm_thread) or ''

threads_ui = ThreadList(None)
sel = set()

def hook_is_me(name):
    return name == 'David Čepelík' or name == 'David Cepelik'

def hook_my_short_name():
    return 'me'

def hook_ago(unix):
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

def hook_thread_date(t):
    return hook_ago(t.get_newest_date())

def hook_thread_tags(t):
    return ' '.join(['+' + u for u in t.get_tags()])

def hook_mangle_authors(authors):
    r = []
    and_me = False
    for a in authors:
        if hook_is_me(a):
            and_me = True
        else:
            r.append(re.split('[ @]', a)[0])
    return ([hook_my_short_name()] if and_me else []) + sorted(r)

def hook_thread_authors(t):
    authors = re.split('[|,] ?', t.get_authors())
    return ', '.join(hook_mangle_authors(authors))

def hook_thread_total_msgs(t):
    return t.get_total_messages()

def hook_default_query():
    return 'tag:inbox and not tag:killed'

def hook_no_subject_text():
    return '(no subject)'

database = notmuch.Database()
query = hook_default_query()
threads = database.create_query(query).search_threads()
for t in threads:
    threads_ui.add_child(ThreadView2(t))

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
    query_ui.text = query
    if cur:
        if sel:
            msgcount.text = 'Msg {}/{} ({}{})'.format(1 + cur.index(), len(threads_ui._children), len(sel), hook_check_mark())
        else:
            msgcount.text = 'Msg {}/{}'.format(1 + cur.index(), len(threads_ui._children))
        pgcount.text = 'Page {}/{}'.format(pager.page(), pager.num_pages())
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
        cur.toggle_select()
        if cur.selected:
            sel.add(cur)
        else:
            sel.remove(cur)
        next_msg()
    elif ch == 'v':
        for t in threads_ui._children:
            t.toggle_select()
            if t.selected:
                sel.add(t)
            else:
                sel.remove(t)
    else:
        error("Key {} not bound".format(charname(ch)))
