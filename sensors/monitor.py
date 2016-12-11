#!/usr/bin/python

from time import sleep
from threading import Thread
from datetime import datetime
import sqlite3
import logging
import typing


Reading = typing.Tuple[typing.Text, typing.Text, datetime, float]
Sensor = typing.Dict[typing.Text, typing.Any]
Reader = typing.Tuple[typing.Text, typing.Any, typing.List[Sensor], bool]


class MonitorInterface:
    def run(self) -> None:
        raise RuntimeError('Unimplemented')

    def attach_reader(self, name: typing.Text, obj: typing.Any, sensors: typing.List[Sensor], use_median: bool) -> None:
        raise RuntimeError('Unimplemented')

    def store_readings(self, readings: typing.List[Reading]) -> None:
        raise RuntimeError('Unimplemented')


class SingletonMonitor(MonitorInterface):
    """
    Monitors a list of sensor readers once.
    Prints the results to console.
    """

    def __init__(self) -> None:
        super(SingletonMonitor, self).__init__()
        self.readers = []  # type: typing.List[Reader]

    def attach_reader(self, name: typing.Text, obj: typing.Any, sensors: typing.List[Sensor], use_median: bool) -> None:
        self.readers.append((name, obj, sensors, use_median))

    def run(self) -> None:
        logger = logging.getLogger(__name__)

        readings = []  # type: typing.List[Reading]

        for name, obj, sensors, use_median in self.readers:
            for sensor in sensors:
                try:
                    name = sensor['name']
                    datatype = sensor['datatype']
                    args = sensor.get('args', [])
                    method_name = 'read_' + sensor['field']
                    logger.debug(
                        "Calling %s(%s)"
                        % (method_name, ', '.join(args)))
                    method = getattr(obj, method_name)

                    if use_median:
                        # Take the median of few attempts
                        n_attempts = 5
                        values = [method(*args) for _ in range(n_attempts)]
                        value = values[n_attempts // 2 + 1]
                    else:
                        value = method(*args)

                    logger.debug("Result: %r" % value)
                    date_time = datetime.utcnow()
                    readings.append((name, datatype, date_time, value))
                except Exception as ex:
                    logger.critical("Error querying %s: %s" % (name, ex))
        self.store_readings(readings)

    def store_readings(self, readings: typing.List[Reading]) -> None:
        for name, datatype, date_time, value in readings:
            self._store_reading(name, datatype, date_time, value)

    def _store_reading(self, name: typing.Text, datatype: typing.Text, date_time: datetime, value: float) -> None:
        logger = logging.getLogger(__name__)
        logger.info("%s %s = %r :: %s" % (date_time, name, value, datatype))


class DatabaseMonitor(SingletonMonitor):
    """
    Monitors a list of sensor readers once.
    Store the results to a SQLite database.
    """

    def __init__(self, database_path: typing.Text) -> None:
        super(DatabaseMonitor, self).__init__()
        self.database_path = database_path

        with sqlite3.connect(self.database_path) as connection:
            self.ensure_master_table_exists(connection)

    def attach_reader(self, name: typing.Text, obj: typing.Any, sensors: typing.List[Sensor], use_median: bool) -> None:
        super(DatabaseMonitor, self).attach_reader(name, obj, sensors, use_median)

        with sqlite3.connect(self.database_path) as connection:
            for sensor in sensors:
                name = sensor['name']
                kind = sensor['kind']
                unit = sensor['unit']
                datatype = sensor['datatype']

                self.ensure_table_exists(
                    name, kind, unit, datatype, connection)

    def store_readings(self, readings: typing.List[Reading]) -> None:
        logger = logging.getLogger(__name__)
        with sqlite3.connect(self.database_path) as connection:
            logger.debug('Storing %d readings to database' % len(readings))
            for name, datatype, date_time, value in readings:
                self._store_reading_db(
                    name, datatype, date_time, value, connection)

    def _store_reading_db(self, name: typing.Text, datatype: typing.Text, date_time: datetime, value: float, connection: typing.Any) -> None:
        connection.execute(
            "INSERT INTO %s (date_time, value) \
             VALUES (?, ?)" % name,
            (date_time.strftime("%Y-%m-%d %H:%M:%S"), value))

    def ensure_table_exists(self, name: typing.Text, kind: typing.Text, unit: typing.Text, datatype: typing.Text, connection: typing.Any) -> None:
        logger = logging.getLogger(__name__)
        logger.debug('Ensuring table %s exists' % name)

        if datatype not in ['INTEGER', 'REAL']:
            raise ValueError("Invalid type: %s" % datatype)

        connection.execute(
            '''CREATE TABLE IF NOT EXISTS %s
               (date_time TEXT  PRIMARY KEY  NOT NULL,
                value     %s
               );''' % (name, datatype))

        connection.execute(
            '''INSERT OR IGNORE INTO master (name, kind, unit, datatype) \
               VALUES (?, ?, ?, ?)''', (name, kind, unit, datatype))

    def ensure_master_table_exists(self, connection: typing.Any) -> None:
        logger = logging.getLogger(__name__)
        logger.debug('Ensuring master table exists')

        connection.execute(
            '''CREATE TABLE IF NOT EXISTS master
               (name     TEXT  PRIMARY KEY  NOT NULL,
                kind     TEXT               NOT NULL,
                unit     TEXT               NOT NULL,
                datatype TEXT               NOT NULL,
                UNIQUE(name)
               );''')


class ContinuousMonitorProxy(MonitorInterface):
    """
    Monitors a list of sensor readers continuously.
    """

    def __init__(self, monitor: MonitorInterface) -> None:
        super(ContinuousMonitorProxy, self).__init__()

        self.monitor = monitor

        self.interval = 60
        self.isReading = False

    def attach_reader(self, name: typing.Text, obj: typing.Any, sensors: typing.List[Sensor], use_median: bool) -> None:
        self.monitor.attach_reader(name, obj, sensors, use_median)

    def run(self) -> None:
        self.start_monitoring()

        try:
            while True:
                sleep(1)
        except (KeyboardInterrupt, SystemExit):
            logger = logging.getLogger(__name__)
            logger.info('Continuous monitor interrupted')

            self.stop_monitoring()

    def set_interval(self, interval: int) -> None:
        logger = logging.getLogger(__name__)
        logger.info("Setting interval to %d seconds" % interval)
        self.interval = int(interval)

    def start_monitoring(self) -> None:
        if self.isReading:
            return

        logger = logging.getLogger(__name__)
        logger.info('Start reading')
        self.isReading = True
        self.thread = Thread(target=self.keep_monitoring)
        self.thread.start()

    def stop_monitoring(self) -> None:
        if not self.isReading:
            return

        logger = logging.getLogger(__name__)
        logger.info("Stop reading (will stop at next iteration, " +
                    "within %d seconds)" % self.interval)

        self.isReading = False

    def keep_monitoring(self) -> None:
        while self.isReading:
            self.monitor.run()
            sleep(self.interval)
