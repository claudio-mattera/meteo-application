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

    def attachReader(self, reader):
        self.readers.append(reader)

    def run(self):
        dateTime = datetime.utcnow()

        readings = {}
        for reader in self.readers:
            try:
                values = reader.readValues()
            except Exception as ex:
                print("Error querying %s reader: %s" % (reader.name(), ex))
                continue
            name = reader.name()
            values = dict((name + key, value) for (key, value) in values.items())
            readings.update(values)

        self.storeReading(dateTime, readings)

    def storeReading(self, dateTime, readings):
        print("Date: %s" % dateTime)
        for name, value in readings.items():
            print("%s: %r" % (name, value))


class DatabaseMonitor(SingletonMonitor):
    """
    Monitors a list of sensor readers once.
    Store the results to a SQLite database.
    """

    def __init__(self, databasePath):
        super(DatabaseMonitor, self).__init__()
        self.databasePath = databasePath
        self.ensureTableExists()

    def storeReading(self, dateTime, reading):
        logger = logging.getLogger(__name__)
        logger.debug('Storing reading to database')

        with sqlite3.connect(self.databasePath) as connection:
            connection.execute(
                "INSERT INTO MeteoData \
                    (dateTime, \
                     internalTemperature, \
                     pressureTemperature, pressurePressure, pressureAltitude, \
                     humidityTemperature, humidityHumidity, \
                     windSpeed, windDirection, \
                     lightInfrared, lightVisible, lightUltraviolet) \
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (dateTime,
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
                    reading.get('lightUltraviolet')
                    ));

    def ensureTableExists(self):
        logger = logging.getLogger(__name__)
        logger.debug('Ensuring table MeteoData exists')

        with sqlite3.connect(self.databasePath) as connection:
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
                    lightUltraviolet     REAL
                    );''')


class FileMonitor(SingletonMonitor):
    """
    Monitors a list of sensor readers once.
    Writes the results to a file.
    """

    def __init__(self, fileName):
        super(FileMonitor, self).__init__()
        self.fileName = fileName

        if not isfile(self.fileName):
            with open(self.fileName, 'w') as file:
                file.write(self.fileHeading())

    def storeReading(self, dateTime, reading):
        readingString = self.formatReadingForFile(dateTime, reading)
        with open(self.fileName, 'a') as file:
            file.write(readingString)

    def fields(self):
        return ['internalTemperature',
                'pressureTemperature', 'pressurePressure', 'pressureAltitude',
                'humidityTemperature', 'humidityHumidity',
                'windSpeed', 'windDirection',
                'lightInfrared', 'lightVisible', 'lightUltraviolet']

    def fileHeading(self):
        return "date," + ','.join(self.fields()) + "\n"

    def formatReadingForFile(self, dateTime, reading):
        dateString = dateTime.isoformat()
        f = lambda value: ("%.2f" % value) if value else ''
        valuesString = ','.join(f(reading[field]) for field in self.fields())
        return dateString + ',' + valuesString + '\n'


class ContinuousMonitorProxy(object):
    """
    Monitors a list of sensor readers continuously.
    """

    def __init__(self, monitor):
        self.monitor = monitor

        self.interval = 60
        self.isReading = False

    def attachReader(self, reader):
        self.monitor.attachReader(reader)

    def run(self):
        self.startMonitoring()

        try:
            while True:
                sleep(1)
        except (KeyboardInterrupt, SystemExit):
            logger = logging.getLogger(__name__)
            logger.info('Continuous monitor interrupted')

            self.stopMonitoring()

    def setInterval(self, interval):
        logger = logging.getLogger(__name__)
        logger.info("Setting interval to %d seconds" % interval)
        self.interval = int(interval)

    def startMonitoring(self):
        if self.isReading:
            return

        logger = logging.getLogger(__name__)
        logger.info('Start reading')
        self.isReading = True
        self.thread = Thread(target=self.keepMonitoring)
        self.thread.start()

    def stopMonitoring(self):
        if not self.isReading:
            return

        logger = logging.getLogger(__name__)
        logger.info("Stop reading (will stop at next iteration, \
                    within %d seconds)" % self.interval)

        self.isReading = False

    def keepMonitoring(self):
        while self.isReading:
            self.monitor.run()
            sleep(self.interval)
