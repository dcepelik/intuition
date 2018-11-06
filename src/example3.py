#!/usr/bin/env python3

import tulip
import re
import time
import notmuch
import shutil

cols, rows = shutil.get_terminal_size()
screen = tulip.AnsiScreen(rows - 1, cols)

def hook_check_mark():
    return "\u2022"

def hook_thread_subject(t):
    return t.get_subject()

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
    def helper(scale, unit):
        return '{}{}'.format(int(d / scale), unit)
    if d > 3 * month:
        return helper(month, 'M')
    if d > week:
        return helper(week, 'w')
    if d > day:
        return helper(day, 'd')
    if d > 2 * hour:
        return helper(hour, 'h')
    if d > minute:
        return helper(minute, 'm')
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

def hook_charname(c):
    if not c.isspace():
        return c
    if c == "\r":
        return 'Return'
    if c == ' ':
        return 'Space'

class UIError(Exception):
    pass

# Widget support for relative focus moving
class ThreadList(tulip.ColumnLayout):
    def __init__(self, search):
        super().__init__()
        self.search = search
        self.selection = set()
        self.add_cell(tulip.Cell(halign=tulip.HAlign.RIGHT))
        self.add_cell(tulip.Cell())
        self.add_cell(tulip.Cell(weight=1))
        self.add_cell(tulip.Cell())
        self.add_cell(tulip.Cell(halign=tulip.HAlign.RIGHT))
        self.add_cell(tulip.Cell())
        self.add_cell(tulip.Cell())
        self.add_cell(tulip.Cell(weight=2))

    @property
    def pager(self):
        return self.lookup(tulip.Pager)

    def next_msg(self):
        f = self.find_focused_leaf()
        if f:
            f = cur.nlr_next_focusable()
        if f:
            f.focus()
            self.redraw()
            if not f.is_visible():
                self.pager.next_page()
        else:
            raise UIError("No messages below")

    def prev_msg(self):
        f = self.find_focused_leaf()
        if f:
            f = f.nlr_prev_focusable()
        if f:
            f.focus()
            self.redraw()
            if not f.is_visible():
                self.pager.prev_page()
        else:
            raise UIError("No messages above")

    def focus_first_msg(self):
        l = win.ui_pager.nlr_first_focusable()
        if l:
            l.focus()
            win.ui_pager.scroll_to_widget(l)

    def focus_last_msg(self):
        l = win.ui_pager.nlr_last_focusable()
        if l:
            l.focus()
            win.ui_pager.scroll_to_widget(l)

class ThreadListItem(tulip.Row):
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

    @property
    def thread_list(self):
        return self.lookup(ThreadList)

    def toggle_selected(self):
        self.selected = not self.selected
        if self.selected:
            self.thread_list.selection.add(self)
        else:
            self.thread_list.selection.remove(self)

    def before_render(self):
        self.ui_date.text = hook_thread_date(self.nm_thread)
        self.ui_authors.text = hook_thread_authors(self.nm_thread)
        total = hook_thread_total_msgs(self.nm_thread)
        self.ui_total.text = str(total)
        self.ui_total_lparen.hidden = self.ui_total_rparen.hidden = self.ui_total.hidden = total < 2
        self.ui_check.hidden = not self.selected
        self.ui_subj.text = hook_thread_subject(self.nm_thread) or hook_no_subject_text()
        self.ui_tags.text = hook_thread_tags(self.nm_thread) or ''

ui_threads = ThreadList(None)

class SoupWindow(tulip.RowLayout):
    def __init__(self):
        super().__init__()
        self.tabs = []
        self.ui_pager = tulip.Pager([ui_threads])
        self.ui_msgcount = tulip.Text().add_class('msgcount')
        self.ui_pgcount = tulip.Text().add_class('pgcount')
        self.ui_statusbar = tulip.ColumnLayout()
        self.ui_statusbar.add_cell(tulip.Cell(weight=1))
        self.ui_statusbar.add_cell(tulip.Cell(weight=1, halign=tulip.HAlign.CENTER))
        self.ui_statusbar.add_cell(tulip.Cell(weight=1, halign=tulip.HAlign.RIGHT))
        self.ui_statusbar.add_child(tulip.Row([
            tulip.Text(':reply-all'),
            self.ui_pgcount,
            self.ui_msgcount,
        ]))
        self.ui_errlist = tulip.HContainer()
        self.add_cell(tulip.Cell(weight=1))
        self.add_cell(tulip.Cell())
        self.add_cell(tulip.Cell())
        self.add_child(tulip.Column([
            self.ui_pager,
            self.ui_statusbar,
            self.ui_errlist,
        ]))

    def before_render(self):
        self.ui_pgcount.text = 'Page {}/{}'.format(self.ui_pager.page(), self.ui_pager.num_pages())

    def after_render(self):
        self.ui_errlist.clear_children()

    def add_error(self, msg):
        self.ui_errlist.add_child(tulip.Text("E: {}".format(msg)).add_class('error'))

class Tab(tulip.VContainer):
    def __init__(self, widget, title):
        self.title = title

database = notmuch.Database()
query = hook_default_query()
threads = database.create_query(query).search_threads()
for t in threads:
    ui_threads.add_child(ThreadListItem(t))

query_ui = tulip.Text().add_class('query')

win = SoupWindow()
win.tabs.append(Tab(None, 'foo'))
f = win.nlr_first_focusable()
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

while True:
    try:
        cur = ui_threads.find_focused_leaf()
        query_ui.text = query
        if cur:
            if ui_threads.selection:
                win.ui_msgcount.text = 'Msg {}/{} ({}{})'.format(1 + cur.index(), len(ui_threads._children), len(ui_threads.selection), hook_check_mark())
            else:
                win.ui_msgcount.text = 'Msg {}/{}'.format(1 + cur.index(), len(ui_threads._children))
        screen.clear()
        def render():
            win.render(screen, 0, 0, 0, 0, screen.nrows, screen.ncols)
        render()
        screen.render()
        ch = read_char()
        if ch == 'q':
            break
        elif ch == 'j':
            ui_threads.next_msg()
        elif ch == 'k':
            ui_threads.prev_msg()
        elif ch == 'g':
            ui_threads.focus_first_msg()
        elif ch == 'G':
            ui_threads.focus_last_msg()
        elif ch == 'z':
            win.ui_pager.scroll_to_widget(cur)
        elif ch == 'J':
            win.ui_pager.next_page()
            win.ui_pager.redraw()
            if cur and not cur.is_visible():
                v = win.ui_pager.nlr_next_visible()
                while v and not v.focusable: # TODO idiomatically
                    v = v.nlr_next_visible()
                if v:
                    v.focus()
        elif ch == 'K':
            win.ui_pager.prev_page()
            win.ui_pager.redraw()
            if cur and not cur.is_visible():
                v = win.ui_pager.nlr_next_visible()
                while v and not v.focusable:
                    v = v.nlr_next_visible()
                if v:
                    v.focus()
        elif ch == '@':
            pass
        elif ch == ' ':
            cur.toggle_selected()
            ui_threads.next_msg()
        elif ch == 'v':
            for t in ui_threads._children:
                t.toggle_selected()
        else:
            win.add_error("Key {} not bound".format(hook_charname(ch)))
    except UIError as e:
        win.add_error(e)
