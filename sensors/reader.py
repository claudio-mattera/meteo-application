#!/usr/bin/python

import typing

from Adafruit_BMP085 import BMP085
from BH1750 import BH1750
from HTU21D import HTU21D
from Wifi import Wifi

class PressureReader(object):

    ULTRALOWPOWER_MODE = 0
    STANDARD_MODE      = 1
    HIRES_MODE         = 2
    ULTRAHIRES_MODE    = 3

    def __init__(self, mode: int=STANDARD_MODE, address: int=0x77) -> None:
        self.bmp = BMP085(address, mode)

    def name(self) -> typing.Text:
        return 'pressure'

    def fields(self) -> typing.List[typing.Text]:
        return ['Temperature', 'Pressure', 'Altitude']

    def readValues(self) -> typing.Dict[typing.Text, typing.Any]:
        temperature = self.bmp.read_temperature()
        pressure = self.bmp.read_pressure()

        # To calculate altitude based on an estimated mean sea level pressure
        # (1013.25 hPa) call the function as follows, but this won't be very
        # accurate.

        # To specify a more accurate altitude, enter the correct mean sea level
        # pressure level.  For example, if the current pressure level is 1023.50
        # hPa enter 102350 since we include two decimal places in the integer
        # value altitude = bmp.readAltitude(102350).
        altitude = self.bmp.read_altitude()

        return {
            'Temperature': temperature,
            'Pressure': pressure,
            'Altitude': altitude
        }


class HumidityReader(object):

    def __init__(self) -> None:
        self.htu = HTU21D()

    def name(self) -> typing.Text:
        return 'humidity'

    def fields(self) -> typing.List[typing.Text]:
        return ['Temperature', 'Humidity']

    def readValues(self) -> typing.Dict[typing.Text, typing.Any]:
        temperature = self.htu.read_temperature()
        humidity = self.htu.read_humidity()

        return {
            'Temperature': temperature,
            'Humidity': humidity
        }


class WindReader(object):

    def __init__(self) -> None:
        pass

    def name(self) -> typing.Text:
        return 'wind'

    def fields(self) -> typing.List[typing.Text]:
        return ['Speed', 'Direction']

    def readValues(self) -> typing.Dict[typing.Text, typing.Any]:
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

    def __init__(self, mode: int=ONE_TIME_HIGH_RES_MODE_2, address: int=0x23) -> None:
        self.bh1750 = BH1750(address, mode)

    def name(self) -> typing.Text:
        return 'light'

    def fields(self) -> typing.List[typing.Text]:
        return ['Infrared', 'Visible', 'Ultraviolet']

    def readValues(self) -> typing.Dict[typing.Text, typing.Any]:
        infrared = None
        visible = self.bh1750.read_light()
        ultraviolet = None

        return {
            'Infrared': infrared,
            'Visible': visible,
            'Ultraviolet': ultraviolet
        }

class InternalReader(object):

    def __init__(self) -> None:
        pass

    def name(self) -> typing.Text:
        return 'internal'

    def fields(self) -> typing.List[typing.Text]:
        return ['Temperature']

    def readValues(self) -> typing.Dict[typing.Text, typing.Any]:
        import subprocess
        args = ['/opt/vc/bin/vcgencmd', 'measure_temp']
        output = subprocess.check_output(args)
        # Output has form "temp=XX.X'C\n"
        temperature = float(output[5:-3])

        return {
            'Temperature': temperature
        }

class PresenceReader(object):

    def __init__(self, known_devices: typing.Dict[typing.Text, typing.Any]) -> None:
        self.wifi = Wifi(known_devices)

    def name(self) -> typing.Text:
        return 'presence'

    def fields(self) -> typing.List[typing.Text]:
        return ['Count']

    def readValues(self) -> typing.Dict[typing.Text, typing.Any]:
        presence_count = self.wifi.read_presence_count()
        return {
            'Count': presence_count
        }
