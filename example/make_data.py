#!/usr/bin/env python3

from PIL import Image

IMG_FILENAME = 'hello.png'
OUTPUT_FILENAME = 'hello.data'


def make_data(img, hardness_transparent, hardness_opaque):
    assert img.size == (1024, 1024), img.size
    assert img.mode == 'RGBA', img.mode
    assert len(hardness_transparent) == 32  # hash length
    assert len(hardness_opaque) == 32  # hash length
    data_rgb = bytearray()
    data_hardness = bytearray()
    for px in img.getdata():
        assert len(px) == 4
        data_rgb.extend(px[:3])
        if px[3] == 0:
            data_hardness.extend(hardness_transparent)
        elif px[3] == 255:
            data_hardness.extend(hardness_opaque)
        else:
            raise ValueError(px)
    return data_rgb + data_hardness


def run():
    img = Image.open(IMG_FILENAME)
    data = make_data(img, b'\xff' * 1 + b'\x00' * 31, b'\xff' * 3 + b'\x00' * 29)
    with open(OUTPUT_FILENAME, 'wb') as fp:
        fp.write(data)


if __name__ == '__main__':
    run()
