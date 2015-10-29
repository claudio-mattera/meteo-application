#!/usr/bin/env python3

import sqlite3


def read_table(db, fields, field_names):
    query = "SELECT %s FROM MeteoData" % ', '.join(fields)
    output = ','.join(field_names) + '\n'
    for row in db.execute(query):
        output += ','.join(map(lambda x: "%s" % x, row)) + '\n'
    return output


def read_pressure_table(db):
    fields = ['datetime(dateTime, "localtime")',
              'internalTemperature',
              'pressureTemperature',
              'pressurePressure']
    field_names = ['date',
                   'internal_temperature',
                   'temperature',
                   'pressure']
    return read_table(db, fields, field_names)

def read_light_table(db):
    fields = ['datetime(dateTime, "localtime")',
              'internalTemperature',
              'pressureTemperature',
              'lightVisible']
    field_names = ['date',
                   'internal_temperature',
                   'temperature',
                   'light']
    return read_table(db, fields, field_names)


def read_presence_table(db):
    fields = ['datetime(dateTime, "localtime")',
              'presenceCount']
    field_names = ['date',
                   'count']
    return read_table(db, fields, field_names)


def read_tables(database):
    with sqlite3.connect(database) as db:
        pressure = read_pressure_table(db)
        light = read_light_table(db)
        presence = read_presence_table(db)
        return (pressure, light, presence)


def write_output(destination_dir, name, data):
    filename = destination_dir + '/' + name + '.csv'
    with open(filename, 'w') as file:
        file.write(data)


def main():
    destination_dir = '/var/www/meteo'
    database = '/var/lib/meteo/data.db'
    (pressure, light, presence) = read_tables(database)
    write_output(destination_dir, 'pressure', pressure)
    write_output(destination_dir, 'light', light)
    write_output(destination_dir, 'presence', presence)


if __name__ == '__main__':
    main()
