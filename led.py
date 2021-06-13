# to run script: `sudo python3 led.py`
#
# written by Boris Yakubchik
#
# Edit these:

NUM_OF_LED = 144
BRIGHTNESS = 0.2 # maximum 1 -- best when 1/n is an integer
PIANO_STARTS_WITH = 'B2'

# =========================================================
# DO NOT EDIT BELOW

from time import sleep
from time import time
import math
import threading
import colorsys

import board
import neopixel

import mido

import keyboard

pixels = neopixel.NeoPixel(board.D18, NUM_OF_LED, brightness=BRIGHTNESS, auto_write=False)

devices = mido.get_input_names()
piano = []

for device in devices:
  if device.startswith(PIANO_STARTS_WITH):
    piano.append(device)

if len(piano) == 0:
  print('\nIs the piano connected / turned on?\n')
  quit()
else:
  print('Listening for MIDI from', piano[0])


# =======================================================================
# Variables

# array for all BLOBS
all_blobs = {}

min_bright = math.ceil(1 / BRIGHTNESS)

# array for pixel color computation - to be written to the LED strip later
rgb_r = [1] * NUM_OF_LED # fill all of them with 1
rgb_g = [1] * NUM_OF_LED # fill all of them with 1
rgb_b = [1] * NUM_OF_LED # fill all of them with 1

# to throttle keyboard events
throttle_left = 0
throttle_right = 0
throttle_f12 = 0

color_bg = [1, 1, 2]
color_key = [2, 1, 1]

# each Blob is a key pressed that evolves over time via its `update` method
class Blob:
  def __init__(self, x, r, v, s):
    self.x = x # x - location on x axis
    self.r = r # radius
    self.v = v # value == brightness
    self.s = s # status: `down`, `legato`, or `decay`

  def update(self):
    if self.s == 'down' or self.s == 'legato':
      self.r = min(self.r + 1, 5)
      self.v = math.floor(self.v * 0.98)
    else:
      self.r = self.r + 1
      self.v = math.floor(self.v * 0.75) # dim it


def add_note_to_workspace(key, velocity):
  all_blobs[key] = Blob(map_key_to_x(key), 1, velocity, 'down')


hue1 = 0.0
hue2 = 0.09


def update_colors():
  global color_bg
  global color_key
  global hue1
  global hue2
  global all_blobs

  hue1 = hue1 + 0.0005
  if hue1 > 1:
    hue1 = 0

  hue2 = hue2 + 0.0005
  if hue2 > 1:
    hue2 = 0

  # bg
  (r1, g1, b1) = colorsys.hsv_to_rgb(hue1, 0.65, 0.1)
  # keys
  fudge = min(len(all_blobs) * 0.02, 0.2)
  (r2, g2, b2) = colorsys.hsv_to_rgb(hue2, 0.8 + fudge, 0.1)

  # print(round(r * 200, 2), 
  #       round(g * 200, 2), 
  #       round(b * 200, 2))

  color_bg[0] = r1 * 150
  color_bg[1] = g1 * 150
  color_bg[2] = b1 * 150

  color_key[0] = r2 * 40
  color_key[1] = g2 * 40
  color_key[2] = b2 * 40


def thread_function(name):
  while True:

    global rgb_r
    global rgb_g
    global rgb_b

    update_colors()

    # print(len(all_blobs)) # to check that blobs disappear after some time

    rgb_r = [color_bg[0]] * NUM_OF_LED # reset array to min
    rgb_g = [color_bg[1]] * NUM_OF_LED # reset array to min
    rgb_b = [color_bg[2]] * NUM_OF_LED # reset array to min

    for blob_key in all_blobs:

      blob = all_blobs[blob_key]

      blob.update()

      for x in range(math.floor(blob.x - blob.r), math.ceil(blob.x + blob.r)):

        if (x >= 0 and x < NUM_OF_LED):
          scaler = (1 - abs(blob.x - x) / blob.r) ** 2
          # never let it go above 255
          # this can happen because we add many blobs together
          rgb_r[x] = min(rgb_r[x] + scaler * blob.v * color_key[0], 255) 
          rgb_g[x] = min(rgb_g[x] + scaler * blob.v * color_key[1], 255) 
          rgb_b[x] = min(rgb_b[x] + scaler * blob.v * color_key[2], 255) 

    for x in range(0, NUM_OF_LED):
      # make sure these are integers
      pixels[x] = (math.floor(rgb_r[x]), 
                   math.floor(rgb_g[x]), 
                   math.floor(rgb_b[x]))

    pixels.show()

    sleep(0.05) # ~20 FPS

    to_delete = []

    # only keep blobs that are above brightness of 1
    for blob_key in all_blobs:
      if all_blobs[blob_key].v < 2:
        to_delete.append(blob_key)

    for key in to_delete:
      all_blobs.pop(key)


thread = threading.Thread(target=thread_function, args=(1,))
thread.start()

legato_pedal = 0 # 0 - not pressed, 1 - pressed


def unlegato_all_keys():
  for key in all_blobs:
    if all_blobs[key].s == 'legato':
      all_blobs[key].s = 'decay'


def handle_pedal(pedal, value):
  global legato_pedal
  if pedal == 67:
    throttle_key('left')
  elif pedal == 66:
    throttle_key('right')
  elif pedal == 64:
    if legato_pedal == 0 and value != 0:
      legato_pedal = 1
      print('legato ON')
    if value == 0:
      legato_pedal = 0
      print('legato OFF')
      unlegato_all_keys()

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
  # 65 = center between 21 and 108
  # 72 = NUM_OF_LEDS / 2 + fudge factor
  return (key - 65) * 2 + 72


with mido.open_input(piano[0]) as inport:
  for msg in inport:
    # print(msg)
    if hasattr(msg, 'velocity'):
      # print(msg.velocity)
      if msg.velocity == 64: # represents key-up velocity
        if msg.note in all_blobs: # key may have decayed and been removed already
          if legato_pedal == 1:
            all_blobs[msg.note].s = 'legato'
          else:
            all_blobs[msg.note].s = 'decay'
      else:
        add_note_to_workspace(msg.note, msg.velocity)

    elif hasattr(msg, 'control'):
      # pedal numbers 64, 65, 66
      handle_pedal(msg.control, msg.value)

    else:
      print('something new and unknown!')
      print(msg)
