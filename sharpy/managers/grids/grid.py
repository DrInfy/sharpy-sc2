import math
import os
from abc import abstractmethod

from s2clientprotocol.debug_pb2 import Color

from sc2.position import Point2, Point3
from .rectangle import Rectangle
from .blocker_type import BlockerType

class Grid:
    def __init__(self, width, height):
        self.height = height
        self.width = width
        self.height = height
        self._data = [[0 for y in range(height)] for x in range(width)]

    def set(self, x: int, y: int, value):
        #print(f"{x},{y})")
        self._data[x][y] = value

    def get(self, x:int, y: int):
        """Get value from position, no checking for performance"""
        #print(f'{x}, {y}')
        return self._data[x][y]

    def __getitem__(self, pos:Point2):
        """ Example usage: is_pathable = self._game_info.pathing_grid[Point2((20, 20))] == 0 """
        if not self.is_inside(pos):
            return self.get_default()

        return self.get(math.floor(pos[0]), math.floor(pos[1]))

    @abstractmethod
    def get_default(self):
        ...

    def is_inside(self, pos:Point2):
        return 0 <= pos[0] < self.width and 0 <= pos[1] < self.height

    def query_area(self, position: Point2, fillType: BlockerType, check) -> bool:
        """ <summary>
         Query that fails if any is true.
         </summary>
         <returns>True if all cells pass check func. </returns>
        """
        area = self.get_area(position, fillType)
        return self.query_rect(area, check)

    def query_direction(self, start: Point2, step: Point2, steps: int, check) -> bool:
        position = start
        for i in range(0, steps):
            position += step
            if not check(self[position]):
                return False
        return True

    def query_rect(self, rect: Rectangle, check) -> bool:
        minx = max(rect.x, 0)
        miny = max(rect.y, 0)
        maxx = min(rect.right, self.width - 1)
        maxy = min(rect.bottom, self.height - 1)

        for x in range(minx, maxx):
            for y in range(miny, maxy):
                if not check(self.get(x, y)):
                    return False
        return True

    def fill_area(self, pos: Point2, fill_type: BlockerType, func):
        area = self.get_area(pos, fill_type)
        self.fill_rect(area, func)

    def get_area(self, position: Point2, fillType: BlockerType) -> Rectangle:
        x = math.floor(position.x)
        y = math.floor(position.y)

        if fillType == BlockerType.Building1x1:
            w = 1
            h = 1
        elif fillType == BlockerType.Building2x2:
            w = 2
            h = 2
        elif fillType == BlockerType.Building3x3:
            w = 3
            h = 3
        elif fillType == BlockerType.Building4x4:
            w = 4
            h = 4
        elif fillType == BlockerType.Building5x5:
            w = 5
            h = 5
        elif fillType == BlockerType.Building6x6:
            w = 6
            h = 6
        elif fillType == BlockerType.Minerals:
            w = 2
            h = 1
        else:
            raise Exception('invalid fill type')

        wStart = math.ceil(x - w / 2)
        hStart = math.ceil(y - h / 2)
        return Rectangle(wStart, hStart, w, h)

    def fill_rect(self, rect: Rectangle, func):
        minx = max(rect.x, 0)
        miny = max(rect.y, 0)
        maxx = min(rect.right, self.width - 1)
        maxy = min(rect.bottom, self.height - 1)

        for x in range(minx, maxx):
            for y in range(miny, maxy):
                self.set(x, y, func(self.get(x, y)))

    def fill_rect_func(self, rect: Rectangle, func):
        minx = max(rect.x, 0)
        miny = max(rect.y, 0)
        maxx = min(rect.right, self.width - 1)
        maxy = min(rect.bottom, self.height - 1)

        for x in range(minx, maxx):
            for y in range(miny, maxy):
                self.set(x, y, func(self.get(x, y), Point2((x, y))))

    def save_image(self, filename, color_func):
        import numpy as np

        image_data = []
        for y in range(0, self.height):
            for x in range(0, self.width):
                y_value = self.height - 1 - y
                #print(f'{x}, {y_value}')
                image_data.append(self.color_to_value(color_func(self.get(x, y_value))))

        myarray = np.asarray(image_data, dtype=np.uint32)
        from PIL import Image

        #databytes = np.packbits(myarray)
        im = Image.frombytes(mode='RGBA', size=tuple((self.width, self.height)), data=myarray)

        if not os.path.exists('data'):
            os.mkdir('data')
        im.save(os.path.join("data", filename))

    def color_to_value(self, color: Point3) -> int:
        return color[0] + color[1] * 256 + color[2] * 256 * 256