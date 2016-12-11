import subprocess


class BoardTemperature(object):

    def __init__(self) -> None:
        pass

    def read_temperature(self) -> float:
        args = ['/opt/vc/bin/vcgencmd', 'measure_temp']
        output = subprocess.check_output(args)
        # Output has form "temp=XX.X'C\n"
        return float(output[5:-3])
