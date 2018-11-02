#!/usr/bin/python3

import tulip

class Message:
    def __init__(self, headers, text):
        self.headers = headers
        self.text = text
        self.follows = []

    def add_followup(self, msg1):
        self.follows.add(msg1)

screen = tulip.AnsiScreen(20, 40)

class MessageView(tulip.VContainer):
    def __init__(self, msg, indent=0):
        super().__init__()
        self.indent = indent
        header = tulip.ColumnLayout()
        header.add_class('bluebg')
        header.add_cell(tulip.Cell())
        header.add_cell(tulip.Cell())
        header.add_cell(tulip.Cell())
        header.add_cell(tulip.Cell())
        header.add_cell(tulip.Cell())
        header.add_cell(tulip.Cell())
        header.add_cell(tulip.Cell())
        header.add_cell(tulip.Cell(weight=1))

        sender = tulip.Text('Foo')
        sender.add_class('focused')

        header.add_child(tulip.Row([
            tulip.Box(0, 1),
            tulip.Text('+'),
            tulip.Box(0, 1),
            sender,
            tulip.Box(0, 1),
            tulip.Text('(2 days ago)'),
            tulip.Box(0, 1),
            tulip.Text('nowhere to go'),
        ]))
        self.add_child(header)

        vindent = tulip.ColumnLayout()
        vindent.add_cell(tulip.Cell(min_width=2 * indent))
        vindent.add_cell(tulip.Cell(weight=1))
        vindent.add_child(tulip.Row([
            tulip.Text(''),
            tulip.Paragraph("Hello World\nThis line is much longer than the others on purpose,\nso that the trivial line-wrapping algorithm can be demonstrated"),
        ]))
        self.add_child(vindent)

msg1 = Message({'From': 'foo', 'Subject': 'bar'}, 'hello')
msg1.follows.append(Message({'From': 'foo', 'Subject': 'bar'}, 'hello'))
msg1.follows.append(Message({'From': 'foo', 'Subject': 'bar'}, 'hello'))
msg1.follows.append(Message({'From': 'foo', 'Subject': 'bar'}, 'hello'))
msg1v = MessageView(msg1)
msg2v = MessageView(msg1, indent=1)

vcont = tulip.VContainer([msg1v, tulip.Box(1, 0), msg2v])
vcont.render(screen, 0, 0, 0, 0, screen.nrows, screen.ncols)
screen.render()
