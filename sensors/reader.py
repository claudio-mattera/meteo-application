#!/usr/bin/python

from Adafruit_BMP085 import BMP085
from BH1750 import BH1750
from HTU21D import HTU21D
from Wifi import Wifi

class PressureReader(object):

    ULTRALOWPOWER_MODE = 0
    STANDARD_MODE      = 1
    HIRES_MODE         = 2
    ULTRAHIRES_MODE    = 3

    def __init__(self, mode=STANDARD_MODE, address=0x77):
        self.bmp = BMP085(address, mode)

    def name(self):
        return 'pressure'

    def fields(self):
        return ['Temperature', 'Pressure', 'Altitude']

    def readValues(self):
        temperature = self.bmp.readTemperature()
        pressure = self.bmp.readPressure()

        # To calculate altitude based on an estimated mean sea level pressure
        # (1013.25 hPa) call the function as follows, but this won't be very
        # accurate.

        # To specify a more accurate altitude, enter the correct mean sea level
        # pressure level.  For example, if the current pressure level is 1023.50
        # hPa enter 102350 since we include two decimal places in the integer
        # value altitude = bmp.readAltitude(102350).
        altitude = self.bmp.readAltitude()

        return {
            'Temperature': temperature,
            'Pressure': pressure,
            'Altitude': altitude
        }


class HumidityReader(object):

    def __init__(self):
        self.htu = HTU21D()

    def name(self):
        return 'humidity'

    def fields(self):
        return ['Temperature', 'Humidity']

    def readValues(self):
        temperature = self.htu.read_temperature()
        humidity = self.htu.read_humidity()

        return {
            'Temperature': temperature,
            'Humidity': humidity
        }


class WindReader(object):

    def __init__(self):
        pass

    def name(self):
        return 'wind'

    def fields(self):
        return ['Speed', 'Direction']

    def readValues(self):
        speed = None
        direction = None

        return {
            'Speed': speed,
            'Direction': direction
        }


class LightReader(object):

    CONTINUOUS_HIGH_RES_MODE   = 0x10
    CONTINUOUS_HIGH_RES_MODE_2 = 0x11
    CONTINUOUS_LOW_RES_MODE    = 0x13
    ONE_TIME_HIGH_RES_MODE     = 0x20
    ONE_TIME_HIGH_RES_MODE_2   = 0x21
    ONE_TIME_LOW_RES_MODE      = 0x23

    def __init__(self, mode=ONE_TIME_HIGH_RES_MODE_2, address=0x23):
        self.bh1750 = BH1750(address, mode)

    def name(self):
        return 'light'

    def fields(self):
        return ['Infrared', 'Visible', 'Ultraviolet']

    def readValues(self):
        infrared = None
        visible = self.bh1750.readLight()
        ultraviolet = None

        return {
            'Infrared': infrared,
            'Visible': visible,
            'Ultraviolet': ultraviolet
        }

class InternalReader(object):

    def __init__(self):
        pass

    def name(self):
        return 'internal'

    def fields(self):
        return ['Temperature']

    def readValues(self):
        import subprocess
        args = ['/opt/vc/bin/vcgencmd', 'measure_temp']
        output = subprocess.check_output(args)
        # Output has form "temp=XX.X'C\n"
        temperature = float(output[5:-3])

        return {
            'Temperature': temperature
        }

class PresenceReader(object):

    def __init__(self, known_devices):
        self.wifi = Wifi(known_devices)

    def name(self):
        return 'presence'

    def fields(self):
        return ['Count']

    def readValues(self):
        presence_count = self.wifi.readPresenceCount()
        return {
            'Count': presence_count
        }
