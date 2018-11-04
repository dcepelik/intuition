#!/usr/bin/env python3
import tulip

c1 = tulip.Text('C1')
c1.focusable = True

screen = tulip.MockScreen(1, 2)

hc = tulip.HContainer([
    tulip.Text('A'),
    tulip.Text('B'),
    tulip.VContainer([
        c1,
        tulip.Text('C2'),
        tulip.Text('C3'),
    ]),
    tulip.Text('D'),
    tulip.Text('E'),
])
hc.focusable = True

def preorder_walk(w):
    while w:
        yield w
        w = w._nlr_walk(1)

hc.render(screen, 0, 0, 0, 1, screen.nrows, screen.ncols)
print(screen)
print(hc.last_render_l)
print(hc.last_render_r)
for c in preorder_walk(hc):
    print(c)
