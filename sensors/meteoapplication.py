#!/usr/bin/env python3

import logging
import yaml
import os
import imp
import typing
from monitor import (
    MonitorInterface, SingletonMonitor, DatabaseMonitor, ContinuousMonitorProxy
)


def load_class(directory: typing.Text, module_name: typing.Text, class_name: typing.Text) -> typing.Any:
    foo = imp.load_source(module_name, directory + "/" + module_name + ".py")
    return getattr(foo, class_name)


class Application:

    def run(self) -> None:
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
                    % (module_name, class_name, ', '.join([str(a) for a in ctor_args])))
                obj = clazz(*ctor_args)
                monitor.attach_reader(
                    info,
                    obj,
                    sensors_information[info]['sensors'],
                    sensors_information[info]['use_median'],
                )
            except ImportError as e:
                logging.critical("Can't continue for %s: %s" % (class_name, e))
            except IOError as e:
                logging.critical("Can't continue for %s: %s" % (class_name, e))
        monitor.run()

    def parse_command_line(self) -> typing.Any:
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

        return parser.parse_args()

    def setup_logging(self, args: typing.Any) -> None:
        level = logging.DEBUG if args.verbose else logging.INFO
        logging.basicConfig(level=level)

    def retrieve_sensors_information(self, filename: typing.Text) -> typing.Dict:
        with open(filename, encoding='utf-8') as file:
            return yaml.load(file)[0]

    def create_monitor(self, args: typing.Any) -> MonitorInterface:
        monitor = self.create_basic_monitor(args)
        if args.continuous:
            continuous_monitor = ContinuousMonitorProxy(monitor)
            continuous_monitor.set_interval(args.continuous)
            return continuous_monitor
        else:
            return monitor

    def create_basic_monitor(self, args: typing.Any) -> MonitorInterface:
        if args.storage == 'dummy':
            return SingletonMonitor()
        elif args.storage == 'db':
            return DatabaseMonitor(args.database)
        else:
            raise RuntimeError("Unknown storage backend \"%s\"" % args.storage)


def main() -> None:
    application = Application()
    application.run()

if __name__ == '__main__':
    main()
