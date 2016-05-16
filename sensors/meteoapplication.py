#!/usr/bin/env python3

import logging
import yaml
import os
from monitor import (
    SingletonMonitor, DatabaseMonitor, ContinuousMonitorProxy)


def load_class(directory, module_name, class_name):
    import imp
    foo = imp.load_source(module_name, directory + "/" + module_name + ".py")
    return getattr(foo, class_name)


class Application:

    def run(self):
        directory = os.path.dirname(__file__)
        args = self.parse_command_line()
        self.setup_logging(args)
        sensors_information = self.retrieve_sensors_information(args.sensors)
        monitor = self.create_monitor(args)
        for info in sensors_information:
            try:
                module_name = sensors_information[info]['module_name']
                class_name = sensors_information[info]['class_name']
                logging.debug(
                    "Instantiating class %s.%s"
                    % (module_name, class_name))
                clazz = load_class(directory, module_name, class_name)
                ctor_args = sensors_information[info].get('ctor_args', [])
                logging.debug(
                    "Instantiating object %s.%s(%s)"
                    % (module_name, class_name, ', '.join(ctor_args)))
                obj = clazz(*ctor_args)
                monitor.attach_reader(
                    info, obj, sensors_information[info]['sensors'])
            except ImportError as e:
                logging.critical("Can't continue for %s: %s" % (class_name, e))
            except FileNotFoundError as e:
                logging.critical("Can't continue for %s: %s" % (class_name, e))
        monitor.run()

    def parse_command_line(self):
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument(
            '-v', '--verbose',
            help='increase output verbosity',
            action='store_true')
        parser.add_argument(
            '-s', '--sensors',
            help='sensors data file',
            type=str,
            default='sensors.yaml')
        parser.add_argument(
            '-c', '--continuous',
            help='continuously read sensors every N seconds',
            type=int, metavar='N')
        parser.add_argument(
            'storage',
            help='storage backend',
            type=str, choices=['db', 'dummy'])
        parser.add_argument(
            '--database',
            help='database path',
            type=str, default='meteodata.db')
        parser.add_argument(
            '--filename',
            help='output file path',
            type=str, default='meteodata.txt')
        parser.add_argument(
            '--known-wifi-devices',
            help='known wi-fi devices filename',
            type=str, default='known_devices.txt')

        return parser.parse_args()

    def setup_logging(self, args):
        level = logging.DEBUG if args.verbose else logging.INFO
        logging.basicConfig(level=level)

    def retrieve_sensors_information(self, filename):
        with open(filename, encoding='utf-8') as file:
            return yaml.load(file)[0]

    def create_monitor(self, args):
        monitor = self.create_basic_monitor(args)
        if args.continuous:
            continuous_monitor = ContinuousMonitorProxy(monitor)
            continuous_monitor.set_interval(args.continuous)
            return continuous_monitor
        else:
            return monitor

    def create_basic_monitor(self, args):
        if args.storage == 'dummy':
            return SingletonMonitor()
        elif args.storage == 'db':
            return DatabaseMonitor(args.database)
        else:
            raise RuntimeError("Unknown storage backend \"%s\"" % args.storage)


def main():
    application = Application()
    application.run()

if __name__ == '__main__':
    main()
