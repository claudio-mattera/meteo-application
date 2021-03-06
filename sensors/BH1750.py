#!/usr/bin/env python3

import time
from Adafruit_I2C import Adafruit_I2C
import logging


# ===========================================================================
# BH1750 Class
# ===========================================================================

class BH1750:
    i2c = None  # type: Adafruit_I2C

    __RAW_TO_LUX_COEFFICIENT = 1.2

    __BH1750_I2CADDR = 0x23
    __BH1750_POWER_DOWN = 0x00
    __BH1750_POWER_ON = 0x01
    __BH1750_RESET = 0x07

    # Operating Modes
    __BH1750_CONTINUOUS_HIGH_RES_MODE = 0x10
    __BH1750_CONTINUOUS_HIGH_RES_MODE_2 = 0x11
    __BH1750_CONTINUOUS_LOW_RES_MODE = 0x13
    __BH1750_ONE_TIME_HIGH_RES_MODE = 0x20
    __BH1750_ONE_TIME_HIGH_RES_MODE_2 = 0x21
    __BH1750_ONE_TIME_LOW_RES_MODE = 0x23

    def __init__(
            self,
            address: int=__BH1750_I2CADDR,
            mode: int=__BH1750_ONE_TIME_HIGH_RES_MODE,
            debug: bool=False
            ) -> None:
        self.i2c = Adafruit_I2C(address)

        self.address = address
        self.debug = debug

        # Make sure the specified mode is in the appropriate range
        VALID_MODES = [
            self.__BH1750_CONTINUOUS_HIGH_RES_MODE,
            self.__BH1750_CONTINUOUS_HIGH_RES_MODE_2,
            self.__BH1750_CONTINUOUS_LOW_RES_MODE,
            self.__BH1750_ONE_TIME_HIGH_RES_MODE,
            self.__BH1750_ONE_TIME_HIGH_RES_MODE_2,
            self.__BH1750_ONE_TIME_LOW_RES_MODE
        ]
        if mode not in VALID_MODES:
            if (self.debug):
                logger = logging.getLogger(__name__)
                logger.debug("Invalid Mode: Using ONE_TIME_HIGH_RES by default")
            self.mode = self.__BH1750_ONE_TIME_HIGH_RES_MODE
        else:
            self.mode = mode

    def read_raw_light(self) -> int:
        data = self.i2c.readList(self.mode, 2)
        if data == -1:
            return -1
        return ((data[0] << 8) + data[1])

    def read_light(self) -> float:
        return self.read_raw_light() / self.__RAW_TO_LUX_COEFFICIENT


if __name__ == '__main__':
    sensor = BH1750(debug=True)
    light = sensor.read_light()
    print("Light: {0}".format(light))
