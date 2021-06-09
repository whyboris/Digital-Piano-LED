# clear out all pixels that are turned on

import board
import neopixel

NUM_OF_PIXELS = 144

pixels = neopixel.NeoPixel(board.D18, NUM_OF_PIXELS, brightness=0.2, auto_write=False)

for x in range (0, NUM_OF_PIXELS):
  pixels[x] = (0, 0, 0)

pixels.show()