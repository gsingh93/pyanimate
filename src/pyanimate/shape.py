from __future__ import annotations

import copy
import math
from typing import Generic, Never, Self, TypeAlias, TypeVar, Union, cast, overload

from .solver import Expression, Term, Variable

T = TypeVar("T", bound=int | float | Term | Expression | Variable)

# TODO: Is there a better way to do this?
UnresolvedShape: TypeAlias = Union[
    "Shape[Variable]",
    "Shape[Term]",
    "Shape[Expression]",
    "Shape[Variable | Term]",
    "Shape[Variable | Expression]",
    "Shape[Term | Expression]",
    "Shape[Variable | Term | Expression]",
    "Shape[int | float | Variable]",
    "Shape[int | float | Term]",
    "Shape[int | float | Expression]",
    "Shape[int | float | Variable | Term]",
    "Shape[int | float | Variable | Expression]",
    "Shape[int | float | Term | Expression]",
    "Shape[int | float | Variable | Term | Expression]",
]


class Shape(tuple[T, ...], Generic[T]):
    def __new__(cls, *args: T) -> Self:
        return tuple.__new__(cls, args)

    def __neg__(self) -> Self:
        """Negate each field of the shape"""
        return self.mul(-1)

    def add(self, other: int | float, /) -> Self:
        """Add a scalar to all fields of the shape"""
        x = (i + other for i in self)
        return type(self)(*x)

    @overload
    def __add__(self, other: Shape[int] | Shape[float], /) -> Self:
        """Adding a shape of floats or ints to any shape should return Self"""

    @overload
    def __add__(self: Shape[int] | Shape[float], other: Shape, /) -> Shape:
        """Adding any shape to a shape of floats or ints should return the type of the
        other Shape"""

    def __add__(self, other: Shape, /):
        x = (i + j for i, j in zip(self, other))
        return type(self)(*x)

    def sub(self, other: int | float, /) -> Self:
        """Subtract a scalar from all fields of the shape"""
        x = (i - other for i in self)
        return type(self)(*x)

    @overload
    def __sub__(self, other: Shape[int] | Shape[float], /) -> Self:
        """Subtracting a shape of floats or ints to any shape should return Self"""

    @overload
    def __sub__(self: Shape[int] | Shape[float], other: Shape, /) -> Shape:
        """Subtracting any shape to a shape of floats or ints should return the type of
        the other Shape
        """

    def __sub__(self, other: Self, /):
        x = (i - j for i, j in zip(self, other))
        return type(self)(*x)

    def mul(self, other: int | float, /) -> Self:
        """Multiply all fields of the shape by a scalar"""
        # TODO: This is a hack to preserve the type of Self if it is a Shape[int] (which
        # is needed for `Color`). Maybe there's a way to check the value of `T` at
        # runtime?
        res = []
        int_array = True
        for i in self:
            if not isinstance(i, int):
                int_array = False
            res.append(i * other)

        if int_array:
            res = map(int, res)
        return type(self)(*res)

    @overload
    def __mul__(self, other: Shape[int] | Shape[float], /) -> Self:
        """Multiplying a shape of floats or ints to any shape should return Self"""

    @overload
    def __mul__(self: Shape[int] | Shape[float], other: Shape, /) -> Shape:
        """Multiplying any shape to a shape of floats or ints should return the type of
        the other Shape
        """

    @overload
    def __mul__(
        self: UnresolvedShape,
        other: UnresolvedShape,
        /,
    ) -> Never:
        """Multiplying a shape containing Variables, Terms, or Expressions by another
        shape containing Variables, Terms, or Expressions should not be allowed"""

    def __mul__(self, other: Self, /) -> Self:
        resolved = cast(Point[int | float], self.get())
        other_resolved = cast(Point[int | float], other.get())

        # Multiplying two tuples requires both to already be resolved
        assert resolved == self and other_resolved == other

        x = (i * j for i, j in zip(resolved, other_resolved))
        return type(self)(*x)

    def __truediv__(self, other: Shape[int] | Shape[float], /) -> Self:
        x = (i / j for i, j in zip(self, other))
        return type(self)(*x)

    def truediv(self, other: int | float, /) -> Self:
        x = (i / other for i in self)
        return type(self)(*x)

    def __radd__(self, other: Self, /) -> Self:
        return self + other

    def __rsub__(self, other: Self, /) -> Self:
        return self - other

    def __rmul__(self, other: Self, /) -> Self:
        return self * other

    def __str__(self) -> str:
        return f"{type(self).__name__}{tuple(self.get())}"

    # TODO: Ideally we want the return type to be `Self[int] | Self[float]`, but that
    # would require HKT
    def get(self) -> Self:
        args = []
        has_float = False
        for i in self:
            if isinstance(i, int):
                assert not has_float
                args.append(i)
            elif isinstance(i, float):
                has_float = True
                args.append(i)
            else:
                args.append(i.value())

        if has_float:
            args = map(float, args)
            return type(self)(*args)
        else:
            args = map(int, args)
            return type(self)(*args)

    def __deepcopy__(
        self,
        memo: dict[int, Self],
    ) -> Self:
        # We need to deepcopy a tuple, not the original object, otherwise the
        # deepcopy implementation will not use the tuple's deepcopy method.
        return type(self)(*copy.deepcopy(tuple(self), memo))


class Point(Shape[T], Generic[T]):
    @property
    def x(self) -> T:
        return self[0]

    @property
    def y(self) -> T:
        return self[1]

    @classmethod
    def from_polar(cls, mag: float, radians: float) -> Point[T]:
        return cls(mag * math.cos(radians), mag * math.sin(radians))

    @property
    def mag(self) -> float:
        resolved = cast(Point[int | float], self.get())
        return (resolved.x**2 + resolved.y**2) ** 0.5

    @property
    def radians(self) -> float:
        resolved = cast(Point[int | float], self.get())
        return math.atan2(resolved.y, resolved.x)

    def unit(self) -> Point[T]:
        assert self.mag != 0
        return self.truediv(self.mag)

    def __str__(self) -> str:
        x = None
        y = None
        if not isinstance(self.x, (int, float)) or not isinstance(self.y, (int, float)):
            x, y = self.get()

        s = "P("
        if x is None:
            s += str(self.x)
        else:
            s += f"{self.x} ({x})"

        s += ", "

        if y is None:
            s += str(self.y)
        else:
            s += f"{self.y} ({y})"

        s += ")"

        return s

    def __repr__(self) -> str:
        return f"{self} [0x{id(self):x}]"


class Color(Shape[int]):
    def __new__(  # pylint: disable=arguments-differ
        cls, r: int, g: int, b: int, a: int = 255
    ) -> Self:
        return tuple.__new__(cls, (r, g, b, a))

    @classmethod
    def from_alpha(cls, alpha: int) -> Color:
        return cls(0, 0, 0, alpha)

    @property
    def r(self) -> int:
        return self[0]

    @property
    def g(self) -> int:
        return self[1]

    @property
    def b(self) -> int:
        return self[2]

    @property
    def a(self) -> int:
        return self[3]


BLACK = Color(0, 0, 0)
RED = Color(255, 0, 0)
GREEN = Color(0, 255, 0)
BLUE = Color(0, 0, 255)
YELLOW = Color(255, 255, 0)
CYAN = Color(0, 255, 255)
MAGENTA = Color(255, 0, 255)
GREY = Color(128, 128, 128)
GRAY = GREY
WHITE = Color(255, 255, 255)
