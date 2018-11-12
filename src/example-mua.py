#!/usr/bin/env python3

import pdb
import os
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
screen = tulip.AnsiScreen(rows, cols)

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

class Collapsible(tulip.VContainer):
    def __init__(self, a, b):
        super().__init__([a, b])
        self.a = a
        self.b = b
        self.collapsed = None
        self.expand()
        self.onkey("l", lambda c, w: self.toggle())

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

class Switcher(tulip.VContainer):
    def __init__(self, children = []):
        super().__init__(children)
        self.active = None

    def add_child(self, w):
        super().add_child(w)
        if not self.active:
            self.active = w
        else:
            w.hide()

    def switch_to(self, w):
        if self.active:
            self.active.hide()
        w.focus()
        self.active = w.show()

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
                    cover.text = '-- {} quoted line(s) --'.format(len(q._children))
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

class MessageView(tulip.VContainer):
    def __init__(self, nm_msg, indent=0):
        super().__init__()
        self.nm_msg = nm_msg
        self.indent = indent
        self.mtime = None

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
        hdr_row = tulip.Row([
            tulip.Box(0, 2 * self.indent),
            tulip.Text('+'),
            tulip.Box(0, 2),
            self.ui_summary,
        ]).add_class('msg-header')
        hdr_row.focusable = True
        layout.add_child(hdr_row)

        self.ui_headers = tulip.ColumnLayout()
        self.ui_headers.add_cell(tulip.Cell())
        self.ui_headers.add_cell(tulip.Cell())
        self.ui_headers.add_cell(tulip.Cell(weight=1))
        headers_row = tulip.Row([
            tulip.Empty(),
            tulip.Empty(),
            tulip.Empty(),
            self.ui_headers,
        ]).add_class('msg-headers')
        self.ui_hdr_coll = Collapsible(headers_row, tulip.Empty()).collapse()
        layout.add_child(self.ui_hdr_coll)

        self.ui_att = tulip.VContainer()

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
                self.ui_att,
                tulip.Box(1, 0),
            ]),
        ]))
        self.ui_text_coll = Collapsible(layout2, tulip.Empty()).collapse()

        self.ui_replies = tulip.VContainer()
        for r in self.nm_msg.get_replies():
            self.ui_replies.add_child(MessageView(r, self.indent + 1))

        self.add_child(layout)
        self.add_child(self.ui_text_coll)
        self.add_child(self.ui_replies)

        def next_msg(w, c):
            m = w.next_p(lambda u: isinstance(u, MessageView))
            if m:
                m.first_focusable().focus()
                return True
            raise UIError("No next message")

        def prev_msg(w, c):
            m = w.prev_p(lambda u: isinstance(u, MessageView))
            if m:
                m.first_focusable().focus()
                return True
            raise UIError("No previous message")

        self.onkey("l", lambda w, c: w.ui_text_coll.toggle())
        self.onkey("H", lambda w, c: w.ui_hdr_coll.toggle())
        self.onkey("n", next_msg)
        self.onkey("p", prev_msg)

    def before_render(self):
        mtime = os.path.getmtime(self.nm_msg.get_filename())
        if self.mtime == mtime:
            win.ui_cmd.text = "Reused"
            return
        self.mtime = mtime

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
                    if part.get_content_maintype() == 'multipart':
                        continue
                    if part.get_content_type() == 'text/plain':
                        self.ui_text.text += part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8')
                    else:
                        ui_att = tulip.Text(
                            "-- Attachment: {} --".format(part.get_filename())
                        ).add_class('quote')
                        ui_att.focusable = True
                        self.ui_att.add_child(ui_att)
                if not self.ui_text.text:
                    self.ui_text.text = 'HTML bullcrap'
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

