#!/usr/bin/python

import time
import logging

# ===========================================================================
# DSTH01 Class
# ===========================================================================

I2CADDR = 0x40


class DSTH01:

    __STATUS_REGISTER = 0x00
    __HIGH_DATA_REGISTER = 0x01
    __LOW_DATA_REGISTER = 0x02
    __CONFIG_REGISTER = 0x03

    __READY = 0x00

    __FAST_BIT = 0x20
    __NORMAL_BIT = 0x00
    __HUMIDITY_BIT = 0x00
    __TEMPERATURE_BIT = 0x10

    __POLL_INTERVAL = 0.01

    def __init__(self, address: int=I2CADDR, debug: bool=False) -> None:
        self.address = address
        self.debug = debug

    def readData(self, bit: int, fast: bool=False) -> int:
        "Read data from sensor"
        command = (bit & DSTH01.__FAST_BIT) if fast else (bit & DSTH01.__NORMAL_BIT)

        self.writeRegister(DSTH01.__CONFIG_REGISTER, command)
        time.sleep(DSTH01.__POLL_INTERVAL)

        status = 0x01 & self.readRegister(DSTH01.__STATUS_REGISTER)
        if self.debug:
            print("Status: %d" % status)

        i = 0
        while status != DSTH01.__READY and i < 100:
            time.sleep(DSTH01.__POLL_INTERVAL)
            status = 0x01 & self.readRegister(DSTH01.__STATUS_REGISTER)
            if self.debug:
                print("Status: %d" % status)
            i += 1

        high = self.readRegister(DSTH01.__HIGH_DATA_REGISTER)
        low = self.readRegister(DSTH01.__LOW_DATA_REGISTER)
        return (high << 3) + (low >> 5)

    def readTemperature(self) -> float:
        "Read temperature from sensor"
        temperature = self.readData(DSTH01.__TEMPERATURE_BIT)
        return temperature / 32 - 50

    def readHumidity(self) -> float:
        "Read relative humidity from sensor"
        humidity = self.readData(DSTH01.__HUMIDITY_BIT)
        return humidity / 16 - 24

    def readRegister(self, register: int) -> int:
        raise RuntimeError('Unimplemented')

    def writeRegister(self, register: int, value: int) -> None:
        raise RuntimeError('Unimplemented')


class DSTH01_i2c(DSTH01):
    def __init__(self, address: int=I2CADDR, debug: bool=False) -> None:
        DSTH01.__init__(self, address, debug)

        from Adafruit_I2C import Adafruit_I2C
        self.i2c = Adafruit_I2C(address)

    def readRegister(self, register: int) -> int:
        return self.i2c.readU8(register)

    def writeRegister(self, register: int, value: int) -> None:
        self.i2c.write8(register, value)


class DSTH01_smbus(DSTH01):
    def __init__(self, address: int=I2CADDR, debug: bool=False) -> None:
        DSTH01.__init__(self, address, debug)
        self.address = address

        import smbus
        self.bus = smbus.SMBus(1)

    def readRegister(self, register: int) -> int:
        return self.bus.read_byte_data(self.address, register)

    def writeRegister(self, register: int, value: int) -> None:
        self.bus.write_byte_data(self.address, register, value)


if __name__ == '__main__':
    sensor = DSTH01_i2c(debug=True)

    humidity = sensor.readHumidity()
    print("Humidity: %d%%" % humidity)

    temperature = sensor.readTemperature()
    print("Temperature: %d C" % temperature)
