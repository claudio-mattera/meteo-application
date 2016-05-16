#!/usr/bin/python3

import subprocess
import re


class Wifi:

    def __init__(self, known_devices):
        if isinstance(known_devices, dict):
            self.known_devices = known_devices
        elif isinstance(known_devices, str):
            self.known_devices = self._load_dict_from_file(known_devices)
        else:
            raise RuntimeError('"known_devices" must be a dict or a filename')
        self.pattern = re.compile(
            '(?P<ip>\\d+\\.\\d+\\.\\d+\\.\\d+)\\s+'
            '(?P<mac>\\w+:\\w+:\\w+:\\w+:\\w+:\\w+)\\s*\n')

    def read_active_nics(self):
        cmd = ['arp-scan', '--interface=wlan0', '--localnet', '--quiet']
        outcome = subprocess.check_output(cmd)
        string = outcome.decode('utf-8')
        matches = self.pattern.findall(string)
        return [mac.lower() for (ip, mac) in matches]

    def read_active_devices(self):
        active_nics = self.read_active_nics()
        for mac in active_nics:
            if mac not in self.known_devices:
                new_value = 1 + max(self.known_devices.values())
                self.known_devices[mac] = new_value

        assert all(mac in self.known_devices for mac in active_nics)

        return set(self.known_devices[mac] for mac in active_nics)

    def read_presence_count(self):
        active_devices = self.read_active_devices()
        return len(active_devices - set([0]))

    def _load_dict_from_file(self, filename):
        import ast
        with open(filename, 'r') as file:
            content = file.read()
            return ast.literal_eval(content)

if __name__ == '__main__':
    import sys
    sensor = Wifi(sys.argv[1])

    active_nics = sensor.read_active_nics()
    print("Hosts: %s" % ', '.join(active_nics))

    active_devices = sensor.read_active_devices()
    print("Known hosts: %s"
          % ', '.join(["%s" % device for device in active_devices]))

    presence_count = sensor.read_presence_count()
    print("Presence count: %d" % presence_count)
