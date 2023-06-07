from __future__ import annotations

import math
import sys
import uuid
from collections import OrderedDict
from copy import deepcopy
from enum import Enum
from typing import Generic, NotRequired, Self, TypeAlias, TypeVar, Unpack

from kiwisolver import UnsatisfiableConstraint

from . import get_logger
from .renderer import Renderer
from .shape import Point as P
from .solver import Constraint, Expression, Solver, Term, Variable
from .style import Anchor, Style, StyleParams

logger = get_logger(__name__, indent=True)


class Align(str, Enum):
    TOP = "top"
    CENTER = "center"
    BOTTOM = "bottom"
    RIGHT = "right"
    LEFT = "left"


class ObjectParamsNoCanvas(StyleParams):
    width: NotRequired[int | Variable | Term | Expression | None]
    height: NotRequired[int | Variable | Term | Expression | None]
    style: NotRequired[Style | None]


class ObjectParams(ObjectParamsNoCanvas):
    canvas: Canvas


class Object:
    def __init__(
        self,
        canvas: Canvas,
        *,
        width=None,
        height=None,
        style: Style | None = None,
        **kwargs: Unpack[StyleParams],
    ) -> None:
        # Construct a new Style that inherits from the parent
        if not style:
            # This will inherit from the default style
            style = Style(**kwargs)

        if kwargs:
            # This will inherit from the user-supplied style
            style = style.clone(**kwargs)

        self._id = uuid.uuid4()

        self.style = style
        self.canvas = canvas
        self.cloned_to = None

        self._x = Variable(f"x.{self.name}")
        self._y = Variable(f"y.{self.name}")
        self._w = Variable(f"w.{self.name}")
        self._h = Variable(f"h.{self.name}")
        self._width_constraint = None
        self._height_constraint = None
        self.children: OrderedDict[Object, P] = OrderedDict()
        self.parent: Object | None = None

        if width is not None:
            self._width_constraint = self._w == width
        if height is not None:
            self._height_constraint = self._h == height

    @property
    def name(self):
        return self.__class__.__name__ + "." + str(self._id)[:4]

    @property
    def pos(self) -> P[int]:
        self.canvas.solver.update()
        return P(int(self._x.value()), int(self._y.value()))

    @property
    def dim(self) -> P[int]:
        self.canvas.solver.update()
        return P(int(self._w.value()), int(self._h.value()))

    @property
    def x(self) -> Variable:
        self.canvas.solver.update()
        return self._x

    @property
    def y(self) -> Variable:
        self.canvas.solver.update()
        return self._y

    @property
    def width(self) -> Variable:
        self.canvas.solver.update()
        return self._w

    @width.setter
    def width(self, val: int | Variable) -> None:
        # if self._width_constraint and self.canvas.solver.hasConstraint(
        #     self._width_constraint
        # ):
        #     # assert self.canvas.solver.hasConstraint(self._width_constraint)
        #     self.canvas.solver.remove(self._width_constraint)

        self._width_constraint = self._w == val
        # self.canvas.solver.add(self._width_constraint)

    @property
    def height(self) -> Variable:
        self.canvas.solver.update()
        return self._h

    @height.setter
    def height(self, val: int | Variable) -> None:
        # if self._height_constraint and self.canvas.solver.hasConstraint(
        #     self._height_constraint
        # ):
        #     # assert self.canvas.solver.hasConstraint(self._height_constraint)
        #     self.canvas.solver.remove(self._height_constraint)

        self._height_constraint = self._h == val
        # self.canvas.solver.add(self._height_constraint)

    def add(self, obj: Object | ObjectProxy, offset: P = P(0, 0)) -> None:
        if isinstance(obj, _Proxy):
            obj = obj.latest()

        logger.debug("Adding %s to %s at offset %r", obj, self, offset)
        self.children[obj] = offset

        assert obj.parent is None
        obj.parent = self
        obj.style.parent_obj_style = self.style

    def remove(self, obj: Object | ObjectProxy) -> None:
        if isinstance(obj, _Proxy):
            obj = obj.latest()

        if obj not in self.children:
            raise ValueError(f"Object {obj} not found")

        del self.children[obj]
        obj.parent = None

    def prepare_impl(self, _renderer: Renderer) -> None:
        for obj, offset in self.children.items():
            c = self.x + offset.x == obj.x
            self.canvas.solver.add(c)
            self.canvas.solver.update()

            c = self.y + offset.y == obj.y
            self.canvas.solver.add(c)
            self.canvas.solver.update()

    def prepare(self, renderer: Renderer) -> None:
        self.canvas.solver.add(self._x >= 0)
        self.canvas.solver.add(self._y >= 0)
        self.canvas.solver.add(self._w >= 0)
        self.canvas.solver.add(self._h >= 0)

        if self._width_constraint:
            self.canvas.solver.add(self._width_constraint)
        if self._height_constraint:
            self.canvas.solver.add(self._height_constraint)

        self.canvas.solver.update()

        logger.debug("Preparing %s", self)

        self.prepare_impl(renderer)

        for obj, offset in self.children.items():
            logger.debug("Preparing child %s %s (offset %r)", obj, obj.pos, offset)
            obj.prepare(renderer)

        logger.debug("Finished preparing %s", self)

    def render(self, renderer: Renderer) -> None:
        for obj in self.children:
            logger.debug("Rendering child %s %s", obj, obj.pos)
            obj.render(renderer)

    def dump(self, indent=0) -> str:
        res = " " * indent + str(self)
        for child in self.children:
            res += "\n" + child.dump(indent + 1)

        return res

    def clone(self, unique=False) -> Self:
        logger.debug("Cloning %s", self)
        c = deepcopy(self)

        if unique:
            # TODO: We need to update all the variable names?
            c._id = uuid.uuid4()
            self.cloned_to = None

        return c

    def latest(self) -> Self:
        if self.cloned_to:
            return self.cloned_to.latest()

        return self

    def __deepcopy__(self, memo) -> Self:
        cls = self.__class__
        copy = cls.__new__(cls)

        # Because `__hash__` uses `self._id`, we need to copy that manually first before
        # calling `deepcopy`, otherwise the `deepcopy` implementation will throw some
        # exceptions
        copy._id = self._id
        logger.debug(
            "copying %s %s %s to %s %s %s",
            cls.__name__,
            id(self),
            hex(id(self)),
            cls.__name__,
            id(copy),
            hex(id(copy)),
        )

        memo[id(self)] = copy

        copy.canvas = deepcopy(self.canvas, memo)

        copy.cloned_to = None

        # TODO: Every time a field is added this needs to be updated, is there a better
        # way to do this?
        copy.children = deepcopy(self.children, memo)
        copy.parent = deepcopy(self.parent, memo)
        copy.style = deepcopy(self.style, memo)

        c = copy

        c._width_constraint = deepcopy(self._width_constraint, memo)
        c._height_constraint = deepcopy(self._height_constraint, memo)
        c._w = deepcopy(self._w, memo)
        c._h = deepcopy(self._h, memo)
        c._x = deepcopy(self._x, memo)
        c._y = deepcopy(self._y, memo)

        self.cloned_to = copy

        return copy

    def __str__(self) -> str:
        self.canvas.solver.update()
        return (
            f"{type(self).__name__}({str(self._id)[:4]}, {self.dim}) [{hex(id(self))}]"
        )

    def __eq__(self, o: Self) -> bool:
        return self._id == o._id

    def __hash__(self):
        return hash(self._id)


