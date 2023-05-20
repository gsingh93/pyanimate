from __future__ import annotations

import logging
import math
import traceback
import uuid
from collections import OrderedDict
from copy import deepcopy
from enum import Enum
from typing import Optional, Self

from kiwisolver import Constraint, Expression, Solver, Term, Variable

from . import get_logger
from .renderer import Renderer
from .shape import Point as P
from .style import Anchor, Style


def copy_constraint(v: Variable, c: Constraint) -> tuple[Variable, Constraint]:
    e = c.expression()
    terms = []

    new_var = Variable()
    for term in e.terms():
        if term.variable() is v:
            terms.append(Term(new_var, term.coefficient()))
        else:
            terms.append(Term(term.variable(), term.coefficient()))

    return new_var, Constraint(Expression(terms, e.constant()), c.op(), c.strength())


logger = get_logger(__name__, indent=True)


class Align(str, Enum):
    TOP = "top"
    CENTER = "center"
    BOTTOM = "bottom"
    RIGHT = "right"
    LEFT = "left"


class Object:
    def __init__(self, canvas, width=None, height=None, style=None, **kwargs) -> None:
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

        short_id = self.__class__.__name__ + "." + str(self._id)[:4]
        self._x = Variable(f"x.{short_id}")
        self._y = Variable(f"y.{short_id}")
        self._w = Variable(f"w.{short_id}")
        self._h = Variable(f"h.{short_id}")
        self._width_constraint = None
        self._height_constraint = None
        self.children: OrderedDict[Object, P] = OrderedDict()
        self.parent: Optional[Object] = None

        self.canvas.solver.addConstraint(self._x >= 0)
        self.canvas.solver.addConstraint(self._y >= 0)
        self.canvas.solver.addConstraint(self._w >= 0)
        self.canvas.solver.addConstraint(self._h >= 0)
        if width is not None:
            self._width_constraint = self._w == width
            self.canvas.solver.addConstraint(self._width_constraint)
        if height is not None:
            self._height_constraint = self._h == height
            self.canvas.solver.addConstraint(self._height_constraint)

        self.cloned_to = None

    @property
    def pos(self) -> P[int]:
        self.canvas.solver.updateVariables()
        return P(int(self._x.value()), int(self._y.value()))

    @property
    def x(self) -> Variable:
        self.canvas.solver.updateVariables()
        return self._x

    @property
    def y(self) -> Variable:
        self.canvas.solver.updateVariables()
        return self._y

    @property
    def width(self) -> Variable:
        self.canvas.solver.updateVariables()
        return self._w

    @width.setter
    def width(self, val) -> None:
        if self._width_constraint:
            assert self.canvas.solver.hasConstraint(self._width_constraint)
            self.canvas.solver.removeConstraint(self._width_constraint)

        self._width_constraint = self._w == val
        self.canvas.solver.addConstraint(self._width_constraint)

    @property
    def height(self) -> Variable:
        self.canvas.solver.updateVariables()
        return self._h

    @height.setter
    def height(self, val) -> None:
        if self._height_constraint:
            assert self.canvas.solver.hasConstraint(self._height_constraint)
            self.canvas.solver.removeConstraint(self._height_constraint)

        self._height_constraint = self._h == val
        self.canvas.solver.addConstraint(self._height_constraint)

    def add(self, obj, offset=P(0, 0)) -> None:
        self.children[obj] = offset

        assert obj.parent is None
        obj.parent = self
        obj.style.parent_obj_style = self.style

    def find(self, obj: Object, remove: bool = False) -> Optional[Object]:
        for child in self.children:
            if child == obj:
                if remove:
                    del self.children[obj]

                child.parent = None
                return child

        for child in self.children:
            result = child.find(obj, remove)
            if result:
                return result

        return None

    def remove(self, obj: Object) -> bool:
        return self.find(obj, remove=True) is not None

    def replace(self, obj: Object, new: Object) -> None:
        # We need to search for `obj` as we need the actual object we're going to be
        # replacing, not just some object that is equal to it
        old = self.find(obj)
        if not old:
            raise ValueError(f"Object {obj} not found")

        # TODO: Speed this up by adding a cloned_from/cloned_to attribute that can find
        # the newer version of the object

        assert old.parent is not None
        parent = self.find(old.parent)
        assert parent is not None

        logger.debug(
            "Replacing %s with %s in parent %s", str(old), str(new), str(parent)
        )

        # Preserve the order of items in the dictionary
        parent.children = OrderedDict(
            (new, value) if key == old else (key, value)
            for key, value in parent.children.items()
        )
        old.parent = None
        new.parent = parent
        new.style.parent_obj_style = parent.style

    def prepare_impl(self, renderer: Renderer):
        for obj, offset in self.children.items():
            self.canvas.solver.addConstraint(self.x + offset.x == obj.x)
            self.canvas.solver.addConstraint(self.y + offset.y == obj.y)

    def prepare(self, renderer: Renderer):
        self.prepare_impl(renderer)

        for obj in self.children:
            logger.debug("Preparing child %s %s", obj, obj.pos)
            obj.prepare(renderer)

    def render(self, renderer: Renderer) -> None:
        for obj in self.children:
            logger.debug("Rendering child %s %s", obj, obj.pos)
            obj.render(renderer)

    def dump(self, indent: int = 0) -> str:
        res = " " * indent + str(self)
        for child in self.children:
            res += "\n" + child.dump(indent + 1)

        return res

    def clone(self, unique: bool = False):
        logger.debug("Cloning %s", self)
        c = deepcopy(self)

        if unique:
            c._id = uuid.uuid4()

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
        short_id = c.__class__.__name__ + "." + str(self._id)[:4]

        c._width_constraint = None
        c._height_constraint = None
        if self._width_constraint:
            v, constraint = copy_constraint(self._w, self._width_constraint)
            v.setName(f"w.{short_id}")
            c._w = v
            c._width_constraint = constraint
            c.canvas.solver.addConstraint(constraint)
        else:
            c._w = Variable(f"w.{short_id}")

        if self._height_constraint:
            v, constraint = copy_constraint(self._h, self._height_constraint)
            v.setName(f"h.{short_id}")
            c._h = v
            c._height_constraint = constraint
            c.canvas.solver.addConstraint(constraint)
        else:
            c._h = Variable(f"h.{short_id}")

        c._x = Variable(f"x.{short_id}")
        c._y = Variable(f"y.{short_id}")

        c.canvas.solver.addConstraint(c._x >= 0)
        c.canvas.solver.addConstraint(c._y >= 0)
        c.canvas.solver.addConstraint(c._w >= 0)
        c.canvas.solver.addConstraint(c._h >= 0)

        self.cloned_to = copy

        return copy

    def __str__(self) -> str:
        self.canvas.solver.updateVariables()
        return f"{type(self).__name__}({str(self._id)[:4]}, {self._w.value()}, {self._h.value()}) [{hex(id(self))}]"

    def __eq__(self, o: Self) -> bool:
        return self._id == o._id

    def __hash__(self):
        return hash(self._id)


