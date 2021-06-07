from time import sleep
import board
import neopixel
import math

NUM_OF_PIXELS = 144

pixels = neopixel.NeoPixel(board.D18, NUM_OF_PIXELS, brightness=0.2, auto_write=False)

for x in range (0, NUM_OF_PIXELS):
  pixels[x] = (0, 0, 0)

import mido

devices = mido.get_input_names()

# print(devices)

all_things = []

rgb = [0] * NUM_OF_PIXELS

piano = []

for device in devices:
  if device.startswith('B2'):
    piano.append(device)

# print(piano)
print('Listening for MIDI from', piano[0])

class Blob:
  def __init__(self, x, r, v):
    self.x = x
    self.r = r
    self.v = v
  
  def update(self):
    self.r = self.r + 1
    self.v = math.floor(self.v / 2)



def lol(key, val):
  pixels[key] = (val, val, val)
  pixels.show()
  all_things.append(Blob(key, 1, val))


import threading

def thread_function(name):
  while True:

    print(len(all_things))
    for blob in all_things:
      blob.update()
      for x in range(blob.x - blob.r, blob.x + blob.r):
        # pixels[x] = (blob.v, blob.v, blob.v)
        rgb[x] = blob.v

    for idx, val in enumerate(rgb):
      pixels[idx] = (val, val, val)

    pixels.show()

    sleep(0.5)
    
    all_things[:] = [a for a in all_things if a.v > 1]

thread = threading.Thread(target=thread_function, args=(1,))
thread.start()

with mido.open_input(piano[0]) as inport:
  for msg in inport:
    # print(msg)
    if hasattr(msg, 'velocity'):
      # print(msg.velocity)
      raw = msg.velocity
      if raw == 64: # represents key-up velocity
        # do nothing!
        pass
      else:
        val = math.floor(raw * 0.4) # make dimmer
        lol(msg.note, val)
      # pixels[msg.note] = (val, val, val) 
    
    elif hasattr(msg, 'control'):
      # pedal pressed
      pedal = msg.control

      if pedal == 67:
        print('left')
      elif pedal == 66:
        print('right')
      elif pedal == 64:
        print('legato')
      else:
        print('unknown!')
        print(msg)

    else:
      pring('something new and unknown!')
      print(msg)
