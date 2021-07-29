#!/usr/bin/env python3

from flask import abort, Flask, g, jsonify, make_response, redirect, request, Response
from PIL import Image
import hashlib
import io
import os
import struct
import time

SIZE = (1024, 1024)
CACHE_FILENAME = 'place.data'
HASH_ALGORITHM = hashlib.sha256
HASH_BYTES = 32
POST_STRUCT = struct.Struct('<HH3B16s' + str(HASH_BYTES) + 's')  # X, Y, R, G, B, Nonce, Hash
OVERWRITE_STRUCT = struct.Struct('<HH3B')  # X, Y, R, G, B
ADMIN_HASH = b'\x8f\xec\x8f\x2e\xb9\x43\x3f\xb2\xf5\xf8\xa6\x39\x38\x30\x69\x0d\x71\x6d\xed\x53\x45\x37\x62\xbf\x99\x74\x53\xf4\x25\xec\x44\xbf'
PROJECT_HOMEPAGE = 'https://github.com/BenWiederhake/pixelcrush'

# This is very silly, but it's arguably easier than reading it from a file or configuring nginx/apache for it:
FAVICON = b'\x00\x00\x01\x00\x01\x00\x10\x10\x00\x00\x01\x00 \x00h\x04\x00\x00\x16\x00\x00\x00(\x00\x00\x00\x10\x00\x00\x00 \x00\x00\x00\x01\x00 \x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xf0F:\xffa\x89\xb9\xff\xee\xef\xf6\xffeH\x80\xff\xdf\x8e\xe6\xffb\xa4\x01\xff\xe0\x19L\xff\xea\xfeN\xff\x08\xce>\xff\x89\x14H\xffp\x0ek\xff\xd2\x88\xba\xff]\r\x89\xff\xa5"\xcd\xff\x866\x8e\xff\xf9>\x13\xff\x91\x80\x16\xff\x0e\xc6\xbe\xff\xc7\x8d\x81\xff\x9aY\xff\xff\xa3\x05I\xff\x1ac\xd7\xff4\xdd\xce\xff\xf2\xb5p\xffs\xf2\x95\xff\xf4\xd2\x0c\xff\xbd\x8c\xb9\xffH\xe3)\xff\x1f*;\xff\xd1\x90M\xff\xa3\x8ac\xff\xcd;\xe8\xff\xbe\xab\x9a\xffY_a\xff\'\x14{\xff}\r\xeb\xff\xdc\xc4\xa9\xff\x04\xf7H\xffnI\xc6\xfft40\xff&T\xe1\xff\xa8_>\xff\xf3\x19C\xfft\xa4\x9a\xff\x87\xf5\xd4\xff\x97\xa2J\xff\xa2\xfcX\xff\x81aa\xffD\xa6\xb8\xff9O\xce\xff\x14\x18O\xffv\xcck\xff9U\xad\xffj\xb6t\xff\xf9\xbd\x99\xff/\xa6\xdf\xff\x93q\xbb\xff\xbdG\x06\xff\xc9kD\xff\xb4h\x1a\xff\xbc\x9aN\xff \xa8<\xff=>n\xff*\x01\xb1\xff\xbe\x08\r\xffJe\x98\xffgg\xf7\xff\x15\x7f\xfb\xff_\xd4\xa6\xff\xd2z_\xff\xa4\xba\xa3\xff\x82\\\xdc\xff\xa1_T\xff\x06\xbb\xc4\xffK9\xa8\xff\xe8\xaeD\xff\xd2Fq\xff\xf1\x19K\xffB\x8a\xf1\xff\x13\x81\x8f\xff\xe0\x00L\xffN\xc3\x9f\xff;\xe1\xc1\xffq{\x81\xff\xdc\xe1\xe4\xff\xfb \xff\xff\x0bw\xe9\xff3\x91\xdb\xff\xdf\xcf\x1c\xff<\xcc\x8f\xff\xe2\xd1+\xff\xfa9O\xff\x92\x07+\xff\xfc\xf8\xf1\xff9\x90%\xffQ4\xd6\xff1X\xf4\xff\xf1\xe6\xb6\xff\x0e\xd4\xde\xff\x8f)\xa5\xffu\xd3\xfe\xffR\xcc\xff\xffe\x18g\xff|]\xd7\xff">Y\xff\x8c\xe2G\xff)\x01G\xffBt\xf3\xff\x1c#\x8b\xff\xe7\t\xc7\xff\x1e\xfe\xf6\xff\x9e\xc7)\xffq\x0f\xa2\xff\xdb\xf4\xd4\xffE=\x01\xff\x7fgT\xff0(4\xff[\xc0\x05\xffU\xd7\x9f\xff\x8c\xae\xb8\xff\xdd\x06R\xff \x82*\xff.\xa1\x0c\xffG\x17\xa6\xff\x00\x1e\x07\xff\xf8]\xdb\xff\x81M\xc8\xff\xed\x80\x1e\xff\xe5\xee\x01\xff3\x1e\x04\xff\xac\x80z\xff>\xf4\xbd\xffT`y\xff4\xafr\xff1\xb2W\xff<\x129\xffw\xa5U\xff\xb8=\xaa\xffU"\xaa\xff\xf1\xd5\xaf\xff\xb0&\xa4\xffZ\x14\xdd\xff\xbc\xbc\xa6\xff\xad\x15\x92\xff\x96\xaf\x00\xff\xe7\x1c$\xff\x19\xa2\x1a\xff\xc8\xeeE\xffDyr\xff\xb1>[\xff]\x15\xf0\xff\x96cF\xff\'@B\xff\xa6\xa8U\xff\xc2\x93/\xff\xf1\xf5U\xffC\x88\x9f\xff\x9d \x8b\xff\x7f\xf2Y\xff$m\x0b\xff\x1fF\xc1\xff\x88%>\xff\xb6\xb3\x95\xff\xd8v\x1a\xff\xf4\xcf|\xff\x17\x07\x16\xff\x11\xe3\xf3\xff\xeal\x9c\xff\x8dY\xdd\xff\xc8\xd4\xe0\xff\xa9;\x9b\xff\x07w\xd1\xff\xe1]\x91\xff#\xbb\xf1\xff5\xd8!\xff\xca,U\xfft\x9ax\xff\xbc\xa6\x80\xffY\xad\xf6\xff?\x1bL\xff\xc7\xf9\xbe\xff\xdcC\\\xff@#\x10\xff:\xa5N\xff\xd2\x07,\xff=\x17\x82\xff\xb4h\r\xff\xb3!y\xff\x07F1\xff\x1c+\xb5\xff\xc4B\xf7\xff\xbev\x05\xffKE\xec\xff3\xfb\xf3\xff\xd2\x94\xc9\xff\x17\x08Y\xff\x93\xe0]\xff\xf8\xc81\xffb\n\xff\xffc\xe7\xb5\xff\x8c\xfb\xf4\xff\x86\x95\xf7\xffd\xcd\x1f\xff\xf5\x98\'\xff\x88\xd7\xbe\xffQ\xef}\xff\xe9\xf6\xc3\xff&m\xb1\xffw\x90\x1a\xff\xb6I\xc1\xff\xecq\x03\xff+cT\xffh\xda\x15\xff\x95\xbb\xbd\xffF\xbf\xaf\xff\x95\xbf\x8c\xff\xe9F\xc1\xff\xa6\xb1\xbf\xff\n-\xef\xff\xcb\xec \xff%\xbf\x16\xffW\x18\x15\xffQ\x08\x93\xffy\xf3\x00\xff\xa9.\xf1\xffWk\x18\xff:rw\xff\xc9g\x04\xffRd\xb7\xff\x8eAN\xff\xbe\xe2F\xff\x04M\x83\xffA6c\xffhL\x90\xff\x88\xf1\xbe\xff\xa9\xf3"\xff\xff\xeca\xff\x90OT\xfff\x9a\xac\xffb\xc6\x16\xff\x9a\x7f^\xff\xbc\xc1\x0e\xff\x11\x81h\xff\xb6\x11\xae\xff\xcf\xa4h\xff\xdd\x91\x15\xff\xad\xa8]\xff\xd8\xeax\xff\x9e\x8b\x12\xff\x89\x068\xff\x88\xb07\xffq\xa7>\xff\xbcU\xdc\xff\x0c\x07G\xff\xe4vg\xff\xf4M}\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'


