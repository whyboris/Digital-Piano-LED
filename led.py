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

devices = mido.get_input_names()
piano = []

for device in devices:
  if device.startswith('B2'):
    piano.append(device)

if len(piano) == 0:
  print('Piano not connected / turned on?')
  quit()
else:
  print('Listening for MIDI from', piano[0])


# =======================================================================
# DECLARE SOME VARIABLES

# array for all BLOBS
all_blobs = []

# array for pixel color computation - to be written to the LED strip later
rgb = [1] * NUM_OF_PIXELS # fill all of them with 1

# to throttle keyboard events
throttle_left = 0 
throttle_right = 0
throttle_f12 = 0

# each Blob is a key pressed that evolves over time via its `update` method
class Blob:
  def __init__(self, x, r, v):
    self.x = x # x - location on x axis
    self.r = r # radius
    self.v = v # value == brightness
  
  def update(self):
    self.r = self.r + 1 # spread it out 
    self.v = math.floor(self.v * 0.90) # dim it


def add_note_to_workspace(key, val):
  # pixels[key] = (val, val, val)
  # pixels.show()
  all_blobs.append(Blob(map_key_to_x(key), 1, val))


def thread_function(name):
  while True:

    global rgb

    # print(len(all_blobs))

    # first clear out the rgb array
    rgb = [5] * NUM_OF_PIXELS

    for blob in all_blobs:

      blob.update()

      for x in range(math.floor(blob.x - blob.r), math.ceil(blob.x + blob.r)):

        if (x >= 0 and x < NUM_OF_PIXELS):
          scaler = (1 - abs(blob.x - x) / blob.r) ** 2
          rgb[x] = min(rgb[x] + scaler * blob.v, 255) # never let it go above 255
                                           # this can happen because we add many blobs together

    for idx, val in enumerate(rgb):
      pixels[idx] = (max(math.floor(val), 5), 
                     max(math.floor(val), 5), 
                     max(math.floor(val), 5))

    pixels.show()

    sleep(0.05)
    
    all_blobs[:] = [a for a in all_blobs if a.v > 2]


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

# takes raw key (21 - 108) and returns x coordinate
def map_key_to_x(key):
  return (key - 65) * 2 + 72


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
        val = math.floor(raw) # make dimmer
        add_note_to_workspace(msg.note, val)
      # pixels[msg.note] = (val, val, val) 
    
    elif hasattr(msg, 'control'):
      # pedal pressed
      pedal = msg.control
      handle_pedal(pedal)

    else:
      pring('something new and unknown!')
      print(msg)
