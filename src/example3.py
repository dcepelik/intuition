#!/usr/bin/env python3

import pdb
import tulip
import re
import string
import time
from datetime import datetime
import notmuch
import shutil
import email
import email.parser
import email.policy

cols, rows = shutil.get_terminal_size()
screen = tulip.AnsiScreen(rows - 1, cols)

def hook_check_mark():
    return "\u2022"

def hook_absdate(unix):
    now = int(time.time())
    d = now - unix
    return datetime.fromtimestamp(unix).strftime("%d.%m.%Y %H:%M")

def hook_thread_subject(t):
    return t.get_subject()

def hook_is_me(name):
    return name == 'David Čepelík' or name == 'David Cepelik'

def hook_my_short_name():
    return 'me'

def hook_show_header(name):
    return name.lower() in {'subject', 'to', 'user-agent', 'x-mailer'}

def hook_ago(unix, short=True):
    now = int(time.time())
    d = now - unix
    minute = 60
    hour = 60 * minute
    day = 24 * hour
    week = 7 * day
    month = 30 * day
    year = 365 * day
    def helper(scale, unit):
        v = int(d / scale)
        if v > 1:
            unit += 's'
        if short:
            return '{}{}'.format(v, unit[0])
        return '{} {} ago'.format(v, unit)
    if d > 3 * month:
        return helper(month, 'month')
    if d > week:
        return helper(week, 'week')
    if d > day:
        return helper(day, 'day')
    if d > 2 * hour:
        return helper(hour, 'hour')
    if d > minute:
        return helper(minute, 'minute')
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

#def hook_is_quote_intro(line, addrs):
#    def ends_with_colon():
#        return l[-1] == ':'
#    def contains_keywords():
#        keywords = {"quoting", "wrote", "napsal(a)"}
#        for w in l.split(' '):
#            if w.lower() in keywords:
#                return True
#        return False
#    def mentions_author_address():
#        for a in addrs:
#            if a in line:
#                return True
#        return False
#    tests = [ends_with_colon, contains_keywords, mentions_author_address]
#    score = 0
#    for t in tests:
#        if t():
#            score += 1
#    return score >= 2

class Collapsible(tulip.VContainer):
    def __init__(self, a, b):
        super().__init__([a, b])
        self.a = a
        self.b = b
        self.collapsed = None
        self.expand()
        self.onkey("\r", lambda c, w: self.toggle())

    def collapse(self):
        self.a.hide()
        self.b.show()
        self.collapsed = True
        return self

    def expand(self):
        self.a.show()
        self.b.hide()
        self.collapsed = False
        return self

    def toggle(self):
        if self.collapsed:
            self.expand()
        else:
            self.collapse()
        return self

class BodyView(tulip.VContainer):
    def __init__(self, text=''):
        super().__init__()
        self._text = text
        self.do()

    def do(self):
        self.clear_children()
        para = re.sub("\r\n", "\n", self._text).split("\n\n")
        first = True
        q = None
        cover = None
        for p in para:
            if not p:
                continue
            if not first:
                self.add_child(tulip.Box(1, 0))
            q = None
            for l in p.split("\n"):
                if not l:
                    continue
                if l[0] == '>':
                    if not q:
                        q = tulip.VContainer().add_class('quote')
                        cover = tulip.Text().add_class('quote')
                        c = Collapsible(q, cover).collapse()
                        c.focusable = True
                        self.add_child(c)
                    q.add_child(tulip.Paragraph(l))
                    cover.text = '- {} quoted lines'.format(len(q._children))
                else:
                    q = None
                    self.add_child(tulip.Paragraph(l))
            first = False

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, t):
        if self._text != t:
            self._text = t
            self.do()

#class ThreadsW:
#    def __init__(self, nm_threads):
#        self.nm_threads = nm_threads
#        self._threads = None
#
#    def threads():
#        if not self._threads:
#            self._threads = [ThreadW(t) for t in self._nm_threads]
#        return self._threads
#
#class ThreadW:
#    def __init__(self, nm_thread):
#        self.nm_thread = nm_thread
#        self.