class VLayout(Object):
    def __init__(self, align=Align.CENTER, **kwargs) -> None:
        super().__init__(**kwargs)
        self.align = align

    def __deepcopy__(self, memo):
        copy = super().__deepcopy__(memo)
        copy.align = deepcopy(self.align, memo)

        return copy

    def prepare_impl(self, renderer: Renderer):
        for obj, offset in self.children.items():
            self.canvas.solver.addConstraint(
                obj.x == self.x + (self.width / 2) - (obj.width / 2) + offset.x
            )
            constraint = self.width >= obj.width + offset.x
            self.canvas.solver.addConstraint(constraint)
            self.canvas.solver.updateVariables()

        children = list(self.children)
        for i in range(len(children)):
            obj = children[i]
            offset = self.children[obj]
            if i == 0:
                self.canvas.solver.addConstraint(obj.y == self.y + offset.y)
            else:
                prev_child = children[i - 1]
                self.canvas.solver.addConstraint(
                    obj.y == prev_child.y + prev_child.height + offset.y
                )

        constraint = sum(obj.height + offset.y for obj, offset in self.children.items())
        self.height = constraint


class HLayout(Object):
    def __init__(self, align=Align.CENTER, **kwargs) -> None:
        super().__init__(**kwargs)
        self.align = align

    def __deepcopy__(self, memo):
        copy = super().__deepcopy__(memo)
        copy.align = deepcopy(self.align, memo)

        return copy

    def prepare_impl(self, renderer: Renderer):
        for obj, offset in self.children.items():
            self.canvas.solver.addConstraint(
                obj.y == self.y + (self.height / 2) - (obj.height / 2) + offset.y
            )
            constraint = self.height >= obj.height + offset.y
            self.canvas.solver.addConstraint(constraint)

        children = list(self.children)
        for i in range(len(children)):
            obj = children[i]
            offset = self.children[obj]

            if i == 0:
                self.canvas.solver.addConstraint(obj.x == self.x + offset.x)
            else:
                self.canvas.solver.addConstraint(
                    obj.x == children[i - 1].x + children[i - 1].width + offset.x
                )

            self.canvas.solver.updateVariables()

        self.width = sum(obj.width + offset.x for obj, offset in self.children.items())