T = TypeVar("T", bound=Object)


class _Proxy(Generic[T]):
    _obj: T

    def __new__(cls, target: T):
        return super().__new__(cls)

    def __init__(self, obj: T) -> None:
        super().__setattr__("_obj", obj)

    def __getattr__(self, name: str):
        super().__setattr__("_obj", self._obj.latest())
        return getattr(self._obj, name)

    def __setattr__(self, name: str, value) -> None:
        super().__setattr__("_obj", self._obj.latest())
        setattr(self._obj, name, value)

    def latest(self) -> T:
        super().__setattr__("_obj", self._obj.latest())
        return self._obj

    def __str__(self) -> str:
        return f"Proxy[{str(self._obj)}]"


ObjectProxy: TypeAlias = _Proxy[Object]


def Proxy(target: T) -> T:
    # We use a factory function because you can't lie about the return type in `__new__`

    # TODO: type: ignore or cast?
    return _Proxy(target)  # type: ignore


class LayoutParams(ObjectParams):
    align: NotRequired[Align]


class LayoutParamsNoCanvas(ObjectParamsNoCanvas):
    align: NotRequired[Align]


# TODO: We can make this class handle even more logic from the subclasses
class Layout(Object):
    def __init__(
        self, *, align: Align = Align.CENTER, **kwargs: Unpack[ObjectParams]
    ) -> None:
        super().__init__(**kwargs)
        self.align = align

    def __deepcopy__(self, memo):
        copy = super().__deepcopy__(memo)
        copy.align = self.align

        return copy

    def get_center_constraint(self, obj: Object, offset: P) -> Constraint:
        raise NotImplementedError()

    def get_secondary_dim_constraint(self, obj: Object, offset: P) -> Constraint:
        raise NotImplementedError()

    def set_primary_dim_constraint(self) -> None:
        raise NotImplementedError()

    def get_linear_constraint(
        self, prev_obj: Object | None, obj: Object, offset: P
    ) -> Constraint:
        raise NotImplementedError()

    def prepare_impl(self, _renderer: Renderer) -> None:
        for obj, offset in self.children.items():
            c = self.get_center_constraint(obj, offset)
            self.canvas.solver.add(c)

            c = self.get_secondary_dim_constraint(obj, offset)
            self.canvas.solver.add(c)

            self.canvas.solver.update()

        prev_child = None
        for obj, offset in self.children.items():
            c = self.get_linear_constraint(prev_child, obj, offset)
            self.canvas.solver.add(c)

            prev_child = obj

            self.canvas.solver.update()

        self.set_primary_dim_constraint()


