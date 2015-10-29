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

    def readActiveNics(self):
        cmd = ['arp-scan', '--interface=wlan0', '--localnet', '--quiet']
        outcome = subprocess.check_output(cmd)
        string = outcome.decode('utf-8')
        matches = self.pattern.findall(string)
        return [mac.lower() for (ip, mac) in matches]

    def readActiveDevices(self):
        active_nics = self.readActiveNics()
        for mac in active_nics:
            if mac not in self.known_devices:
                new_value = 1 + max(self.known_devices.values())
                self.known_devices[mac] = new_value

        assert all(mac in self.known_devices for mac in active_nics)

        return set(self.known_devices[mac] for mac in active_nics)

    def readPresenceCount(self):
        active_devices = self.readActiveDevices()
        return len(active_devices - set([0]))

    def _load_dict_from_file(self, filename):
        import ast
        with open(filename, 'r') as file:
            content = file.read()
            return ast.literal_eval(content)

if __name__ == '__main__':
    import sys
    sensor = Wifi(sys.argv[1])

    active_nics = sensor.readActiveNics()
    print("Hosts: %s" % ', '.join(active_nics))

    active_devices = sensor.readActiveDevices()
    print("Known hosts: %s"
          % ', '.join(["%s" % device for device in active_devices]))

    presence_count = sensor.readPresenceCount()
    print("Presence count: %d" % presence_count)