def chunk_list(l, chunk_size):
    assert len(l) % chunk_size == 0
    return [l[i * chunk_size:(i + 1) * chunk_size] for i in range(len(l) // chunk_size)]


def count_leading_ones(pixel_hash):
    leading_ones = 0
    for b in pixel_hash:
        if b == 255:
            leading_ones += 8
            continue
        # Or better:
        # leading_ones += __builtin_clz(255 - b);
        # FIXME: Come on! This should only be two instructions!
        if b >= 0b11111110:
            leading_ones += 7
        elif b >= 0b11111100:
            leading_ones += 6
        elif b >= 0b11111000:
            leading_ones += 5
        elif b >= 0b11110000:
            leading_ones += 4
        elif b >= 0b11100000:
            leading_ones += 3
        elif b >= 0b11000000:
            leading_ones += 2
        elif b >= 0b10000000:
            leading_ones += 1
        break

    return leading_ones


def to_heat_rgb(pixel_hash):
    leading_ones = count_leading_ones(pixel_hash)
    leading_ones = max(0, leading_ones - 4)

    if leading_ones <= 15:
        # 0-4: black
        # to 15: gradient to red
        return (leading_ones * 17, 0, 0)
    elif leading_ones <= 30:
        # to 30: gradient to yellow
        return (255, (leading_ones - 15) * 17, 0)
    elif leading_ones <= 45:
        # to 45: gradient to white
        return (255, 255, (leading_ones - 30) * 17)
    elif leading_ones <= 60:
        # to 60: gradient to blue
        x = 255 - (leading_ones - 30) * 17
        return (x, x, 255)
    else:
        # beyond: magenta
        return (255, 0, 255)


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
        self.heatmap_data = None
        self.produce_png()
        self.produce_heatmap()
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

    def produce_heatmap(self):
        data = self.heatmap_data
        if data is None:
            data = self.compute_heatmap()
            self.heatmap_data = data
        return data

    def compute_heatmap(self):
        b = io.BytesIO()
        img = Image.new('RGB', SIZE)
        img.putdata([to_heat_rgb(h) for h in self.hardness])
        img.save(b, 'png')
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
        self.overwrite(xy, rgb)

    def overwrite(self, xy, rgb):
        self.img.putpixel(xy, rgb)
        self.png_data = None
        self.heatmap_data = None

    def save(self):
        data = bytearray()
        for px in self.img.getdata():
            data.extend(px)
        for h in self.hardness:
            data.extend(h)
        filename = time.strftime('pixelcrush_save_%s.data')
        filename = os.path.realpath(filename)
        with open(filename, 'wb') as fp:
            fp.write(data)
        return filename


app = Flask(__name__)


@app.route('/')
def index():
    return redirect(PROJECT_HOMEPAGE)


@app.route("/favicon.ico")
def favicon():
    return Response(FAVICON, mimetype='image/ico')


@app.route("/place.png")
def place_png():
    png_data = app.crusher.produce_png()
    return Response(png_data, mimetype='image/png')


@app.route("/heatmap.png")
def heatmap_png():
    heatmap_data = app.crusher.produce_heatmap()
    return Response(heatmap_data, mimetype='image/png')


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
    if len(request_data) % POST_STRUCT.size != 0 or len(request_data) == 0:
        return make_response('Expected {} bytes (or multiple thereof)'.format(POST_STRUCT.size), 400)

    response = bytearray()
    any_failed = False
    for i in range(len(request_data) // POST_STRUCT.size):
        single_request = request_data[i * POST_STRUCT.size:(i + 1) * POST_STRUCT.size]
        try:
            x, y, r, g, b, nonce, hash_expected = POST_STRUCT.unpack(single_request)
        except struct.error:
            return make_response('How did you do that? o.O', 400)

        if x >= SIZE[0] or y >= SIZE[1]:
            return make_response('Out of {} bounds'.format(SIZE), 400)

        hash_actual = HASH_ALGORITHM(single_request[:-HASH_BYTES]).digest()
        if hash_actual != hash_expected:
            return make_response('Hash mismatch', 400)

        hash_best = app.crusher.try_set((x, y), (r, g, b), hash_actual)

        if hash_best is None:
            # Success!
            response.extend(hash_actual)
        else:
            any_failed = True
            response.extend(hash_best)

    if any_failed:
        return make_response(response, 409)  # HTTP 409 Conflict; inform the caller about the currently best hash

    # Elide all successful responses. This is for two reasons:
    # - Maximum compatibility with old (single-shot) implementation
    # - Avoid unnecessary traffic
    return ''


# $ curl -s 'http://127.0.0.1:5000/save?secret=%49%20%74%6f%6c%64%20%79%6f%75%3a%20%49%27%6d%20%6e%6f%74%20%74%68%61%74%20%73%74%75%70%69%64%21' -d ''
@app.route("/save", methods=["POST"])
def do_save():
    actual_hash = HASH_ALGORITHM(request.args.get('secret', '').encode()).digest()
    if actual_hash != ADMIN_HASH:
        abort(404)

    filename = app.crusher.save()

    return filename


# $ SECRET=%49%20%74%6f%6c%64%20%79%6f%75%3a%20%49%27%6d%20%6e%6f%74%20%74%68%61%74%20%73%74%75%70%69%64%21 ./example/overwritepixel.py 500 501 255 255 255
@app.route("/overwrite_pixel", methods=["POST"])
def overwrite_pixel():
    actual_hash = HASH_ALGORITHM(request.args.get('secret', '').encode()).digest()
    if actual_hash != ADMIN_HASH:
        abort(404)

    request_data = request.get_data()
    try:
        x, y, r, g, b = OVERWRITE_STRUCT.unpack(request_data)
    except struct.error:
        return make_response('Expected {} bytes'.format(OVERWRITE_STRUCT.size), 400)

    if x >= SIZE[0] or y >= SIZE[1]:
        return make_response('Out of {} bounds'.format(SIZE), 400)

    app.crusher.overwrite((x, y), (r, g, b))

    return ':)'


@app.before_first_request
def init_crusher():
    app.crusher = CrushState()


if __name__ == "__main__":
    app.run()
