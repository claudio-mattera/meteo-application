#!/usr/bin/python3

import time
from Adafruit_I2C import Adafruit_I2C
import logging
from array import array

# ===========================================================================
# HTU21D Class
# ===========================================================================


class RawI2C(object):

    I2C_SLAVE = 0x0703

    def __init__(self, device: int, bus: int) -> None:
        import io
        import fcntl

        self.fr = io.open("/dev/i2c-"+str(bus), "rb", buffering=0)
        self.fw = io.open("/dev/i2c-"+str(bus), "wb", buffering=0)

        # set device address
        fcntl.ioctl(self.fr, self.I2C_SLAVE, device)
        fcntl.ioctl(self.fw, self.I2C_SLAVE, device)

    def write(self, bs: bytes) -> None:
        self.fw.write(bs)

    def read(self, bs: int) -> bytes:
        return self.fr.read(bs)

    def close(self) -> None:
        self.fw.close()
        self.fr.close()


class HTU21D :
    i2c = None  # type: RawI2C

    __HTU21D_I2CADDR    = 0x40

    __HTU21D_READ_TEMP_HOLD = b"\xE3"
    __HTU21D_READ_HUM_HOLD = b"\xE5"
    __HTU21D_READ_TEMP_NOHOLD = b"\xF3"
    __HTU21D_READ_HUM_NOHOLD = b"\xF5"
    __HTU21D_WRITE_USER_REG = b"\xE6"
    __HTU21D_READ_USER_REG = b"\xE7"
    __HTU21D_SOFT_RESET= b"\xFE"
    MEASUREMENT_DELAY = .1

    def __init__(self, address: int=__HTU21D_I2CADDR, debug: bool=False) -> None:
        self.i2c = RawI2C(address, 1)

        self.address = address
        self.debug = debug

        self.i2c.write(self.__HTU21D_SOFT_RESET)
        time.sleep(0.1)

    def read_data(self, command: bytes) -> int:
        self.i2c.write(command)
        time.sleep(self.MEASUREMENT_DELAY)
        data = self.i2c.read(3)
        buffer = array('B', data)
        valid = self.crc8check(buffer)
        if not valid:
            return -1
        return (buffer[0] << 8 | buffer[1]) & 0xFFFC

    def read_temperature(self) -> float:
        t = self.read_data(self.__HTU21D_READ_TEMP_HOLD)
        return -46.85 + 175.72 * t / 2**16

    def read_humidity(self) -> float:
        h = self.read_data(self.__HTU21D_READ_HUM_HOLD)
        return -6 + 125 * h / 2 ** 16

    def read_dew_point(self) -> float:
        from math import log10
        A = 8.1332
        B = 1762.39
        C = 235.66
        rh = self.read_humidity()
        t = self.read_temperature()
        pp = 10 ** (A - B / (t + C))
        denom = log10(rh * pp / 100.) - A
        return - (B / denom + C)

    def crc8check(self, value: array) -> bool:
        # From https://www.raspberrypi.org/forums/viewtopic.php?f=44&t=76688
        # Ported from Sparkfun Arduino HTU21D Library: https://github.com/sparkfun/HTU21D_Breakout
        remainder = ((value[0] << 8) + value[1]) << 8
        remainder |= value[2]

        # POLYNOMIAL = 0x0131 = x^8 + x^5 + x^4 + 1
        # divsor = 0x988000 is the 0x0131 polynomial shifted to farthest left of three bytes
        divsor = 0x988000

        for i in range(0, 16):
            if remainder & 1 << (23 - i):
                remainder ^= divsor
            divsor = divsor >> 1

        return remainder == 0


if __name__ == '__main__':
    s = HTU21D()
    t = s.read_temperature()
    print("Temperature: %.1f C" % t)
    h = s.read_humidity()
    print("Humidity: %.1f %%" % h)
    d = s.read_dew_point()
    print("Dew point: %.1f C" % d)
