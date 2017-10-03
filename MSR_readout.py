#!/usr/bin/env python
"""
Usage:
  MSR_readout [options]

Options:
  --help
  --device PATH    path to USB device file [default: /dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A800ftAV-if00-port0]
  --outfile PATH   path to output file [default: MSR.json]
  --quiet          do not print the json to stdout

Read the output file maybe like this:
    import pandas as pd
    df = pd.read_json('MSR.json', lines=True)
    df['time'] = pd.to_datetime(df.time, unit='s')
    df.set_index('time', inplace=True)
"""
from docopt import docopt
import serial
import time
import numpy as np
from datetime import datetime
import json

device_path = ''

B = -5.775e-7
A = 3.9083e-3


def temp_from_R(R):
    return (-A + np.sqrt(A**2 - 4*B*(1-(R/1e3))))/(2*B)


def initialize_device(s):
    print("initializing device, please wait ...", end="", flush=True)
    for i in range(16):
        s.write(('Er{0}\n'.format(i)).encode('ascii'))
        s.flush()
        time.sleep(0.3)
        s.read_all()

    s.write(b'P\n')
    s.read_all()
    print("done")


def main():
    args = docopt(__doc__)

    serial_device = serial.Serial(args['--device'])
    initialize_device(serial_device)

    outfile = open(args['--outfile'], 'a')
    full_line = ""
    left_part = ""
    while True:
        full_line += serial_device.read_all().decode('ascii')
        if '\n' in full_line:
            left_part, full_line = full_line.split('\n', 1)
        if left_part and left_part[0] == 'R':
            stuff = list(map(float, left_part.split('|')[1:-1]))
            left_part = ""
            resistances = np.array(stuff[1:])
            temps = temp_from_R(resistances)
            json_object = {
               'time': datetime.utcnow().timestamp(),
            }
            for i, t in enumerate(temps):
                json_object['T'+str(i)] = t
            if not args['--quiet']:
                print(json_object)
            outfile.write(json.dumps(json_object))
            outfile.write('\n')
            outfile.flush()


if __name__ == "__main__":
    main()
