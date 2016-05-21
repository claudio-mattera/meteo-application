import bottle

import sqlite3
import datetime


def parse_bool(string):
    return string.lower() in ['true', 't', 'yes', 'y']


bottle.default_app().config.load_config('config.ini')

RESAMPLING = parse_bool(bottle.default_app().config['charts.resampling'])
RESAMPLING_FREQUENCY = bottle.default_app().config[
    'charts.resampling_frequency']
DATABASE_PATH = bottle.default_app().config['sqlite.db']
ROOT = bottle.default_app().config['server.root']


def resample(readings, start, end, frequency):
    import pandas as pd
    from resample import resample

    def write_reading(i, v):
        timestamp = int(i.timestamp() * 1000)
        value = v.item()
        return [timestamp, value]

    if len(readings) > 0:
        datetimes, values = zip(*readings)
    else:
        datetimes, values = [], []

    series = pd.Series(values, index=pd.to_datetime(datetimes))

    resampled = resample(
        series,
        start.replace(second=00),
        end,
        frequency,
        'nan'
    ).dropna()

    return [write_reading(i, resampled[i]) for i in resampled.index]


def parse_date(string):
    return datetime.datetime.strptime(string, "%Y-%m-%d %H:%M:%S")


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


@bottle.get(ROOT + 'get_available_streams')
def get_available_streams():

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        query = "SELECT name, kind FROM master"
        cursor = connection.execute(query)
        streams = [
            {'name': row['name'], 'kind': row['kind']} for row in cursor]

    return {
        'streams': streams
    }


@bottle.get(ROOT + 'get_stream')
def get_stream():
    meters = bottle.request.GET.get("meters").split(',')
    start = parse_date(bottle.request.GET.get("start"))
    end = parse_date(bottle.request.GET.get("end"))

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

        if RESAMPLING:
            readings = resample(readings, start, end, RESAMPLING_FREQUENCY)

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
        'data': data
    }

    return output


@bottle.get(ROOT)
def index():
    return bottle.static_file('index.html', root='.', mimetype='text/html')