class VLayout(Layout):
    def get_center_constraint(self, obj: Object, offset: P) -> Constraint:
        return obj.x == self.x + (self.width / 2) - (obj.width / 2) + offset.x

    def get_secondary_dim_constraint(self, obj: Object, offset: P) -> Constraint:
        return self.width >= obj.width + offset.x

    def set_primary_dim_constraint(self) -> None:
        expr = sum(obj.height + offset.y for obj, offset in self.children.items())
        if self._height_constraint:
            self.canvas.solver.remove(self._height_constraint)
        self._height_constraint = self.height == expr
        self.canvas.solver.add(self._height_constraint)

    def get_linear_constraint(
        self, prev_obj: Object | None, obj: Object, offset: P
    ) -> Constraint:
        if prev_obj:
            return obj.y == prev_obj.y + prev_obj.height + offset.y
        else:
            return obj.y == self.y + offset.y


class HLayout(Layout):
    def get_center_constraint(self, obj: Object, offset: P) -> Constraint:
        return obj.y == self.y + (self.height / 2) - (obj.height / 2) + offset.y

    def get_secondary_dim_constraint(self, obj, offset) -> Constraint:
        return self.height >= obj.height + offset.y

    def set_primary_dim_constraint(self) -> None:
        expr = sum(obj.width + offset.x for obj, offset in self.children.items())
        if self._width_constraint:
            self.canvas.solver.remove(self._width_constraint)
        self._width_constraint = self.width == expr
        self.canvas.solver.add(self._width_constraint)

    def get_linear_constraint(
        self, prev_obj: Object | None, obj: Object, offset: P
    ) -> Constraint:
        if prev_obj:
            return obj.x == prev_obj.x + prev_obj.width + offset.x
        else:
            return obj.x == self.x + offset.x


class Rectangle(Object):
    def render(self, renderer: Renderer) -> None:
        x, y = self.x.value(), self.y.value()
        renderer.rectangle(
            P(x, y),
            # TODO: Should we be subtracting self.style.stroke_width?
            P(x + self.width.value() - 1, y + self.height.value() - 1),
            self.style,
        )
        super().render(renderer)


class GridParams(ObjectParams):
    step_size: NotRequired[int]


class GridParamsNoCanvas(ObjectParamsNoCanvas):
    step_size: NotRequired[int]


