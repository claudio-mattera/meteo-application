#!/bin/bash

DESTDIR="/var/www"

> $DESTDIR/pressure.csv
echo "date,internal_temperature,temperature,pressure" >> $DESTDIR/pressure.csv
sqlite3 /var/lib/meteo/data.db "SELECT datetime(dateTime),internalTemperature,pressureTemperature,pressurePressure FROM MeteoData" | sed s/\|/,/g >> $DESTDIR/pressure.csv

> $DESTDIR/light.csv
echo "date,internal_temperature,temperature,light" >> $DESTDIR/light.csv
sqlite3 /var/lib/meteo/data.db "SELECT datetime(dateTime),internalTemperature,pressureTemperature,lightVisible FROM MeteoData" | sed s/\|/,/g >> $DESTDIR/light.csv
