#!/usr/bin/python3

import tulip

class Message:
    def __init__(self, headers, text):
        self.headers = headers
        self.text = text
        self.follows = []

    def add_followup(self, msg1):
        self.follows.add(msg1)

screen = tulip.AnsiScreen(20, 80)

class MessageView(tulip.VContainer):
    def __init__(self, msg, indent=0):
        super().__init__()
        self.msg = msg
        header = tulip.HContainer()
        header.add_class('bluebg')
        spacing = tulip.Text(' ' * 3 * indent)
        sender = tulip.Text('Foo Bar')
        sender.add_class('focused')
        times = tulip.Text(' (3 months ago)')
        mark = tulip.Text(' + ')
        clrfil = tulip.Text(128 * ' ')
        sample = tulip.Text(' I told you before, foo off my bar!')
        header.add_child(spacing)
        header.add_child(mark)
        header.add_child(sender)
        header.add_child(times)
        header.add_child(sample)
        header.add_child(clrfil)
        self.add_child(header)
        textlines = tulip.VContainer()
        textlines.add_child(tulip.Text("It is rather unexpected,"))
        textlines.add_child(tulip.Text("what I'm 'bout to say"))
        textlines.add_child(tulip.Text("I have become disconnected"))
        textlines.add_child(tulip.Text("From the worlds so far away"))
        self.add_child(textlines)

msg1 = Message({'From': 'foo', 'Subject': 'bar'}, 'hello')
msg1.follows.append(Message({'From': 'foo', 'Subject': 'bar'}, 'hello'))
msg1.follows.append(Message({'From': 'foo', 'Subject': 'bar'}, 'hello'))
msg1.follows.append(Message({'From': 'foo', 'Subject': 'bar'}, 'hello'))
msg1v = MessageView(msg1)
msg2v = MessageView(msg1)

vcont = tulip.VContainer([msg1v, msg2v])
vcont.render(screen, 0, 0, 0, 0, screen.nrows, screen.ncols)
screen.render()