class Rectangle(Object):
    def render(self, renderer: Renderer) -> None:
        # Borders are mandatory at the moment, so the minimum size is 2x2
        assert self.width >= 2 and self.height >= 2

        x, y = self.x.value(), self.y.value()
        renderer.rectangle(
            P(x, y),
            # Subtract one from width and height to account for the border
            P(x + self.width.value() - 1, y + self.height.value() - 1),
            self.style,
        )
        super().render(renderer)


class Line(Object):
    # TODO: Support polar coordinates
    def __init__(self, *, end: P[float], start: P[float] = P(0, 0), **kwargs) -> None:
        super().__init__(**kwargs)
        self.start = start
        self.end = end

    def __deepcopy__(self, memo):
        copy = super().__deepcopy__(memo)

        copy.start = self.start
        copy.end = self.end

        return copy

    # def prepare_impl(self, renderer: Renderer):
    # self.width = self.end - self.start
    # self.height = self.end.y.value() - self.start.max(self.start.y, self.end.y)

    def render(self, renderer: Renderer) -> None:
        start = P(self.start.x.value(), self.start.y.value())
        end = P(self.end.x.value(), self.end.y.value())

        # renderer.line(self.start + pos, self.end + pos, self.style)
        renderer.line(start, end, self.style)


class Grid(Object):
    def __init__(self, step_size=100, **kwargs) -> None:
        super().__init__(**kwargs)
        self.step_size = step_size

    def prepare_impl(self, renderer: Renderer):
        if not self._width_constraint:
            self.width = renderer._w
        if not self._height_constraint:
            self.height = renderer._h

    def render(self, renderer: Renderer):
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


class TextBox(Rectangle):
    def __init__(self, text, align=Anchor.MIDDLE_MIDDLE, **kwargs) -> None:
        super().__init__(**kwargs)
        self._text = text

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        self._text = value

    def prepare_impl(self, renderer: Renderer) -> None:
        if self._width_constraint is None or self._height_constraint is None:
            _, _, right, bottom = renderer.text_bbox(self.text, self.style)

            if self._width_constraint is None:
                self.width = right

            if self._height_constraint is None:
                self.height = bottom

            self.canvas.solver.updateVariables()

    def render(self, renderer: Renderer) -> None:
        # We need to call super here first so the text appears on top of the box instead
        # of behind it
        super().render(renderer)

        renderer.text(
            self.text,
            (
                self.pos
                + P(int(self.width.value()), int(self.height.value())).floordiv(2)
            ),
            self.style.clone(anchor=Anchor.MIDDLE_MIDDLE),
        )

    def __deepcopy__(self, memo):
        copy = super().__deepcopy__(memo)
        copy._text = self._text

        return copy

    def __str__(self) -> str:
        self.canvas.solver.updateVariables()
        return f"{type(self).__name__}({str(self._id)[:4]}, {repr(self.text)}, {self.width}, {self.height}) [{hex(id(self))}]"


# TODO: Get rid of this and just use TextBox?
class Text(Object):
    def __init__(self, text: str, align=Align.LEFT, **kwargs) -> None:
        super().__init__(**kwargs)
        self._text = text
        self.align = align

    def __deepcopy__(self, memo):
        copy = super().__deepcopy__(memo)
        copy._text = deepcopy(self._text, memo)
        copy.align = deepcopy(self.align, memo)
        return copy

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text) -> None:
        self._text = text

    def prepare(self, renderer: Renderer) -> None:
        if self._width_constraint is None or self._height_constraint is None:
            _, _, right, bottom = renderer.text_bbox(self.text, self.style)

            if self._width_constraint is None:
                self.width = right

            if self._height_constraint is None:
                self.height = bottom

    def render(self, renderer: Renderer) -> None:
        if self.align == Align.RIGHT:
            renderer.text(
                self.text,
                self.pos + P(self.width, 0),
                self.style.clone(anchor=Anchor.TOP_RIGHT),
            )
        elif self.align == Align.CENTER:
            renderer.text(
                self.text,
                (self.pos + P(self.width.value(), self.height.value()).floordiv(2)),
                self.style.clone(anchor=Anchor.MIDDLE_MIDDLE),
            )
        else:
            renderer.text(self.text, self.pos, self.style)

    def __str__(self) -> str:
        self.canvas.solver.updateVariables()
        return f"{type(self).__name__}({str(self._id)[:4]}, {repr(self.text)}, {self.width}, {self.height}) [{hex(id(self))}]"


