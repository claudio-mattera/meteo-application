#!/usr/bin/python

import smbus
import logging
import typing

# ===========================================================================
# Adafruit_I2C Class
# ===========================================================================

class Adafruit_I2C(object):

  @staticmethod
  def getPiRevision() -> int:
    "Gets the version number of the Raspberry Pi board"
    # Courtesy quick2wire-python-api
    # https://github.com/quick2wire/quick2wire-python-api
    # Updated revision info from: http://elinux.org/RPi_HardwareHistory#Board_Revision_History
    try:
      with open('/proc/cpuinfo','r') as f:
        for line in f:
          if line.startswith('Revision'):
            return 1 if line.rstrip()[-1] in ['2','3'] else 2
    except:
      return 0

  @staticmethod
  def getPiI2CBusNumber() -> int:
    # Gets the I2C bus number /dev/i2c#
    return 1 if Adafruit_I2C.getPiRevision() > 1 else 0

  def __init__(self, address: int, busnum: int=-1, debug: bool=False) -> None:
    self.address = address
    # By default, the correct I2C bus is auto-detected using /proc/cpuinfo
    # Alternatively, you can hard-code the bus version below:
    # self.bus = smbus.SMBus(0); # Force I2C0 (early 256MB Pi's)
    # self.bus = smbus.SMBus(1); # Force I2C1 (512MB Pi's)
    self.bus = smbus.SMBus(busnum if busnum >= 0 else Adafruit_I2C.getPiI2CBusNumber())
    self.debug = debug

  def reverseByteOrder(self, data: int) -> int:
    "Reverses the byte order of an int (16-bit) or long (32-bit) value"
    # Courtesy Vishal Sapre
    byteCount = len(hex(data)[2:].replace('L','')[::2])
    val       = 0
    for i in range(byteCount):
      val    = (val << 8) | (data & 0xff)
      data >>= 8
    return val

  def errMsg(self) -> typing.Text:
    msg = "Error accessing 0x%02X: Check your I2C address" % self.address
    logger = logging.getLogger(__name__)
    logger.error(msg)
    return msg

  def write8(self, reg: int, value: int) -> None:
    "Writes an 8-bit value to the specified register/address"
    try:
      self.bus.write_byte_data(self.address, reg, value)
      if self.debug:
        logger = logging.getLogger(__name__)
        logger.debug("I2C: Wrote 0x%02X to register 0x%02X" % (value, reg))
    except IOError as err:
      msg = self.errMsg()
      raise RuntimeError(msg)

  def write16(self, reg: int, value: int) -> None:
    "Writes a 16-bit value to the specified register/address pair"
    try:
      self.bus.write_word_data(self.address, reg, value)
      if self.debug:
        logger = logging.getLogger(__name__)
        logger.debug("I2C: Wrote 0x%02X to register pair 0x%02X,0x%02X" %
         (value, reg, reg+1))
    except IOError as err:
      msg = self.errMsg()
      raise RuntimeError(msg)

  def writeRaw8(self, value: int) -> None:
    "Writes an 8-bit value on the bus"
    try:
      self.bus.write_byte(self.address, value)
      if self.debug:
        logger = logging.getLogger(__name__)
        logger.debug("I2C: Wrote 0x%02X" % value)
    except IOError as err:
      msg = self.errMsg()
      raise RuntimeError(msg)

  def writeList(self, reg: int, ls: typing.List[int]) -> None:
    "Writes an array of bytes using I2C format"
    try:
      if self.debug:
        logger = logging.getLogger(__name__)
        logger.debug("I2C: Writing list to register 0x%02X:" % reg)
        logger.debug(','.join(map(str, ls)))
      self.bus.write_i2c_block_data(self.address, reg, ls)
    except IOError as err:
      msg = self.errMsg()
      raise RuntimeError(msg)

  def readList(self, reg: int, length: int) -> typing.List[int]:
    "Read a list of bytes from the I2C device"
    try:
      results = self.bus.read_i2c_block_data(self.address, reg, length)
      if self.debug:
        logger = logging.getLogger(__name__)
        logger.debug("I2C: Device 0x%02X returned the following from reg 0x%02X" %
         (self.address, reg))
        logger.debug(results)
      return results
    except IOError as err:
      msg = self.errMsg()
      raise RuntimeError(msg)

  def readU8(self, reg: int) -> int:
    "Read an unsigned byte from the I2C device"
    try:
      result = self.bus.read_byte_data(self.address, reg)
      if self.debug:
        logger = logging.getLogger(__name__)
        logger.debug("I2C: Device 0x%02X returned 0x%02X from reg 0x%02X" %
         (self.address, result & 0xFF, reg))
      return result
    except IOError as err:
      msg = self.errMsg()
      raise RuntimeError(msg)

  def readS8(self, reg: int) -> int:
    "Reads a signed byte from the I2C device"
    try:
      result = self.bus.read_byte_data(self.address, reg)
      if result > 127: result -= 256
      if self.debug:
        logger = logging.getLogger(__name__)
        logger.debug("I2C: Device 0x%02X returned 0x%02X from reg 0x%02X" %
         (self.address, result & 0xFF, reg))
      return result
    except IOError as err:
      msg = self.errMsg()
      raise RuntimeError(msg)

  def readU16(self, reg: int, little_endian: bool=True) -> int:
    "Reads an unsigned 16-bit value from the I2C device"
    try:
      result = self.bus.read_word_data(self.address,reg)
      # Swap bytes if using big endian because read_word_data assumes little
      # endian on ARM (little endian) systems.
      if not little_endian:
        result = ((result << 8) & 0xFF00) + (result >> 8)
      if (self.debug):
        logger = logging.getLogger(__name__)
        logger.debug("I2C: Device 0x%02X returned 0x%04X from reg 0x%02X" % (self.address, result & 0xFFFF, reg))
      return result
    except IOError as err:
      msg = self.errMsg()
      raise RuntimeError(msg)

  def readS16(self, reg: int, little_endian: bool=True) -> int:
    "Reads a signed 16-bit value from the I2C device"
    try:
      result = self.readU16(reg,little_endian)
      if result > 32767: result -= 65536
      return result
    except IOError as err:
      msg = self.errMsg()
      raise RuntimeError(msg)

if __name__ == '__main__':
  try:
    bus = Adafruit_I2C(address=0)
    logger = logging.getLogger(__name__)
    logger.debug("Default I2C bus is accessible")
  except:
    logger.error("Error accessing default I2C bus")
