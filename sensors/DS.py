#!/usr/bin/env python3

import re

FIRST_LINE_PATTERN = re.compile(r"^(\w\w )*: crc=(\w+) (?P<status>\w+)$")
SECOND_LINE_PATTERN = re.compile(r"^(\w\w )*t=(?P<temperature>-?\d+)$")


class DS(object):

    def __init__(self):
        pass

    def parse_temperature(self, string):
        m = FIRST_LINE_PATTERN.match(string[0])
        if m and m.group('status') == 'YES':
            m = SECOND_LINE_PATTERN.match(string[1])
            if m:
                temperature = int(m.group('temperature'))
                if temperature < 85000:
                    return 1e-3 * temperature
        return None

    def read_file(self, id):
        filename = "/sys/bus/w1/devices/%s/w1_slave" % id
        with open(filename, 'r') as file:
            return file.readlines()

    def read_temperature(self, id):
        return self.parse_temperature(self.read_file(id))
