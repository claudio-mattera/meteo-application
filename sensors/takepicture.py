#!/usr/bin/env python3

import picamera
import time
from fractions import Fraction
import argparse
import logging
import io
from PIL import Image
from PIL import ImageStat


CONFIGURATIONS = {
    'auto': {
    },
    'sunny': {
        'exposure_mode': 'auto',
        'awb_mode': 'sunlight'
    },
    'cloudy': {
        'exposure_mode': 'auto',
        'awb_mode': 'cloudy'
    },
    'night': {
        'framerate': Fraction(1, 6),
        'shutter_speed': 6000000,
        'exposure_mode': 'off',
        'iso': 800,
        'awb_mode': 'shade'
    }
}


def estimate_light():
    from BH1750 import BH1750
    sensor = BH1750()
    light_level = sensor.read_light()
    return light_level


def is_below_light_threshold(threshold):
    try:
        light_level = estimate_light()
        return light_level < threshold
    except IOError as e:
        import errno
        if e.errno == errno.EACCES:
            logging.warning('Access to light sensor denied')
            return False
        raise


def parse_resolution(string):
    [width, height] = string.split('x')
    return (int(width), int(height))


def get_configuration(arguments):
    if arguments.light_threshold:
        light_threshold = max(200, arguments.light_threshold)
        if is_below_light_threshold(light_threshold):
            logging.info('Below light threshold, forcing night configuration')
            configuration = CONFIGURATIONS['night']
        else:
            configuration = CONFIGURATIONS[arguments.configuration]
    else:
        configuration = CONFIGURATIONS[arguments.configuration]
    return configuration


def capture_image(arguments):
    configuration = get_configuration(arguments)

    stream = io.BytesIO()
    with picamera.PiCamera() as camera:
        camera.hflip = arguments.hflip
        camera.vflip = arguments.vflip
        if arguments.rotation:
            camera.rotation = arguments.rotation
        camera.resolution = arguments.resolution

        for (key, value) in configuration.items():
            setattr(camera, key, value)
        if 'exposure_mode' in configuration and configuration['exposure_mode'] == 'off':
            # Give the camera a good long time to measure AWB
            # (you may wish to use fixed AWB instead)
            logging.info('Auto-measuring AWB')
            time.sleep(10)

        logging.info('Capturing image')
        camera.capture(stream, format='jpeg')
    stream.seek(0)
    return Image.open(stream)


def save_image(image, arguments):
    if arguments.timestamp:
        timestamp = time.strftime("%Y-%m-%d %H-%M-%S") + ".jpg"
        filename = arguments.filename + timestamp
    else:
        filename = arguments.filename
    logging.info('Saving image')
    image.save(filename, quality=95, optimize=True)


def is_invalid(image):
    stat = ImageStat.Stat(image)
    return max(stat.stddev) < 1


def take_picture(arguments):
    image = capture_image(arguments)

    if is_invalid(image):
        logging.warning('Invalid image, releasing light threshold option')
        arguments.light_threshold = 0
        image = capture_image(arguments)

    save_image(image, arguments)


class StorePairAction(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        super(StorePairAction, self).__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        values = parse_resolution(values)
        setattr(namespace, self.dest, values)


def parse_command_line():
    parser = argparse.ArgumentParser(
        description='Takes a picture with the camera')
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Increase logging')
    parser.add_argument(
        '-f', '--filename',
        default='image.jpg',
        help='The destination image file name')
    parser.add_argument(
        '-t', '--timestamp',
        action='store_true',
        help='Add the current time to file name')
    parser.add_argument(
        '--rotation',
        help='Camera rotation (0, 90, 180, 270)')
    parser.add_argument(
        '--hflip',
        action='store_true',
        help='Horizontally flip the image')
    parser.add_argument(
        '--vflip',
        action='store_true',
        help='Vertically flip the image')
    parser.add_argument(
        '-r', '--resolution',
        default=(2592, 1944),
        action=StorePairAction,
        help='Image resolution, e.g. 1024x768')
    parser.add_argument(
        '-l', '--light-threshold',
        type=int,
        help='Light threshold below which night mode is used')
    parser.add_argument(
        '-c', '--configuration',
        default='auto',
        help="Camera configuration (%s)" % (', '.join(CONFIGURATIONS)))
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    arguments = parse_command_line()
    if arguments.verbose:
        logging.basicConfig(level=logging.INFO)
    take_picture(arguments)
