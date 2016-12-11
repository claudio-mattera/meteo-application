#!/usr/bin/python3

import subprocess
import re
import typing


PATTERN = re.compile(
    '(?P<ip>\\d+\\.\\d+\\.\\d+\\.\\d+)\\s+'
    '(?P<mac>\\w+:\\w+:\\w+:\\w+:\\w+:\\w+)\\s*\n')


class Wifi:

    def __init__(self, known_devices: typing.Dict) -> None:
        self.known_devices = known_devices['known_devices']

    def read_active_nics(self) -> typing.List[typing.Text]:
        cmd = ['arp-scan', '--interface=wlan0', '--localnet', '--quiet']
        outcome = subprocess.check_output(cmd)
        string = outcome.decode('utf-8')
        matches = PATTERN.findall(string)
        return [mac.lower() for (ip, mac) in matches]

    def read_active_devices(self) -> typing.Set[typing.Text]:
        active_nics = self.read_active_nics()
        for mac in active_nics:
            if mac not in self.known_devices:
                new_value = 1 + max(self.known_devices.values())
                self.known_devices[mac] = new_value

        assert all(mac in self.known_devices for mac in active_nics)

        return set(self.known_devices[mac] for mac in active_nics)

    def read_presence_count(self) -> int:
        active_devices = self.read_active_devices()
        return len(active_devices - set([0]))
