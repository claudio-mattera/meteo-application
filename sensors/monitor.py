#!/usr/bin/python

from time import sleep
from threading import Thread
from datetime import datetime
from os.path import isfile
import sqlite3
import logging


class SingletonMonitor(object):
    """
    Monitors a list of sensor readers once.
    Prints the results to console.
    """

    def __init__(self):
        self.readers = []

    def attach_reader(self, name, obj, sensors):
        self.readers.append((name, obj, sensors))

    def run(self):
        date_time = datetime.utcnow()

        readings = {}
        for name, obj, sensors in self.readers:
            for sensor in sensors:
                try:
                    name = sensor['name']
                    args = sensor.get('args', [])
                    method_name = 'read_' + sensor['field']
                    logging.debug(
                        "Calling %s(%s)"
                        % (method_name, ', '.join(args)))
                    method = getattr(obj, method_name)
                    value = method(*args)
                    logging.debug("Result: %r" % value)
                    readings[name] = value
                except Exception as ex:
                    logging.critical("Error querying %s: %s" % (name, ex))

        self.store_reading(date_time, readings)

    def store_reading(self, date_time, readings):
        print("Date: %s" % date_time)
        for name, value in readings.items():
            print("%s: %r" % (name, value))


class DatabaseMonitor(SingletonMonitor):
    """
    Monitors a list of sensor readers once.
    Store the results to a SQLite database.
    """

    def __init__(self, database_path):
        super(DatabaseMonitor, self).__init__()
        self.database_path = database_path
        self.ensure_table_exists()

    def store_reading(self, date_time, reading):
        logger = logging.getLogger(__name__)
        logger.debug('Storing reading to database')

        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                "INSERT INTO MeteoData \
                    (dateTime, \
                     internalTemperature, \
                     pressureTemperature, pressurePressure, pressureAltitude, \
                     humidityTemperature, humidityHumidity, \
                     windSpeed, windDirection, \
                     lightInfrared, lightVisible, lightUltraviolet, \
                     presenceCount) \
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (date_time,
                 reading.get('internalTemperature'),
                 reading.get('pressureTemperature'),
                 reading.get('pressurePressure'),
                 reading.get('pressureAltitude'),
                 reading.get('humidityTemperature'),
                 reading.get('humidityHumidity'),
                 reading.get('windSpeed'),
                 reading.get('windDirection'),
                 reading.get('lightInfrared'),
                 reading.get('lightVisible'),
                 reading.get('lightUltraviolet'),
                 reading.get('presenceCount')
                 ))

    def ensure_table_exists(self):
        logger = logging.getLogger(__name__)
        logger.debug('Ensuring table MeteoData exists')

        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                '''CREATE TABLE IF NOT EXISTS MeteoData
                   (dateTime             TEXT  PRIMARY KEY  NOT NULL,
                    internalTemperature  REAL,
                    pressureTemperature  REAL,
                    pressurePressure     REAL,
                    pressureAltitude     REAL,
                    humidityTemperature  REAL,
                    humidityHumidity     REAL,
                    windSpeed            REAL,
                    windDirection        REAL,
                    lightInfrared        REAL,
                    lightVisible         REAL,
                    lightUltraviolet     REAL,
                    presenceCount        INTEGER
                    );''')


class FileMonitor(SingletonMonitor):
    """
    Monitors a list of sensor readers once.
    Writes the results to a file.
    """

    def __init__(self, file_name):
        super(FileMonitor, self).__init__()
        self.file_name = file_name

        if not isfile(self.file_name):
            with open(self.file_name, 'w') as file:
                file.write(self.file_heading())

    def store_reading(self, date_time, reading):
        reading_string = self.format_reading_for_file(date_time, reading)
        with open(self.file_name, 'a') as file:
            file.write(reading_string)

    def fields(self):
        return ['internalTemperature',
                'pressureTemperature', 'pressurePressure', 'pressureAltitude',
                'humidityTemperature', 'humidityHumidity',
                'windSpeed', 'windDirection',
                'lightInfrared', 'lightVisible', 'lightUltraviolet',
                'presenceCount']

    def file_heading(self):
        return "date," + ','.join(self.fields()) + "\n"

    def format_reading_for_file(self, date_time, reading):
        date_string = date_time.isoformat()

        def f(value):
            return ("%.2f" % value) if value else ''

        calues_string = ','.join(f(reading[field]) for field in self.fields())
        return date_string + ',' + calues_string + '\n'


class ContinuousMonitorProxy(object):
    """
    Monitors a list of sensor readers continuously.
    """

    def __init__(self, monitor):
        self.monitor = monitor

        self.interval = 60
        self.isReading = False

    def attach_reader(self, name, obj, sensors):
        self.monitor.attach_reader(name, obj, sensors)

    def run(self):
        self.start_monitoring()

        try:
            while True:
                sleep(1)
        except (KeyboardInterrupt, SystemExit):
            logger = logging.getLogger(__name__)
            logger.info('Continuous monitor interrupted')

            self.stop_monitoring()

    def set_interval(self, interval):
        logger = logging.getLogger(__name__)
        logger.info("Setting interval to %d seconds" % interval)
        self.interval = int(interval)

    def start_monitoring(self):
        if self.isReading:
            return

        logger = logging.getLogger(__name__)
        logger.info('Start reading')
        self.isReading = True
        self.thread = Thread(target=self.keep_monitoring)
        self.thread.start()

    def stop_monitoring(self):
        if not self.isReading:
            return

        logger = logging.getLogger(__name__)
        logger.info("Stop reading (will stop at next iteration, " +
                    "within %d seconds)" % self.interval)

        self.isReading = False

    def keep_monitoring(self):
        while self.isReading:
            self.monitor.run()
            sleep(self.interval)
