#!/usr/bin/env python3

import logging
from reader import *
from monitor import *

class Application:

    def run(self):
        args = self.parseCommandLine()
        self.setupLogging(args)
        monitor = self.createMonitor(args)
        internalReader = InternalReader()
        pressureReader = PressureReader(args.pressure_accuracy)
        humidityReader = HumidityReader()
        windReader = WindReader()
        lightReader = LightReader()
        presenceReader = PresenceReader(args.known_wifi_devices)
        monitor.attachReader(internalReader)
        monitor.attachReader(pressureReader)
        monitor.attachReader(humidityReader)
        monitor.attachReader(windReader)
        monitor.attachReader(lightReader)
        monitor.attachReader(presenceReader)
        monitor.run()

    def parseCommandLine(self):
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument('-v', '--verbose', help='increase output verbosity', action='store_true')
        parser.add_argument('--pressure-accuracy', help='pressure sensor\'s accuracy', type=int, choices=[0,1,2,3], default=3)
        parser.add_argument('-c', '--continuous', help='continuously read sensors every N seconds', type=int, metavar='N')
        parser.add_argument('storage', help='storage backend', type=str, choices=['db', 'file', 'dummy'])
        parser.add_argument('--database', help='database path', type=str, default='meteodata.db')
        parser.add_argument('--filename', help='output file path', type=str, default='meteodata.txt')
        parser.add_argument('--known-wifi-devices', help='known wi-fi devices filename', type=str, default='known_devices.txt')

        return parser.parse_args()

    def setupLogging(self, args):
        level = logging.DEBUG if args.verbose else logging.INFO
        logging.basicConfig(level=level)

    def createMonitor(self, args):
        monitor = self.createBasicMonitor(args)
        if args.continuous:
            continuousMonitor = ContinuousMonitorProxy(monitor)
            continuousMonitor.setInterval(args.continuous)
            return continuousMonitor
        else:
            return monitor

    def createBasicMonitor(self, args):
        if args.storage == 'dummy':
            return SingletonMonitor()
        elif args.storage == 'file':
            return FileMonitor(args.filename)
        elif args.storage == 'db':
            return DatabaseMonitor(args.database)
        else:
            raise RuntimeError("Unknown storage backend \"%s\"" % args.storage)

def main():
    application = Application()
    application.run()

if __name__ == '__main__':
    main()
