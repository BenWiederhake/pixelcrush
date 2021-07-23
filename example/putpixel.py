#!/usr/bin/env python3

import hashlib
import random
import requests
import struct
import sys
import time

SIZE = (1024, 1024)
HASH_ALGORITHM = hashlib.sha256
HASH_BYTES = 32
PAYLOAD_STRUCT = struct.Struct('<HH3B')
POST_STRUCT = struct.Struct('<HH3B16s' + str(HASH_BYTES) + 's')  # X, Y, R, G, B, Nonce, Hash
URL = 'http://127.0.0.1:5000/post'


def incr_nonce(nonce):
    for i in range(16):
        if nonce[i] == 255:
            nonce[i] = 0
        else:
            nonce[i] += 1
            break


def beat_hash(payload, old_hash):
    print('Trying to beat hash {} for payload {} ...'.format(old_hash, payload), file=sys.stderr)
    tries = 0
    next_report = 100
    nonce = bytearray([random.randrange(255) for _ in range(16)])
    while True:
        new_hash = HASH_ALGORITHM(payload + nonce).digest()
        if new_hash > old_hash:
            return nonce, new_hash
        incr_nonce(nonce)
        tries += 1
        if tries >= next_report:
            print('  {} unsuccessful attempts'.format(tries), file=sys.stderr)
            next_report = next_report * 2


def submit_pixel(post_data):
    response = requests.post(URL, post_data)

    if response.status_code == 200:
        # Done!
        return None
    elif response.status_code == 400:
        raise AssertionError('Something went very wrong. Here is a hint from the server: >>>{}<<<'.format(response.text))
    elif response.status_code == 409:
        # Need to try again
        assert len(response.content) == HASH_BYTES
        return response.content
    else:
        raise AssertionError('Huh? Received HTTP {} from server, along with >>>{}<<<'.format(response.status_code, response.content))


def run_with(x, y, r, g, b, old_hash=None):
    assert 0 <= x < SIZE[0]
    assert 0 <= y < SIZE[1]
    payload = PAYLOAD_STRUCT.pack(x, y, r, g, b)
    if old_hash is None:
        old_hash = bytes(16)

    while True:
        nonce, hashdata = beat_hash(payload, old_hash)
        post_data = payload + nonce + hashdata
        assert len(post_data) == POST_STRUCT.size
        print('Submitting {} with hash {} ...'.format((x, y, r, g, b), hashdata), file=sys.stderr)
        old_hash = submit_pixel(post_data)
        if old_hash is None:
            break


def run_args(argv):
    if len(argv) != 1 + 5:
        print('USAGE: {} X Y R G B'.format(argv[0]), file=sys.stderr)
        exit(1)
    # TODO: Permit supplying (incomplete?) hash
    x, y, r, g, b = [int(x) for x in argv[1:]]
    run_with(x, y, r, g, b)


if __name__ == '__main__':
    run_args(sys.argv)