class Grid(Object):
    def __init__(self, *, step_size=100, **kwargs: Unpack[ObjectParams]) -> None:
        super().__init__(**kwargs)
        self.step_size = step_size

    def prepare_impl(self, renderer: Renderer) -> None:
        if self._width_constraint is None:
            w = renderer.context.w - self.style.padding
            logger.debug("New width for %s: %s", self, w)
            self._width_constraint = self.width == w
            self.canvas.solver.add(self._width_constraint)

        if self._height_constraint is None:
            h = renderer.context.h - self.style.padding
            logger.debug("New height for %s: %s", self, h)
            self._height_constraint = self.height == h
            self.canvas.solver.add(self._height_constraint)

    def render(self, renderer: Renderer) -> None:
        for i in range(0, int(self.width.value()), self.step_size):
            renderer.line(
                P(i + self.pos.x, self.pos.y),
                P(i + self.pos.x, self.height.value()),
                self.style,
            )
        for i in range(0, int(self.height.value()), self.step_size):
            renderer.line(
                P(self.pos.x, i + self.pos.y),
                P(self.width.value(), i + self.pos.y),
                self.style,
            )


class TextBoxParams(ObjectParams):
    align: NotRequired[Align]


class TextBoxParamsNoCanvas(ObjectParamsNoCanvas):
    align: NotRequired[Align]


