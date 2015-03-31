#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time
import logging

keep = True

def pin_callback(pin):
    print("Callback called on pin %d" % pin)
    global keep
    keep = False

def main_loop():
    global keep
    while keep:
        time.sleep(1)

def main():
    pin = 21

    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        GPIO.add_event_detect(pin, GPIO.RISING, callback=pin_callback, bouncetime=3000)
        main_loop()
    finally:
        GPIO.cleanup()


if __name__ == '__main__':
    main()