class MessageView(tulip.VContainer):
    def __init__(self, nm_msg, indent=0):
        super().__init__()
        self.nm_msg = nm_msg
        self.indent = indent

        layout = tulip.ColumnLayout()
        layout.add_cell(tulip.Cell())
        layout.add_cell(tulip.Cell())
        layout.add_cell(tulip.Cell())
        layout.add_cell(tulip.Cell(weight=1))

        self.ui_absdate = tulip.Text().add_class('absdate')
        self.ui_reldate = tulip.Text()
        self.ui_author = tulip.Text().add_class('msg-author')
        self.ui_author_addr = tulip.Text().add_class('msg-author_addr')
        self.ui_summary = tulip.HContainer([
            self.ui_author,
            tulip.Box(0, 1),
            self.ui_author_addr,
            self.ui_absdate,
            tulip.Box(0, 1),
            tulip.Text('('),
            self.ui_reldate,
            tulip.Text(') '),
        ])
        layout.add_child(tulip.Row([
            tulip.Box(0, 2 * self.indent),
            tulip.Text('+'),
            tulip.Box(0, 1),
            self.ui_summary,
        ]).add_class('msg-header'))

        self.ui_headers = tulip.ColumnLayout()
        self.ui_headers.add_cell(tulip.Cell())
        self.ui_headers.add_cell(tulip.Cell())
        self.ui_headers.add_cell(tulip.Cell(weight=1))
        layout.add_child(tulip.Row([
            tulip.Empty(),
            tulip.Empty(),
            tulip.Empty(),
            self.ui_headers,
        ]).add_class('msg-headers'))

        layout2 = tulip.ColumnLayout()
        layout2.add_cell(tulip.Cell())
        layout2.add_cell(tulip.Cell(weight=1))
        self.ui_text = BodyView().add_class('msg-text')
        layout2.add_child(tulip.Row([
            tulip.Box(0, 2 * self.indent),
            tulip.VContainer([
                tulip.Box(1, 0),
                self.ui_text,
                tulip.Box(1, 0),
            ]),
        ]))

        self.ui_replies = tulip.VContainer()
        for r in self.nm_msg.get_replies():
            self.ui_replies.add_child(MessageView(r, self.indent + 1))

        self.add_child(layout)
        self.add_child(layout2)
        self.add_child(self.ui_replies)

    def before_render(self):
        unix = self.nm_msg.get_date()
        self.ui_absdate.text = hook_absdate(unix)
        self.ui_reldate.text = hook_ago(unix, short=False)
        try:
            with open(self.nm_msg.get_filename(), 'rb') as msg_file:
                msg = email.parser.BytesParser(policy=email.policy.default).parse(msg_file)
                self.ui_headers.clear_children()
                for h in msg:
                    if not hook_show_header(h):
                        continue
                    self.ui_headers.add_child(tulip.Row([
                        tulip.Text(h + ':').add_class('header-name'),
                        tulip.Box(0, 1),
                        tulip.Text(msg[h]),
                    ]))
                author = msg['from'].addresses[0]
                self.ui_author.text = author.display_name or author.username
                self.ui_author_addr.text = '<{}@{}> '.format(author.username, author.domain)
                self.ui_author_addr.hide()
                for part in msg.walk():
                    if part.get_content_type() == 'text/plain':
                        self.ui_text.text = part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8')
                        break
        except UnicodeDecodeError:
            pass

class ThreadView(tulip.VContainer):
    def __init__(self, nm_thread):
        super().__init__()
        self.nm_thread = nm_thread

    def build_msg_view_and_replies(self, msg):
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
        self.ui_reldate = tulip.Text().add_class('date')
        self.ui_authors = tulip.Text().add_class('authors')
        self.ui_total_lparen = tulip.Text(' (')
        self.ui_total = tulip.Text()
        self.ui_total_rparen = tulip.Text(') ')
        self.ui_check = tulip.Text(hook_check_mark() + ' ').add_class('check')
        self.ui_subj = tulip.Text().add_class('subject')
        self.ui_tags = tulip.Text().add_class('tags')
        self.add_child(self.ui_reldate)
        self.add_child(tulip.Box(0, 1))
        self.add_child(self.ui_authors)
        self.add_child(self.ui_total_lparen)
        self.add_child(self.ui_total)
        self.add_child(self.ui_total_rparen)
        self.add_child(self.ui_check)
        self.add_child(tulip.HContainer([self.ui_subj, tulip.Box(0, 1), self.ui_tags]))

    def toplevel_msgs(self):
        self.tlc = self.nm_thread.get_toplevel_messages()
        return self.tlc

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
        self.ui_reldate.text = hook_thread_date(self.nm_thread)
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
        self.ui_pager = tulip.Pager()
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

def hook_set_active_widget(w):
    win.ui_pager.clear_children()
    win.ui_pager.add_child(w)
    f = win.nlr_first_focusable()
    if f:
        f.focus()

def hook_switch_main_window():
    ui_threads.focus()
    hook_set_active_widget(ui_threads)
hook_switch_main_window()

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
        cur = win.find_focused_leaf()
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
            f = cur.nlr_next_focusable()
            if f:
                f.focus()
                f.redraw()
                print(f)
                if not f.is_visible():
                    win.ui_pager.next_page()
        elif ch == 'k':
            f = cur.nlr_prev_focusable()
            if f:
                f.focus()
                f.redraw()
                if not f.is_visible():
                    win.ui_pager.prev_page()
            else:
                raise UIError("No messages above")
        elif ch == 'h':
            hook_switch_main_window()
        elif ch == 'g':
            f = win.nlr_first_focusable()
            if f:
                f.focus()
                if not f.is_visible():
                    win.ui_pager.scroll_to_widget(f)
        elif ch == 'G':
            f = win.nlr_last_focusable()
            if f:
                f.focus()
                if not f.is_visible():
                    win.ui_pager.scroll_to_widget(f)
        elif ch == 'z':
            win.ui_pager.scroll_to_widget(cur)
        elif ch == 'l':
            mv = MessageView(next(cur.toplevel_msgs()))
            hook_set_active_widget(mv)
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
            cur.keypress(ch)
    except UIError as e:
        win.add_error(e)
    except tulip.UnhandledKeyError:
        win.add_error("Key {} not bound".format(hook_charname(ch)))
            #win.add_error("Key {} not bound".format(hook_charname(ch)))
