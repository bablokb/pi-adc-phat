#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Read two-channel ADC and display values on a small OLED-display.
#
# You need to configure this script to your needs:
#   - ADC type
#   - GPIO for start/stop button
#   - GPIO for status-LED
#
# Author: Bernhard Bablok
# License: GPL3
#
# Website: https://github.com/bablokb/pi-adc-phat
#
# ----------------------------------------------------------------------------

import smbus, spidev, sys, threading, signal, datetime, time, os

from lib_oled96 import ssd1306
from PIL        import ImageFont
import RPi.GPIO as GPIO

# --- configuration   --------------------------------------------------------

DELAY    = 0.3     # additional delay inbetween samples (must be positive)
                   # Pi-Zero does about 4.5 samples/sec maximum
ADC = "MCP3002"    # ADC-type, must be one of the types defined below
GPIO_BTN = 20      # GPIO connected to button (BCM-numbering)
GPIO_LED = 12      # GPIO connected to LED    (BCM-numbering)
LED_FREQ = 1       # blink frequency of LED
LED_DC   = 50      # duty-cycle of LED (brightness)
U_REF    = 3.3     # reference-voltage
U_FAC    = 5.0/3.0 # this depends on the measurement-circuit (voltage-divider)

# --- constants (don't change)   ---------------------------------------------

FONT_NAME = '/usr/share/fonts/truetype/freefont/FreeMono.ttf'
FONT_SIZE = 25

ADC_VALUES = {
  'MCP3002': { 'CMD_BYTES': [[0,104,0],[0,120,0]], 'RESOLUTION': 10},
  'MCP3008': { 'CMD_BYTES': [[1,128,0],[1,144,0]], 'RESOLUTION': 10},
  'MCP3202': { 'CMD_BYTES': [[1,160,0],[1,224,0]], 'RESOLUTION': 12}
}
ADC_BYTES  = ADC_VALUES[ADC]['CMD_BYTES']
ADC_RES    = 2**ADC_VALUES[ADC]['RESOLUTION']
ADC_MASK   = 2**(ADC_VALUES[ADC]['RESOLUTION']-8) - 1

U_RES = U_REF/ADC_RES

LED_FREQ_ON = 100   # blink-frequency for always on

# --- initialize SPI-bus   ---------------------------------------------------

def init_spi():
  """ initialize SPI bus """

  global spi

  spi = spidev.SpiDev()
  spi.open(0,0)
  spi.max_speed_hz = 50000

# --- initialize oled-display   ----------------------------------------------

def init_oled():
  """ initialize oled-disply """

  global oled, font

  i2cbus = smbus.SMBus(1)
  oled   = ssd1306(i2cbus)
  font   = ImageFont.truetype(FONT_NAME,FONT_SIZE)
  oled.cls()

# --- initialize GPIOs   -----------------------------------------------------

def init_gpios():
  """ initialize GPIOs """

  global led

  GPIO.setmode(GPIO.BCM)
  GPIO.setup(GPIO_LED, GPIO.OUT)
  GPIO.setup(GPIO_BTN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
  GPIO.add_event_detect(GPIO_BTN, GPIO.FALLING,
                        callback=start_stop, bouncetime=1000)
  led = GPIO.PWM(GPIO_LED, LED_FREQ_ON)
  led.start(LED_DC)

# --- read SPI-bus   ---------------------------------------------------------
                        
def read_spi(channel):
  """ read spi-channel """

  global spi

  cmd_bytes = list(ADC_BYTES[channel])       # use copy, since
  data      = spi.xfer(cmd_bytes)            # xfer changes the data
  return ((data[1]&ADC_MASK) << 8) + data[2]

# --- start/stop of data collection   ----------------------------------------

def start_stop(btn):
  """ start/stop of data collection (button callback) """

  global active, event, oled, lock, led

  if not lock.acquire(btn == 0):
    return

  # check for long press
  if btn != 0:
    start_time = time.time()
    while GPIO.input(btn) == 0:       # Wait for the button up
      pass
    buttonTime = time.time() - start_time
    if buttonTime > 2:
      if active:
        event.set()
        oled.cls()
      lock.release()
      os.system("halt -p")
      return

  if active or btn == 0:
    led.ChangeFrequency(LED_FREQ_ON)  # stop blinking LED
    event.set()                       # signal stop event
    oled.cls()                        # clear display
  else:
    led.ChangeFrequency(LED_FREQ)     # change to blink
    event.clear()                     # reset stop event
    threading.Thread(target=collect_data).start()

  active = not active
  lock.release()

# --- collect-data   ---------------------------------------------------------

def collect_data():
  """ collect data """

  global spi, event, out_file

  f = None
  if out_file:
    if out_file == "-":
      f = sys.stdout
    else:
      try:
        f = open(out_file,"a")
      except:
        out_file = None

  while True:
    if out_file and f:
      now = datetime.datetime.now()
    u0 = read_spi(0)*U_RES*U_FAC
    u1 = read_spi(1)*U_RES*U_FAC
    if out_file and f:
      save_data(f,now,u0,u1)
    display_data(u0,u1)
    if event.wait(DELAY):
      break

  if f and out_file != "-":
    try:
      f.close()
    except:
      pass

# --- process data   ---------------------------------------------------------

def save_data(f,now,u0,u1):
  """ process data """

  line = "{0},{1:2.1f},{2:2.1f}\n".format(now.strftime("%s.%f"),u0,u1)
  try:
    f.write(line)
    f.flush()
  except:
    f = none

# --- display data   ---------------------------------------------------------

def display_data(u0,u1):
  """ display data on mini-oled """
  
  global oled, font

  oled.canvas.rectangle((0, 0, oled.width, oled.height), outline=0, fill=0)
  y_off = 0
  oled.canvas.text((0,y_off),"0: {0:3.2f}V".format(u0),font=font,fill=1)
  y_off += 0.9*FONT_SIZE
  oled.canvas.text((0,y_off),"1: {0:3.2f}V".format(u1),font=font,fill=1)
  oled.display()

# --- signal handler   -------------------------------------------------------

def signal_handler(_signo, _stack_frame):
  """ signal-handler to cleanup threads and environment """

  start_stop(0)
  GPIO.cleanup()
  sys.exit(0)

# --- main program   ---------------------------------------------------------

if __name__ == '__main__':

  # setup signal handlers
  signal.signal(signal.SIGTERM, signal_handler)
  signal.signal(signal.SIGINT, signal_handler)

  # setup multithreading
  active = False
  event  = threading.Event()
  lock   = threading.Lock()

  # check argument
  out_file = None
  if len(sys.argv) > 1:
    out_file = sys.argv[1]

  # initialize hardware
  init_spi()
  init_oled()
  init_gpios()

  # main loop (do nothing, events handled by button-callback)
  signal.pause()
