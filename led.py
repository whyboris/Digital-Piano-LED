# to run: `sudo python3 led.py`

from time import sleep
from time import time
import math
import threading

import board
import neopixel

import mido

import keyboard

NUM_OF_PIXELS = 144

pixels = neopixel.NeoPixel(board.D18, NUM_OF_PIXELS, brightness=0.2, auto_write=False)

for x in range (0, NUM_OF_PIXELS):
  pixels[x] = (0, 0, 0)

devices = mido.get_input_names()
piano = []

for device in devices:
  if device.startswith('B2'):
    piano.append(device)

print('Listening for MIDI from', piano[0])

if piano[0] is None:
  print('Piano not connected?')
  quit()


# =======================================================================
# DECLARE SOME VARIABLES

# array for all BLOBS
all_things = []

# array for pixel color computation - to be written to the LED strip later
rgb = [1] * NUM_OF_PIXELS # fill all of them with 1

# to throttle keyboard events
throttle_left = 0 
throttle_right = 0
throttle_f12 = 0

# each Blob is a key pressed that evolves over time via its `update` method
class Blob:
  def __init__(self, x, r, v):
    self.x = x
    self.r = r
    self.v = v
  
  def update(self):
    self.r = self.r + 1
    self.v = math.floor(self.v * 0.8)



def add_note_to_workspace(key, val):
  pixels[key] = (val, val, val)
  pixels.show()
  all_things.append(Blob(key, 1, val))


def thread_function(name):
  while True:

    print(len(all_things))
    for blob in all_things:
      blob.update()
      for x in range(blob.x - blob.r, blob.x + blob.r):
        # pixels[x] = (blob.v, blob.v, blob.v)
        rgb[x] = max(rgb[x] + blob.v, 255)

    for idx, val in enumerate(rgb):
      pixels[idx] = (math.floor(val * 0.8), math.floor(val * 0.8), math.floor(val * 0.8))

    pixels.show()

    sleep(0.1)
    
    all_things[:] = [a for a in all_things if a.v > 2]

thread = threading.Thread(target=thread_function, args=(1,))
thread.start()

def handle_pedal(pedal):
  if pedal == 67:
    throttle_key('left')
  elif pedal == 66:
    throttle_key('right')
  elif pedal == 64:
    print('legato')
  else:
    print('unknown!')
    print(msg)


def throttle_key(key):
  global throttle_left
  global throttle_right
  global throttle_f12
  now = time()
  
  if key == 'left':
  
    if now < throttle_right + 1 and now > throttle_f12 + 0.5:
      throttle_f12 = now
      keyboard.press_and_release('f12')
    elif now > throttle_left + 0.5:
      throttle_left = now
      keyboard.press_and_release(key)

  elif key == 'right':
  
    if now < throttle_left + 1 and now > throttle_f12 + 0.5:
      throttle_f12 = now
      keyboard.press_and_release('f12')
    elif now > throttle_right + 0.5:
      throttle_right = now
      keyboard.press_and_release(key)


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
        val = math.floor(raw * 2) # make dimmer
        add_note_to_workspace(msg.note, val)
      # pixels[msg.note] = (val, val, val) 
    
    elif hasattr(msg, 'control'):
      # pedal pressed
      pedal = msg.control
      handle_pedal(pedal)

    else:
      pring('something new and unknown!')
      print(msg)
