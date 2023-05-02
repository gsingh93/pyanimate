from collections import namedtuple
from typing import Tuple, Union


class Point(namedtuple("Point", ["x", "y"])):
    __slots__ = ()

    def __new__(cls, x: Union["Point", Tuple, int] = 0, y=0):
        if isinstance(x, (Point, tuple)):
            x, y = x

        return super().__new__(cls, x, y)

    # def _calc_cartesian(self):
    #     self._x = self._r * math.cos(self._a)
    #     self._y = self._r * math.sin(self._a)

    # def _calc_polar(self):
    #     self._r = math.sqrt(self._x**2 + self._y**2)
    #     self._a = math.atan2(self._y, self._x)

    # def cartesian(self, x=None, y=None):
    #     if not x:
    #         # act as getter
    #         return (self._x, self._y)
    #     elif type(x) == tuple:
    #         self._x = float(x[0])
    #         self._y = float(x[1])
    #         self._calc_polar()
    #     elif not x == None and not y == None:
    #         self._x = float(x)
    #         self._y = float(y)
    #         self._calc_polar()

    # def polar(self, r=None, a=None):
    #     if not r:
    #         # act as getter
    #         return (self._r, self._a)
    #     elif type(r) == tuple:
    #         self._r = float(r[0])
    #         self._a = float(r[1])
    #         self._calc_cartesian()
    #     elif not r == None and not a == None:
    #         self._r = float(r)
    #         self._a = float(a)
    #         self._calc_cartesian()

    def ints(self):
        return (int(self.x), int(self.y))

    # @property
    # def x(self):
    #     return self._x

    # @x.setter
    # def x(self, val):
    #     self._x = float(val)
    #     self._calc_polar()

    # @property
    # def y(self):
    #     return self._y

    # @y.setter
    # def y(self, val):
    #     self._y = float(val)
    #     self._calc_polar()

    # @property
    # def r(self):
    #     return self._r

    # @r.setter
    # def r(self, val):
    #     self._r = float(val)
    #     self._calc_cartesian()

    # @property
    # def a(self):
    #     return self._a

    # @a.setter
    # def a(self, val):
    #     self._a = float(val)
    #     self._calc_cartesian()

    # def __repr__(self):
    #     return "Point({}, {})({}, {})".format(
    #         self._x, self._y, self._r, self._a
    #     )

    def __add__(self, other: Union["Point", Tuple, int]):
        if isinstance(other, (Point, tuple)):
            return Point(self.x + other[0], self.y + other[1])

        return Point(self.x + other, self.y + other)

    def __sub__(self, other: Union["Point", Tuple, int]):
        if isinstance(other, (Point, tuple)):
            return Point(self.x - other[0], self.y - other[1])

        return Point(self.x - other, self.y - other)

    def __mul__(self, val):
        return Point(self.x * val, self.y * val)

    def __floordiv__(self, val: int):
        return Point(self.x // val, self.y // val)

    def __truediv__(self, val: int):
        return Point(self.x / val, self.y / val)

    def __radd__(self, other: Union["Point", Tuple, int]):
        return self + other

    def __rmul__(self, val):
        return self * val
