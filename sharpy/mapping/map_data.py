from typing import List

from sc2.pixel_map import PixelMap
from sc2.position import Point2
from array import array


class MapData:
    def __init__(self, pixel_map:PixelMap):
        self._data: List[bool] = []
        self.width = pixel_map.width
        self.height = pixel_map.height
        self.max = self.width * self.height
        # Don't ask what happens here, no idea... Seems to work
        for x in range(0, pixel_map.height):
            for y in reversed(range(0, pixel_map.width)):
                self._data.append(pixel_map.is_set((y,x)))

        self._data.reverse()
        #self._data = array("i", list)

    def index(self, x: int, y: int):
        # Index is this negative value, because... Python?
        return -self.width * (y + 1) + x

    def set(self, x: int, y: int, value: bool):
        index = self.index(x, y)
        self._data[index] = value

    def invert(self, x: int, y: int):
        index = self.index(x, y)
        self._data[index] = not self._data[index]

    def get(self, x: int, y: int) ->  bool:
        index = self.index(x, y)
        return self._data[index]

    def print(self, wide=False):
        for y in range(self.height):
            for x in range(self.width):
                print("#" if self.get(x, y) else " ", end=(" " if wide else ""))
            print("")

    def save_image(self, filename):
        import numpy as np
        myarray = np.asarray(self._data)
        # for i in range(self.width):
        #     for j in range(self.height):
        #         data[i][j] = [100, 150, 200, 250]
        #data = [(0, 0, self.get(x, y)*255) for y in range(self.height) for x in range(self.width)]
        from PIL import Image

        #size = myarray.shape[::-1]
        databytes = np.packbits(myarray)
        im = Image.frombytes(mode='1', size=tuple((self.width, self.height)), data=databytes)

        #im = Image.fromarray(myarray * 255, mode='L').convert('1')
        #im = Image.new("1", (self.width, self.height))
        #im.putdata(data)
        im.save(filename)