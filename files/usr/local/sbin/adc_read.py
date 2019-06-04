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

import smbus, spidev, os, time, datetime

from lib_oled96 import ssd1306
from PIL        import ImageFont

# --- configuration   --------------------------------------------------------

INTERVAL  = 1      # sample interval in seconds
FONT_NAME = '/usr/share/fonts/truetype/freefont/FreeMono.ttf'
FONT_SIZE = 30
ADC="MCP3002"      # ADC-type, must be one of the types defined below
GPIO_BTN  = 16     # GPIO connected to button (BCM-numbering)
GPIO_LED  = 12     # GPIO connected to LED    (BCM-numbering)
U_FAC = 5.0/3.0    # this depends on the measurement-circuit (voltage-devider)

# --- constants (don't change)   ---------------------------------------------

ADC_VALUES = {
  'MCP3002': { 'CMD_BYTES': [[0,104,0],[0,120,0]], 'RESOLUTION': 10},
  'MCP3008': { 'CMD_BYTES': [[1,128,0],[1,144,0]], 'RESOLUTION': 10},
  'MCP3202': { 'CMD_BYTES': [[1,160,0],[1,224,0]], 'RESOLUTION': 12}
}
ADC_BYTES  = ADC_VALUES[ADC]['CMD_BYTES']
ADC_RES    = 2**ADC_VALUES[ADC]['RESOLUTION']
ADC_MASK   = 2**(ADC_VALUES[ADC]['RESOLUTION']-8) - 1

U_REF = 3.3
U_RES = U_REF/ADC_RES

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

# --- read SPI-bus   ---------------------------------------------------------
                        
def read_spi(channel):
  """ read spi-channel """

  global spi

  cmd_bytes = list(ADC_BYTES[channel])       # use copy, since
  data      = spi.xfer(cmd_bytes)            # xfer changes the data
  return ((data[1]&ADC_MASK) << 8) + data[2]

# --- collect-data   ---------------------------------------------------------

def collect_data():
  """ collect data """

  global spi

  while True:
    u0 = read_spi(0)*U_RES*U_FAC
    u1 = read_spi(1)*U_RES*U_FAC
    process_data(u0,u1)
    display_data(u0,u1)
    time.sleep(INTERVAL)

# --- process data   ---------------------------------------------------------

def process_data(u0,u1):
  """ process data """

  print("0: {0:2.1f}V\n1: {1:2.1f}V\n".format(u0,u1))

# --- display data   ---------------------------------------------------------

def display_data(u0,u1):
  """ display data on mini-oled """
  
  global oled, font

  oled.canvas.rectangle((0, 0, oled.width, oled.height), outline=0, fill=0)
  y_off = 0
  oled.canvas.text((0,y_off),"0: {0:2.1f}V".format(u0),font=font,fill=1)
  y_off += 0.9*FONT_SIZE
  oled.canvas.text((0,y_off),"1: {0:2.1f}V".format(u1),font=font,fill=1)
  oled.display()

# --- main program   ---------------------------------------------------------

if __name__ == '__main__':

  init_spi()
  init_oled()
  collect_data()