class ThreadListItem(tulip.Row):
    def __init__(self, nm_thread):
        super().__init__()
        self.nm_thread = nm_thread
        self.focusable = True
        self.selected = False
        self.mv = None

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

        def show(w, c):
            if not self.mv:
                self.mv = MessageView(next(self.toplevel_msgs()))
            hook_set_active_widget(self.mv)
            return True

        self.onkey('l', show)

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
        self.ui_cmd = tulip.Text()
        self.ui_switcher = Switcher()
        self.ui_pager = tulip.Pager([self.ui_switcher])
        self.ui_msgcount = tulip.Text().add_class('msgcount')
        self.ui_pgcount = tulip.Text().add_class('pgcount')
        self.ui_statusbar = tulip.ColumnLayout()
        self.ui_statusbar.add_cell(tulip.Cell(weight=1))
        self.ui_statusbar.add_cell(tulip.Cell(weight=1, halign=tulip.HAlign.CENTER))
        self.ui_statusbar.add_cell(tulip.Cell(weight=1, halign=tulip.HAlign.RIGHT))
        self.ui_statusbar.add_child(tulip.Row([
            self.ui_cmd,
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
        pass

    def add_error(self, msg):
        self.ui_errlist.add_child(tulip.Text("E: {}".format(msg)).add_class('error'))
        self.ui_errlist.show()
        self.ui_statusbar.hide()

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
    if w not in win.ui_switcher._children:
        win.ui_switcher.add_child(w)
    if w.focused_leaf() == w:
        f = w.first_focusable()
        if f:
            f.focus()
    win.ui_switcher.switch_to(w)

def hook_switch_main_window():
    #ui_threads.focus()
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
        win.render(screen, 0, 0, 0, 0, screen.nrows, screen.ncols)

        focused = win.focused_leaf()
        if focused and not focused.is_visible():
            v = win.ui_pager.next_visible_p(tulip.focusable_p)
            if v:
                v.focus()
            focused = v

        if focused:
            win.ui_msgcount.text = 'Msg {}/{}'.format(1 + focused.index(), len(ui_threads._children))
            if ui_threads.selection:
                win.ui_msgcount.text += ' ({}{})'.format(len(ui_threads.selection), hook_check_mark())

        screen.clear()
        win.render(screen, 0, 0, 0, 0, screen.nrows, screen.ncols)
        screen.render()
        win.ui_errlist.clear_children()
        win.ui_errlist.hide()
        win.ui_statusbar.show()

        ch = read_char()
        if ch == 'q':
            break
        elif ch == 'j':
            f = focused.next_p(lambda w: w.focusable and not w.hidden_r)
            if f:
                f.focus()
                if not f.is_visible():
                    win.ui_pager.scroll_to_widget(f)
            else:
                raise UIError("No messages below")
        elif ch == 'k':
            f = focused.prev_p(lambda w: w.focusable and not w.hidden_r)
            if f:
                f.focus()
                if not f.is_visible():
                    win.ui_pager.scroll_to_widget(f)
            else:
                raise UIError("No messages above")
        elif ch == 'h':
            hook_switch_main_window()
        elif ch == 'g':
            f = win.first_focusable()
            if f:
                f.focus()
                if not f.is_visible():
                    win.ui_pager.scroll_to_widget(f)
        elif ch == 'G':
            f = win.last_focusable()
            if f:
                f.focus()
                if not f.is_visible():
                    win.ui_pager.scroll_to_widget(f)
        elif ch == 'z':
            win.ui_pager.scroll_to_widget(focused)
        elif ch == 'J':
            win.ui_pager.next_page()
        elif ch == 'K':
            win.ui_pager.prev_page()
        elif ch == '@':
            pass
        elif ch == ' ':
            focused.toggle_selected()
            f = focused.next_p(lambda w: w.focusable and not w.hidden_r)
            if f:
                f.focus()
                if not f.is_visible():
                    win.ui_pager.scroll_to_widget(f)
        elif ch == 'C':
            for w in win.srch(MessageView):
                w.ui_text_coll.toggle()
        elif ch == 'v':
            for t in ui_threads._children:
                t.toggle_selected()
        else:
            if focused:
                focused.keypress(ch)
    except UIError as e:
        win.add_error(e)
        pass
    except tulip.UnhandledKeyError:
        win.add_error("Key {} not bound".format(hook_charname(ch)))
            #win.add_error("Key {} not bound".format(hook_charname(ch)))
