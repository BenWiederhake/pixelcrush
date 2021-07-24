#!/usr/bin/env python3

from flask import Flask, g, jsonify, make_response, redirect, request, Response
from PIL import Image
import hashlib
import io
import struct
import time

SIZE = (1024, 1024)
CACHE_FILENAME = 'place.data'
HASH_ALGORITHM = hashlib.sha256
HASH_BYTES = 32
POST_STRUCT = struct.Struct('<HH3B16s' + str(HASH_BYTES) + 's')  # X, Y, R, G, B, Nonce, Hash
ADMIN_HASH = b'\x8f\xec\x8f\x2e\xb9\x43\x3f\xb2\xf5\xf8\xa6\x39\x38\x30\x69\x0d\x71\x6d\xed\x53\x45\x37\x62\xbf\x99\x74\x53\xf4\x25\xec\x44\xbf'
PROJECT_HOMEPAGE = 'https://github.com/BenWiederhake/pixelcrush'


def chunk_list(l, chunk_size):
    assert len(l) % chunk_size == 0
    return [l[i * chunk_size:(i + 1) * chunk_size] for i in range(len(l) // chunk_size)]


class CrushState:
    def __init__(self):
        expected_length = SIZE[0] * SIZE[1] * (3 * 1 + HASH_BYTES)
        print('Loading {} bytes from {} ...'.format(expected_length, CACHE_FILENAME))
        # If the file doesn't exist yet:
        # $ python3 -c 'fp = open("empty.data", "wb"); fp.write(b"\xff" * (1024*1024*3)); fp.write(b"\x00" * (1024*1024*32))'
        with open(CACHE_FILENAME, 'rb') as fp:
            data = fp.read()
        assert len(data) == expected_length
        start_hardness = (SIZE[0] * SIZE[1] * 3)
        self.img = Image.new('RGB', SIZE)
        self.img.putdata([tuple(rgb) for rgb in chunk_list(data[:start_hardness], 3)])
        self.hardness = [bytes(c) for c in chunk_list(data[start_hardness:], HASH_BYTES)]
        self.png_data = None
        self.produce_png()
        print('Initialized.')

    def produce_png(self):
        data = self.png_data
        if data is None:
            data = self.compute_png()
            self.png_data = data
        return data

    def compute_png(self):
        b = io.BytesIO()
        self.img.save(b, 'png')
        b.seek(0)
        return b.read()

    def hardness_at(self, y):
        idx = y * SIZE[0]
        return self.hardness[idx:idx + SIZE[0]]

    def try_set(self, xy, rgb, new_hash):
        index = xy[0] + xy[1] * SIZE[0]
        old_hash = self.hardness[index]
        if old_hash >= new_hash:
            return old_hash
        self.hardness[index] = new_hash
        self.img.putpixel(xy, rgb)
        self.png_data = None

    def save(self):
        data = bytearray()
        for px in self.img.getdata():
            data.extend(px)
        for h in self.hardness:
            data.extend(h)
        with open(time.strftime('/tmp/pixelcrush_save_%s.data'), 'wb') as fp:
            fp.write(data)


app = Flask(__name__)


@app.route('/')
def index():
    return redirect(PROJECT_HOMEPAGE)


@app.route("/place.png")
def place_png():
    png_data = app.crusher.produce_png()
    return Response(png_data, mimetype='image/png')


# $ echo -ne 'a\0' | curl -s 'http://127.0.0.1:5000/row_hardness' --data-binary @- | hd
@app.route("/row_hardness", methods=["POST"])
def row_hardness():
    request_data = request.get_data()
    try:
        y, = struct.unpack('<H', request_data)
    except struct.error:
        return make_response('Expected 2 bytes, little-endian, encoding the y-value of the row', 400)

    if y >= SIZE[1]:
        return make_response('Out of {} bounds ({:04x})'.format(SIZE, y), 400)

    return make_response(b''.join(app.crusher.hardness_at(y)), 200)


# $ echo -ne 'a\0b\0zA 0123456789abcdef\x2f\x71\x27\xb9\x7e\xa1\x25\x18\x06\xed\x37\xa3\x6f\xf0\xa1\x5a\xf4\x03\x07\xdd\x42\x60\x5b\x22\x42\x42\xbf\xa1\xde\x13\xce\xe0' | curl -s 'http://127.0.0.1:5000/post' --data-binary @- | hd
@app.route("/post", methods=["POST"])
def post_pixel():
    request_data = request.get_data()
    try:
        x, y, r, g, b, nonce, hash_expected = POST_STRUCT.unpack(request_data)
    except struct.error:
        return make_response('Expected {} bytes'.format(POST_STRUCT.size), 400)

    if x >= SIZE[0] or y >= SIZE[1]:
        return make_response('Out of {} bounds'.format(SIZE), 400)

    hash_actual = HASH_ALGORITHM(request_data[:-HASH_BYTES]).digest()
    if hash_actual != hash_expected:
        return make_response('Hash mismatch', 400)

    hash_best = app.crusher.try_set((x, y), (r, g, b), hash_actual)

    if hash_best is not None:
        return make_response(hash_best, 409)  # HTTP 409 Conflict; inform the caller about the currently best hash

    return ''


# $ curl -s 'http://127.0.0.1:5000/save?secret=%49%20%74%6f%6c%64%20%79%6f%75%3a%20%49%27%6d%20%6e%6f%74%20%74%68%61%74%20%73%74%75%70%69%64%21' -d ''
@app.route("/save", methods=["POST"])
def do_save():
    actual_hash = HASH_ALGORITHM(request.args.get('secret', '').encode()).digest()
    if actual_hash != ADMIN_HASH:
        return make_response('', 404)

    app.crusher.save()

    return ':)'


@app.before_first_request
def init_crusher():
    app.crusher = CrushState()


if __name__ == "__main__":
    app.run()
