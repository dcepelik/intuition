#!/usr/bin/env python3

import tulip

screen = tulip.MockScreen(20, 20)
swapped = tulip.SwappedAxesScreen(screen)

hc = tulip.HContainer([tulip.Text("Hello "), tulip.Text("World!")])

hc.render(swapped, 0, 0, 0, 0, 20, 20)
print(screen)

screen.clear()
hc.render(screen, 0, 0, 0, 0, 20, 20)
print(screen)
