#!/usr/bin/python

from time import sleep
from threading import Thread
from datetime import datetime
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
        logger = logging.getLogger(__name__)
        date_time = datetime.utcnow()

        for name, obj, sensors in self.readers:
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
                    value = method(*args)
                    logger.debug("Result: %r" % value)
                    self.store_reading(name, datatype, date_time, value)
                except Exception as ex:
                    logger.critical("Error querying %s: %s" % (name, ex))

    def store_reading(self, name, datatype, date_time, value):
        logger = logging.getLogger(__name__)
        logger.info("%s %s = %r :: %s" % (date_time, name, value, datatype))


class DatabaseMonitor(SingletonMonitor):
    """
    Monitors a list of sensor readers once.
    Store the results to a SQLite database.
    """

    def __init__(self, database_path):
        super(DatabaseMonitor, self).__init__()
        self.database_path = database_path

    def store_reading(self, name, datatype, date_time, value):
        logger = logging.getLogger(__name__)

        with sqlite3.connect(self.database_path) as connection:
            self.ensure_table_exists(name, datatype, connection)

            logger.debug('Storing reading to database')
            connection.execute(
                "INSERT INTO %s (date_time, value) \
                 VALUES (?, ?)" % name,
                (date_time.strftime("%Y-%m-%d %H:%M:%S"), value))

    def ensure_table_exists(self, name, datatype, connection):
        logger = logging.getLogger(__name__)
        logger.debug('Ensuring table %s exists' % name)

        if datatype not in ['INTEGER', 'REAL']:
            raise ValueError("Invalid type: %s" % datatype)

        connection.execute(
            '''CREATE TABLE IF NOT EXISTS %s
               (date_time TEXT  PRIMARY KEY  NOT NULL,
                value     %s
               );''' % (name, datatype))


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