class TextBox(Rectangle):
    def __init__(
        self, text: str, *, align=Align.CENTER, **kwargs: Unpack[ObjectParams]
    ) -> None:
        super().__init__(**kwargs)
        self._text = text
        self._align = align

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        self._text = value

    @property
    def align(self) -> str:
        return self._align

    def prepare_impl(self, renderer: Renderer) -> None:
        # See if any dimensions are dynamically sized
        if self._width_constraint is None or self._height_constraint is None:
            _, _, right, bottom = renderer.text_bbox(self.text, self.style)

            # For dynamically sized dimensions, we make sure to include room for the
            # padding
            if self._width_constraint is None:
                logger.debug("New width for %s: %s", self, right)
                self._width_constraint = self.width == right + self.style.padding * 2
                self.canvas.solver.add(self._width_constraint)

            if self._height_constraint is None:
                logger.debug("New height for %s: %s", self, bottom)
                self._height_constraint = self.height == bottom + self.style.padding * 2
                self.canvas.solver.add(self._height_constraint)

            self.canvas.solver.update()

    def render(self, renderer: Renderer) -> None:
        # We need to call super here first so the text appears on top of the box instead
        # of behind it
        super().render(renderer)

        middle_y = int(self.height.value() / 2)
        if self.align == Align.RIGHT:
            renderer.text(
                self.text,
                self.pos + P(int(self.width.value()), middle_y),
                self.style.clone(anchor=Anchor.MIDDLE_RIGHT),
            )
        elif self.align == Align.CENTER:
            renderer.text(
                self.text,
                self.pos + P(self.width.value() // 2, middle_y),
                self.style.clone(anchor=Anchor.MIDDLE_MIDDLE),
            )
        else:
            assert self.align == Align.LEFT
            renderer.text(
                self.text,
                self.pos + P(0, middle_y),
                self.style.clone(anchor=Anchor.MIDDLE_LEFT),
            )

    def __deepcopy__(self, memo):
        copy = super().__deepcopy__(memo)
        copy._text = self._text
        copy._align = self._align

        return copy

    def __str__(self) -> str:
        self.canvas.solver.update()
        return f"{type(self).__name__}({str(self._id)[:4]}, {repr(self.text)}, {self.dim}) [{hex(id(self))}]"


class Table(HLayout):
    def __init__(self, **kwargs: Unpack[LayoutParams]) -> None:
        super().__init__(**kwargs)


class LineParams(ObjectParams):
    vec: P


class LineParamsNoCanvas(ObjectParamsNoCanvas):
    vec: P


class Line(Object):
    def __init__(self, *, vec: P, **kwargs: Unpack[ObjectParams]) -> None:
        super().__init__(**kwargs)
        self._vec = vec

    @classmethod
    def from_polar(cls, mag: float, angle: float, **kwargs) -> Line:
        vec = P.from_polar(mag, angle)
        return cls(vec=vec, **kwargs)

    def prepare_impl(self, _renderer: Renderer) -> None:
        if self._width_constraint is None:
            w = self._vec.x

            logger.debug("New width for %s: %s", self, w)
            self.canvas.solver.add((self.width == w) | "strong")
            self.canvas.solver.add((self.width == -w) | "strong")

        if self._height_constraint is None:
            h = self._vec.y

            logger.debug("New height for %s: %s", self, h)
            self.canvas.solver.add((self.height == h) | "strong")
            self.canvas.solver.add((self.height == -h) | "strong")

    def __deepcopy__(self, memo):
        copy = super().__deepcopy__(memo)

        copy._vec = deepcopy(self._vec, memo)

        return copy

    def render(self, renderer: Renderer) -> None:
        start = self.pos
        end = start + self._vec.get()
        renderer.line(start, end, self.style)


class DottedLineParams(LineParams):
    dash_len: NotRequired[int]


class DottedLineParamsNoCanvas(LineParamsNoCanvas):
    dash_len: NotRequired[int]


class DottedLine(Line):
    def __init__(self, *, dash_len=10, **kwargs: Unpack[LineParams]) -> None:
        super().__init__(**kwargs)
        self._dash_len = dash_len

    def __deepcopy__(self, memo):
        copy = super().__deepcopy__(memo)

        copy._dash_len = self._dash_len

        return copy

    def render(self, renderer: Renderer) -> None:
        v = self._vec.get()

        length = int(v.mag)
        u = v.unit()

        xy1 = self.pos
        for _ in range(0, length, self._dash_len):
            xy2 = xy1 + u.mul(self._dash_len // 2)
            renderer.line(xy1, xy2, self.style)
            xy1 = xy1 + u.mul(self._dash_len)


class ArrowParams(LineParams):
    double_sided: NotRequired[bool]
    arrowhead_ratio: NotRequired[float]


class ArrowParamsNoCanvas(LineParamsNoCanvas):
    double_sided: NotRequired[bool]
    arrowhead_ratio: NotRequired[float]


class Arrow(Line):
    def __init__(
        self,
        *,
        double_sided=False,
        arrowhead_ratio=0.2,
        **kwargs: Unpack[LineParams],
    ) -> None:
        super().__init__(**kwargs)
        self.double_sided = double_sided
        self.aratio = arrowhead_ratio

    def __deepcopy__(self, memo):
        copy = super().__deepcopy__(memo)
        copy.double_sided = self.double_sided
        copy.aratio = self.aratio
        return copy

    def render(self, renderer: Renderer) -> None:
        super().render(renderer)

        start = self.pos
        end = start + self._vec.get()

        d = end - start
        length = d.mag
        angle = d.radians

        head_length = length * self.aratio
        head_angle = math.pi / 4  # 45 degrees in radians

        head_dx1 = head_length * math.cos(angle + head_angle)
        head_dy1 = head_length * math.sin(angle + head_angle)
        head_dx2 = head_length * math.cos(angle - head_angle)
        head_dy2 = head_length * math.sin(angle - head_angle)

        renderer.line(end, end - P(head_dx1, head_dy1), self.style)
        renderer.line(end, end - P(head_dx2, head_dy2), self.style)

        if self.double_sided:
            renderer.line(
                start,
                start + P(head_dx1, head_dy1),
                self.style,
            )
            renderer.line(start, start + P(head_dx2, head_dy2), self.style)


class Spacer(Object):
    def __init__(self, **kwargs: Unpack[ObjectParams]) -> None:
        super().__init__(**kwargs)

        if self._width_constraint is None:
            self.width = self.style.padding
        if self._height_constraint is None:
            self.height = self.style.padding


class Canvas(Object):
    def __init__(self, **kwargs: Unpack[ObjectParamsNoCanvas]) -> None:
        self._solver = Solver()
        super().__init__(self, **kwargs)

    @property
    def solver(self) -> Solver:
        return self._solver

    def __deepcopy__(self, memo):
        cls = self.__class__
        copy = cls.__new__(cls)

        # Because `__hash__` uses `self._id`, we need to copy that manually first before
        # calling `deepcopy`, otherwise the `deepcopy` implementation will throw some
        # exceptions
        copy._id = self._id
        logger.verbose(
            "copying %s %s %s to %s %s %s",
            self.__class__.__name__,
            id(self),
            hex(id(self)),
            copy.__class__.__name__,
            id(copy),
            hex(id(copy)),
        )

        memo[id(self)] = copy

        copy.canvas = copy
        copy._solver = Solver()

        copy.cloned_to = None

        # TODO: Every time a field is added this needs to be updated, is there a better
        # way to do this?
        copy.children = deepcopy(self.children, memo)
        copy.parent = deepcopy(self.parent, memo)
        copy.style = deepcopy(self.style, memo)

        c = copy

        c._width_constraint = deepcopy(self._width_constraint, memo)
        c._height_constraint = deepcopy(self._height_constraint, memo)
        c._w = deepcopy(self._w, memo)
        c._h = deepcopy(self._h, memo)
        c._x = deepcopy(self._x, memo)
        c._y = deepcopy(self._y, memo)

        self.cloned_to = copy

        return copy

    def add(self, obj: Object | _Proxy[Object], offset: P = P(0, 0)) -> None:
        if isinstance(obj, _Proxy):
            obj = obj.latest()

        super().add(obj, offset.add(self.style.padding))

    def rectangle(self, **kwargs: Unpack[ObjectParamsNoCanvas]) -> Rectangle:
        return Proxy(Rectangle(canvas=self, **kwargs))

    def textbox(self, text: str, **kwargs: Unpack[TextBoxParamsNoCanvas]) -> TextBox:
        return Proxy(TextBox(canvas=self, text=text, **kwargs))

    def line(self, **kwargs: Unpack[LineParamsNoCanvas]) -> Line:
        return Proxy(Line(canvas=self, **kwargs))  # pylint: disable=missing-kwoa

    def dotted_line(self, **kwargs: Unpack[DottedLineParamsNoCanvas]) -> DottedLine:
        return Proxy(DottedLine(canvas=self, **kwargs))

    def arrow(self, **kwargs: Unpack[ArrowParamsNoCanvas]) -> Arrow:
        return Proxy(Arrow(canvas=self, **kwargs))

    def spacer(self, **kwargs: Unpack[ObjectParamsNoCanvas]) -> Spacer:
        return Proxy(Spacer(canvas=self, **kwargs))

    def vlayout(self, **kwargs: Unpack[LayoutParamsNoCanvas]) -> VLayout:
        return Proxy(VLayout(canvas=self, **kwargs))

    def hlayout(self, **kwargs: Unpack[LayoutParamsNoCanvas]) -> HLayout:
        return Proxy(HLayout(canvas=self, **kwargs))

    def grid(self, **kwargs: Unpack[GridParamsNoCanvas]) -> Grid:
        return Proxy(Grid(canvas=self, **kwargs))

    def prepare(self, renderer: Renderer) -> None:
        self.solver.reset()

        self._width_constraint = None
        self._height_constraint = None

        self.solver.add(self.x == 0)
        self.solver.add(self.y == 0)

        super().prepare(renderer)

    def render(self, renderer: Renderer) -> None:
        self.prepare(renderer)

        # Make sure that children are not rendered outside of the canvas
        try:
            # An implementation detail of kiwisolver is that if adding a constraint
            # doesn't violate any other constraints, the solution for the variable will
            # not change. Since we want the Canvas to be as small as possible, we need
            # to add the constraints that limit the minimum size of the Canvas first, so
            # that some solution will be picked, and then we need to add the constraints
            # that limit the maximum size afterwards, so that the smallest solution will
            # still be chosen if there is no constraint violation.
            for obj in self.children:
                self.solver.add(obj.x + obj.width <= self.width)
                self.solver.add(obj.y + obj.height <= self.height)

            self.solver.add(self.width <= renderer.context.w)
            self.solver.add(self.height <= renderer.context.h)
        except UnsatisfiableConstraint:
            logger.error("Image exceeds bounds")
            logger.error("%s", self.solver.dumps())
            sys.exit(1)

        self.solver.update()

        for obj in self.children:
            logger.debug(
                "Rendering %s at %s",
                obj,
                obj.pos,
            )
            obj.render(renderer)

        logger.debug("Finished rendering canvas:\n%s", self.dump())
