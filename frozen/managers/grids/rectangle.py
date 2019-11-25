class Rectangle:
    def __init__(self, x: int, y:int, width: int, height: int):
        assert isinstance(x, int)
        assert isinstance(y, int)
        assert isinstance(width, int)
        assert isinstance(height, int)
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    @property
    def right(self):
        return self.x + self.width

    @property
    def bottom(self):
        return self.y + self.height