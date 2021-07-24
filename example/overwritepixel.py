#!/usr/bin/env python3

import hashlib
import random
import os
import requests
import struct
import sys
import time

SIZE = (1024, 1024)
OVERWRITE_STRUCT = struct.Struct('<HH3B')  # X, Y, R, G, B

if 'SECRET' not in os.environ:
    raise ValueError('"SECRET" environment variable missing!')
URL = 'https://gebirge.uber.space/overwrite_pixel?secret=' + os.environ['SECRET']
print(URL)


def submit_pixel(post_data):
    response = requests.post(URL, post_data)

    if response.status_code == 200:
        # Done!
        return None
    elif response.status_code == 400:
        raise AssertionError('Something went very wrong. Here is a hint from the server: >>>{}<<<'.format(response.text))
    else:
        raise AssertionError('Huh? Received HTTP {} from server, along with >>>{}<<<'.format(response.status_code, response.content))


def run_with(x, y, r, g, b):
    assert 0 <= x < SIZE[0]
    assert 0 <= y < SIZE[1]
    payload = OVERWRITE_STRUCT.pack(x, y, r, g, b)

    submit_pixel(payload)


def run_args(argv):
    if len(argv) != 1 + 5:
        print('USAGE: {} X Y R G B'.format(argv[0]), file=sys.stderr)
        exit(1)
    # TODO: Permit supplying (incomplete?) hash
    x, y, r, g, b = [int(x) for x in argv[1:]]
    run_with(x, y, r, g, b)


if __name__ == '__main__':
    run_args(sys.argv)
