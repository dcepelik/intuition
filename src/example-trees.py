#!/usr/bin/env python3
import tulip

c1 = tulip.Text('C1')
c1.focusable = True
e = tulip.Text('E')

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
    e,
])
hc.focusable = True

for w in hc.descendants():
    print(w)
print("--")
for w in c1.predecessors():
    print(w)
print("--")
for w in e.predecessors():
    print(w)
print("--")
print(c1.next_p(lambda w: True))
print(tulip.Widget.f(c1))
