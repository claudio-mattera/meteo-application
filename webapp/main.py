import hug

import sqlite3
import datetime
import pandas as pd

from resample import resample


DATABASE_PATH = './meteodata.db'

ONE_MINUTE = '1T'


def parse_date(string):
    return datetime.datetime.strptime(string, "%Y-%m-%d %H:%M:%S")


date_time_type = hug.types.accept(
    parse_date, 'A date time', 'Invalid date time provided')


def write_reading(i, v):
    timestamp = int(i.timestamp() * 1000)
    value = v.item()
    return [timestamp, value]


def get_meter_metadata(connection, meter):
    query = "SELECT kind, unit, datatype FROM master WHERE name=?"
    cursor = connection.execute(query, (meter,))
    row = cursor.fetchone()
    return {
        'name': meter,
        'kind': row['kind'],
        'unit': row['unit'],
        'datatype': row['datatype'],
    }


@hug.cli()
@hug.get(output=hug.output_format.json)
@hug.local()
def get_available_streams(hug_timer=3):
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        query = "SELECT name, kind FROM master"
        cursor = connection.execute(query)
        streams = [
            {'name': row['name'], 'kind': row['kind']} for row in cursor]

    return {
        'streams': streams,
        'elapsed_time': float(hug_timer)
    }


@hug.cli()
@hug.get(output=hug.output_format.json)
@hug.local()
def get_stream(
        meters: hug.types.multiple,
        start: date_time_type,
        end: date_time_type,
        hug_timer=3):
    start_string = start.strftime("%Y-%m-%d %H:%M:%S")
    end_string = end.strftime("%Y-%m-%d %H:%M:%S")

    def fetch_meter(meter, connection):
        query = (
            "SELECT date_time, value FROM " + meter + " " +
            "WHERE strftime('%s', date_time) " +
            "BETWEEN strftime('%s', ?) AND strftime('%s', ?)"
        )
        cursor = connection.execute(query, (start_string, end_string))
        readings = [[row['date_time'], row['value']] for row in cursor]

        if len(readings) > 0:
            datetimes, values = zip(*readings)
        else:
            datetimes, values = [], []

        series = pd.Series(values, index=pd.to_datetime(datetimes))

        resampled = resample(
            series,
            start.replace(second=00),
            end,
            ONE_MINUTE,
            'constant'
        )

        readings = [write_reading(i, resampled[i]) for i in resampled.index]

        metadata = get_meter_metadata(connection, meter)

        return {
            'metadata': metadata,
            'readings': readings
        }

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        data = dict(
            (meter, fetch_meter(meter, connection)) for meter in meters)

    output = {
        'data': data,
        'elapsed_time': float(hug_timer)
    }

    return output


@hug.get('/', output=hug.output_format.file)
def index():
    return 'index.html'
