A two-channel ADC pHat for the Pi-Zero
======================================

This hardware/software project creates a two-channel ADC pHat for the
Pi-Zero. Note that it won't be a *real* pHat, because it is missing
the eeprom, but it uses the formfactor.


Hardware
--------

The circuit uses the following components:

  - Adafruit Perma Proto Bonnet Mini Kit  
    (https://www.adafruit.com/product/3203)
  - MCP3002 two-channel ADC (10 bit) connected to the SPI-bus
  - DIL-8 socket for the MCP3002
  - one green LED
  - one button (start/stop of measurement)
  - I2C mini-OLED display based on the SSD1306-chip
  - two 10k ohm resistors (for the voltage-dividers)
  - two 15k ohm resistors (for the voltage-dividers)
  - one 100 ohm resistor (for the LED)
  - 2x2 female connectors (to attach the measurement probes)

Schematic
---------

The schematic:

![](images/schematic.png "Schematic")

Note the two voltage-dividers used for the two analog channels of the
MCP3002. Since our reference voltage is 3.3V, the voltage-dividers extend
the measurement range to 5.5V.

On a breadboard, this looks somewhat messy:

![](images/breadboard.jpg "breadboard with circuit")

We use the **Perma Proto Bonnet Mini Kit** to create a pluggable pHat for
the Pi-Zero:

![](images/pi-adc-phat.jpg "ADC-pHat")

Wiring is best seen using the Fritzing view of the bonnet:

![](images/fritzing-adc.png "Layout using Fritzing")



Software
--------

The software is implemented in python3. To install the software and it's
dependencies, run

    git clone https://github.com/bablokb/pi-adc-phat.git
    cd pi-adc-phat
    sudo tools/install

The install command will also configure SPI and I2C, if not already done.
Note that you must restart your Pi if SPI or I2C is newly activated.


Configuration
-------------

If you use a different ADC or if you use other GPIOs for buttons and LED,
you have to change the program `/usr/local/sbin/adc_read.py`. The same
holds true if you use different resistors for the voltage-divider.

At the beginning of the program you will find a section `configuration`.
Unless you know what you are doing, only change constants in this section:

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


Usage
-----

Connect jumper-wires to the connectors on the lower right of the
bonnet (the two connectors nearer to the middle are GND, the other two
are channel-0 and channel-1 of the ADC).

The installation-script configures a systemd-service for the reader
program. As soon as the LED is on, you can start and stop the measurement
using the push-button.

To shutdown the system, press the button at least for two seconds.

To disable this system-service at startup execute the command

    sudo systemctl disable pi-adc-phat.service

Now you can start the reader-program manually (e.g. from a ssh-shell):

    /usr/local/sbin/adc_read.py [filename|-]

If you pass a filename (or "-" for standard-output) the
measurements will also be appended to the argument file (or dumped to
the console in the latter case).


LED-States
----------

The LED uses the following states:

| State | Description           | Action on button pressed |
|-------|-----------------------|--------------------------|
| On    | ready                 | starts measurement       |
| blink | measurement is active | stops  measurement       |

