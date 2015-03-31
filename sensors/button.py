#!/usr/bin/env python3

import RPi.GPIO as GPIO
from time import sleep
import logging
import argparse

keep = True

def shutdown_callback(pin):
    logging.info("Callback called on pin %d" % pin)
    global keep
    keep = False

def main_loop():
    logging.info('Entering main loop')
    global keep
    while keep:
        sleep(1)

def parse_command_line():
    parser = argparse.ArgumentParser(
        description='Handle button press')
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Increase logging')
    parser.add_argument(
        '-s', '--shutdown-pin',
        type=int,
        default=21,
        help='The pin corresponding to shutdown button')
    return parser.parse_args()

def main():
    arguments = parse_command_line()
    if arguments.verbose:
        logging.basicConfig(level=logging.INFO)
    
    logging.info("Waiting for shutdown event on pin %d"
                 % arguments.shutdown_pin)

    try:
        logging.info('Initializing GPIO')
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(
            arguments.shutdown_pin,
            GPIO.IN,
            pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(
            arguments.shutdown_pin,
            GPIO.RISING,
            callback=shutdown_callback,
            bouncetime=3000)
        main_loop()
    finally:
        logging.info('Cleaning up GPIO')
        GPIO.cleanup()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()