class Table(HLayout):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)


class DottedLine(Line):
    def __init__(self, dash_len=10, **kwargs) -> None:
        super().__init__(**kwargs)
        self.dash_len = dash_len

    def render(self, renderer: Renderer, pos=P(0, 0)) -> None:
        length = (
            (self.end.x - self.start.x) ** 2 + (self.end.y - self.start.y) ** 2
        ) ** 0.5

        if self.end.x != self.start.x:
            u = (self.end - self.start) / length
        else:
            u = P(0, 1)

        xy1 = self.start + pos
        for _ in range(0, int(length), self.dash_len):
            xy2 = xy1 + u.mul(self.dash_len // 2)
            renderer.line(xy1, xy2, self.style)
            xy1 = xy1 + u.mul(self.dash_len)


class Arrow(Line):
    def __init__(self, double_sided=False, arrowhead_ratio=0.2, **kwargs) -> None:
        super().__init__(**kwargs)
        self.double_sided = double_sided
        self.aratio = arrowhead_ratio

    def __deepcopy__(self, memo):
        copy = super().__deepcopy__(memo)
        copy.double_sided = deepcopy(self.double_sided)
        copy.aratio = deepcopy(self.aratio)
        return copy

    def render(self, renderer: Renderer) -> None:
        start = P(self.start.x.value(), self.start.y.value())
        end = P(self.end.x.value(), self.end.y.value())

        renderer.line(start, end, self.style)

        d = end - start
        length = d.mag()
        angle = d.radians()

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
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        if self._width_constraint is None:
            self.width = self.style.padding
        if self._height_constraint is None:
            self.height = self.style.padding


class Canvas(Object):
    def __init__(self, **kwargs) -> None:
        self.solver = Solver()
        super().__init__(self, **kwargs)

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
        copy.solver = Solver()

        copy.cloned_to = None

        # TODO: Every time a field is added this needs to be updated, is there a better
        # way to do this?
        copy.children = deepcopy(self.children, memo)
        copy.parent = deepcopy(self.parent, memo)
        copy.style = deepcopy(self.style, memo)

        c = copy
        short_id = c.__class__.__name__ + "." + str(self._id)[:4]

        c._width_constraint = None
        c._height_constraint = None
        if self._width_constraint:
            v, constraint = copy_constraint(self._w, self._width_constraint)
            v.setName(f"w.{short_id}")
            c._w = v
            c._width_constraint = constraint
            c.canvas.solver.addConstraint(constraint)
        else:
            c._w = Variable(f"w.{short_id}")

        if self._height_constraint:
            v, constraint = copy_constraint(self._h, self._height_constraint)
            v.setName(f"h.{short_id}")
            c._h = v
            c._height_constraint = constraint
            c.canvas.solver.addConstraint(constraint)
        else:
            c._h = Variable(f"h.{short_id}")

        c._x = Variable(f"x.{short_id}")
        c._y = Variable(f"y.{short_id}")

        c.canvas.solver.addConstraint(c._x >= 0)
        c.canvas.solver.addConstraint(c._y >= 0)
        c.canvas.solver.addConstraint(c._w >= 0)
        c.canvas.solver.addConstraint(c._h >= 0)

        self.cloned_to = copy

        return copy

    def add(self, obj, offset=P(0, 0)) -> None:
        super().add(obj, offset.add(self.style.padding))

    def render(self, renderer: Renderer) -> None:
        self.solver.addConstraint(self.x == 0)
        self.solver.addConstraint(self.y == 0)

        self.solver.addConstraint(self.width <= renderer._w)
        self.solver.addConstraint(self.height <= renderer._h)

        self.prepare(renderer)

        self.solver.updateVariables()

        for obj in self.children:
            logger.debug(
                "Rendering %s %s %s",
                obj,
                P(obj.width.value(), obj.height.value()),
                obj.pos,
            )
            obj.render(renderer)

        for obj, offset in self.children.items():
            self.solver.addConstraint(self.width >= offset.x + obj.width)
            self.solver.addConstraint(self.height >= offset.y + obj.height)

        # TODO: How to crop consistently across all frames? Crop at the end?
        # renderer.set_dimensions(P(self.width.value() * 1.5, self.height.value() * 1.5))
