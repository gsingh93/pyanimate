from __future__ import annotations

import math
import uuid
from collections import OrderedDict
from copy import deepcopy
from enum import Enum
from typing import Optional, Self

from . import get_logger
from .renderer import Renderer
from .shape import Point as P
from .solver import Constraint, Solver, Variable
from .style import Anchor, Style

logger = get_logger(__name__, indent=True)


class Align(str, Enum):
    TOP = "top"
    CENTER = "center"
    BOTTOM = "bottom"
    RIGHT = "right"
    LEFT = "left"


class Object:
    def __init__(
        self,
        canvas: Canvas,
        width=None,
        height=None,
        style: Style | None = None,
        **kwargs,
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

        short_id = self.__class__.__name__ + "." + str(self._id)[:4]
        self._x = Variable(f"x.{short_id}")
        self._y = Variable(f"y.{short_id}")
        self._w = Variable(f"w.{short_id}")
        self._h = Variable(f"h.{short_id}")
        self._width_constraint = None
        self._height_constraint = None
        self.children: OrderedDict[Object, P] = OrderedDict()
        self.parent: Optional[Object] = None

        self.canvas.solver.add(self._x >= 0)
        self.canvas.solver.add(self._y >= 0)
        self.canvas.solver.add(self._w >= 0)
        self.canvas.solver.add(self._h >= 0)
        if width is not None:
            self._width_constraint = self._w == width
            self.canvas.solver.add(self._width_constraint)
        if height is not None:
            self._height_constraint = self._h == height
            self.canvas.solver.add(self._height_constraint)

        self.cloned_to = None

        # Contains all constraints that relate this object to its parent
        self.constraints: list[Constraint] = []

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
        if self._width_constraint:
            assert self.canvas.solver.hasConstraint(self._width_constraint)
            self.canvas.solver.remove(self._width_constraint)

        self._width_constraint = self._w == val
        self.canvas.solver.add(self._width_constraint)

    @property
    def height(self) -> Variable:
        self.canvas.solver.update()
        return self._h

    @height.setter
    def height(self, val: int | Variable) -> None:
        if self._height_constraint:
            assert self.canvas.solver.hasConstraint(self._height_constraint)
            self.canvas.solver.remove(self._height_constraint)

        self._height_constraint = self._h == val
        self.canvas.solver.add(self._height_constraint)

    def add(self, obj: Object, offset=P(0, 0)) -> None:
        logger.debug("Adding %s to %s at offset %s", obj, self, offset)
        self.children[obj] = offset

        assert obj.parent is None
        obj.parent = self
        logger.debug(self.style)
        obj.style.parent_obj_style = self.style

    def find(self, obj: Object, remove: bool = False) -> Optional[Object]:
        for child in self.children:
            if child == obj:
                if remove:
                    del self.children[obj]

                    child.parent = None
                    obj.parent = None
                    child.clear_constraints()
                    obj.clear_constraints()

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
        old.clear_constraints()
        new.parent = parent
        new.style.parent_obj_style = parent.style

    def prepare_impl(self, _renderer: Renderer) -> None:
        for obj, offset in self.children.items():
            # print(self.pos, offset, offset.get())
            c = self.x + offset.x == obj.x
            self.canvas.solver.add(c)
            self.canvas.solver.update()
            # print(c)
            obj.constraints.append(c)

            c = self.y + offset.y == obj.y
            self.canvas.solver.add(c)
            self.canvas.solver.update()
            # print(c)
            obj.constraints.append(c)

    def prepare(self, renderer: Renderer):
        logger.debug("Preparing %s", self)
        self.prepare_impl(renderer)

        for obj in self.children:
            logger.debug("Preparing child %s %s", obj, obj.pos)
            obj.prepare(renderer)

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

    def clear_constraints(self) -> None:
        for c in self.constraints:
            # assert self.canvas.solver.hasConstraint(c)
            if self.canvas.solver.hasConstraint(c):
                self.canvas.solver.remove(c)

        self.constraints.clear()

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
        # copy.children = OrderedDict()
        # for child, offset in self.children.items():
        #     x = offset.x
        #     y = offset.y
        #     new_var = None
        #     if isinstance(x, Variable):
        #         logger.warning("Unimplemented")
        #     elif isinstance(x, Expression):
        #         # TODO: all of the variables of `x` reference objects in the original,
        #         # we want to copy this expression so that the variables reference the
        #         # corresponding objects in the copy

        #         # TODO: What if we implemented deepcopy for Variable and Expression? The
        #         # deepcopy infrastructure should then make all the copies for us, and
        #         # they should be already attached to the correct objects/solver.
        #         new_var, new_e = copy_expression(x)

        #     copy.children[deepcopy(child, memo)] = P(x, y)
        copy.children = deepcopy(self.children, memo)

        # print("old")
        # for child, offset in self.children.items():
        #     if isinstance(offset.x, Expression):
        #         print(offset.x, offset.y)
        #         print(offset.x.variables()[0], offset.y.variables()[0])
        # print("new")
        # for child, offset in copy.children.items():
        #     if isinstance(offset.x, Expression):
        #         print(offset.x, offset.y)
        #         print(offset.x.variables()[0], print(offset.y.variables()[0]))

        copy.parent = deepcopy(self.parent, memo)
        copy.style = deepcopy(self.style, memo)

        c = copy
        # short_id = c.__class__.__name__ + "." + str(self._id)[:4]

        # print(1, memo)
        c._width_constraint = deepcopy(self._width_constraint, memo)
        c._height_constraint = deepcopy(self._height_constraint, memo)
        # print(2, memo)
        c._w = deepcopy(self._w, memo)
        c._h = deepcopy(self._h, memo)

        # print("c.w, c.h", c._w, c._h)
        # if c._width_constraint:
        #     c.canvas.solver.add(c._width_constraint)
        # if c._height_constraint:
        #     c.canvas.solver.add(c._height_constraint)

        # c._width_constraint = None
        # c._height_constraint = None
        # if self._width_constraint:
        #     v, constraint = copy_constraint(self._w, self._width_constraint)
        #     v.setName(f"w.{short_id}")
        #     c._w = v
        #     c._width_constraint = constraint
        #     c.canvas.solver.add(constraint)
        # else:
        #     c._w = Variable(f"w.{short_id}")

        # if self._height_constraint:
        #     v, constraint = copy_constraint(self._h, self._height_constraint)
        #     v.setName(f"h.{short_id}")
        #     c._h = v
        #     c._height_constraint = constraint
        #     c.canvas.solver.add(constraint)
        # else:
        #     c._h = Variable(f"h.{short_id}")

        c._x = deepcopy(self._x, memo)  # Variable(f"x.{short_id}")
        c._y = deepcopy(self._y, memo)  # Variable(f"y.{short_id}")

        # c.canvas.solver.add(c._x >= 0)
        # c.canvas.solver.add(c._y >= 0)
        # c.canvas.solver.add(c._w >= 0)
        # c.canvas.solver.add(c._h >= 0)

        self.cloned_to = copy

        c.constraints = []
        for constraint in self.constraints:
            c.constraints.append(constraint)

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


class VLayout(Object):
    def __init__(self, align=Align.CENTER, **kwargs) -> None:
        super().__init__(**kwargs)
        self.align = align

    def __deepcopy__(self, memo):
        copy = super().__deepcopy__(memo)
        copy.align = deepcopy(self.align, memo)

        return copy

    def prepare_impl(self, _renderer: Renderer) -> None:
        for obj, offset in self.children.items():
            c = obj.x == self.x + (self.width / 2) - (obj.width / 2) + offset.x
            self.canvas.solver.add(c)
            obj.constraints.append(c)

            c = self.width >= obj.width + offset.x
            self.canvas.solver.add(c)
            self.canvas.solver.update()
            obj.constraints.append(c)

        children = list(self.children)
        for i, obj in enumerate(children):
            offset = self.children[obj]
            if i == 0:
                c = obj.y == self.y + offset.y
                self.canvas.solver.add(c)
                obj.constraints.append(c)
            else:
                prev_child = children[i - 1]
                c = obj.y == prev_child.y + prev_child.height + offset.y
                self.canvas.solver.add(c)
                obj.constraints.append(c)

        # TODO: Add to obj constraints?
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

    def prepare_impl(self, _renderer: Renderer) -> None:
        for obj, offset in self.children.items():
            c = obj.y == self.y + (self.height / 2) - (obj.height / 2) + offset.y
            self.canvas.solver.add(c)
            obj.constraints.append(c)

            c = self.height >= obj.height + offset.y
            self.canvas.solver.add(c)
            self.canvas.solver.update()
            obj.constraints.append(c)

        children = list(self.children)
        for i, obj in enumerate(children):
            offset = self.children[obj]

            if i == 0:
                c = obj.x == self.x + offset.x
                self.canvas.solver.add(c)
                obj.constraints.append(c)
            else:
                c = obj.x == children[i - 1].x + children[i - 1].width + offset.x
                self.canvas.solver.add(c)
                obj.constraints.append(c)

            self.canvas.solver.update()

        # TODO: Add to obj constraints?
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
    # TODO: Convert absolute to relative
    def __init__(
        self, *, end: P[float], start: P[float] = P(0, 0), relative=True, **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.relative = relative
        self.start = start
        self.end = end

        # self._x = self.start.x
        # self._y = self.start.y

    def __deepcopy__(self, memo):
        copy = super().__deepcopy__(memo)

        copy.start = self.start
        copy.end = self.end
        copy.relative = self.relative

        return copy

    # def prepare_impl(self, renderer: Renderer):
    #     # The user passed in absolute coordinates, we need to convert them to relative
    #     if not self.relative:
    #         self.start = self.parent.
    # self.width = self.end - self.start
    # self.height = self.end.y.value() - self.start.max(self.start.y, self.end.y)

    def render(self, renderer: Renderer) -> None:
        assert self.parent

        offset = self.parent.children[self].get()
        start = self.start.get() + offset
        end = self.end.get() + offset
        if not self.relative:
            start = start - self.parent.pos
            end = end - self.parent.pos

        # renderer.line(self.start + pos, self.end + pos, self.style)
        renderer.line(start, end, self.style)


class Grid(Object):
    def __init__(self, step_size=100, **kwargs) -> None:
        super().__init__(**kwargs)
        self.step_size = step_size

    def prepare_impl(self, renderer: Renderer) -> None:
        if not self._width_constraint:
            self.width = renderer.width()
        if not self._height_constraint:
            self.height = renderer.height()

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


class TextBox(Rectangle):
    def __init__(self, text: str, align=Anchor.MIDDLE_MIDDLE, **kwargs) -> None:
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

            self.canvas.solver.update()

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
        self.canvas.solver.update()
        return f"{type(self).__name__}({str(self._id)[:4]}, {repr(self.text)}, {self.dim}) [{hex(id(self))}]"


# TODO: Get rid of this and just use TextBox?
# class Text(Object):
#     def __init__(self, text: str, align=Align.LEFT, **kwargs) -> None:
#         super().__init__(**kwargs)
#         self._text = text
#         self.align = align

#     def __deepcopy__(self, memo):
#         copy = super().__deepcopy__(memo)
#         copy._text = deepcopy(self._text, memo)
#         copy.align = deepcopy(self.align, memo)
#         return copy

#     @property
#     def text(self):
#         return self._text

#     @text.setter
#     def text(self, text) -> None:
#         self._text = text

#     def prepare(self, renderer: Renderer) -> None:
#         if self._width_constraint is None or self._height_constraint is None:
#             _, _, right, bottom = renderer.text_bbox(self.text, self.style)

#             if self._width_constraint is None:
#                 self.width = right

#             if self._height_constraint is None:
#                 self.height = bottom

#     def render(self, renderer: Renderer) -> None:
#         if self.align == Align.RIGHT:
#             renderer.text(
#                 self.text,
#                 self.pos + P(self.width, 0),
#                 self.style.clone(anchor=Anchor.TOP_RIGHT),
#             )
#         elif self.align == Align.CENTER:
#             renderer.text(
#                 self.text,
#                 (self.pos + P(self.width.value(), self.height.value()).floordiv(2)),
#                 self.style.clone(anchor=Anchor.MIDDLE_MIDDLE),
#             )
#         else:
#             renderer.text(self.text, self.pos, self.style)

#     def __str__(self) -> str:
#         self.canvas.solver.update()
#         return f"{type(self).__name__}({str(self._id)[:4]}, {repr(self.text)}, {self.width}, {self.height}) [{hex(id(self))}]"


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
        copy.double_sided = self.double_sided
        copy.aratio = self.aratio
        return copy

    def render(self, renderer: Renderer) -> None:
        assert self.parent

        offset = self.parent.children[self].get()
        logger.info("offset: %s", offset)
        logger.info("self.start,self.end: %s %s", self.start.get(), self.end.get())
        start = self.start.get() + offset
        end = self.end.get() + offset
        logger.info("start,end: %s %s", start, end)
        if not self.relative:
            logger.info("relative (%s): %s %s", self.parent.pos, start, end)
            start = start - self.parent.pos
            end = end - self.parent.pos

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
        copy.solver = deepcopy(self.solver, memo)  # Solver()

        copy.cloned_to = None

        # TODO: Every time a field is added this needs to be updated, is there a better
        # way to do this?
        # copy.children = OrderedDict()
        # for child, offset in self.children.items():
        #     print(offset.get())
        #     copy.children[deepcopy(child, memo)] = offset
        copy.children = deepcopy(self.children, memo)
        # print("old [canvas]")
        # for child, offset in self.children.items():
        #     if isinstance(offset.x, Expression):
        #         print(offset.x, offset.y)
        #         print(offset.x.variables()[0], offset.y.variables()[0])
        # print("new [canvas]")
        # for child, offset in copy.children.items():
        #     if isinstance(offset.x, Expression):
        #         print(offset.x, offset.y)
        #         print(offset.x.variables()[0], print(offset.y.variables()[0]))
        copy.parent = deepcopy(self.parent, memo)
        copy.style = deepcopy(self.style, memo)

        c = copy
        # short_id = c.__class__.__name__ + "." + str(self._id)[:4]

        # print(3, memo)
        c._width_constraint = deepcopy(self._width_constraint, memo)
        c._height_constraint = deepcopy(self._height_constraint, memo)
        # print(4, memo)
        c._w = deepcopy(self._w, memo)
        c._h = deepcopy(self._h, memo)
        # if c._width_constraint:
        #     c.canvas.solver.add(c._width_constraint)
        # if c._height_constraint:
        #     c.canvas.solver.add(c._height_constraint)

        # if self._width_constraint:
        #     v, constraint = copy_constraint(self._w, self._width_constraint)
        #     v.setName(f"w.{short_id}")
        #     c._w = v
        #     c._width_constraint = constraint
        #     c.canvas.solver.add(constraint)
        # else:
        #     c._w = Variable(f"w.{short_id}")

        # if self._height_constraint:
        #     v, constraint = copy_constraint(self._h, self._height_constraint)
        #     v.setName(f"h.{short_id}")
        #     c._h = v
        #     c._height_constraint = constraint
        #     c.canvas.solver.add(constraint)
        # else:
        #     c._h = Variable(f"h.{short_id}")

        c._x = deepcopy(self._x, memo)  # Variable(f"x.{short_id}")
        c._y = deepcopy(self._y, memo)  # Variable(f"y.{short_id}")

        # c.canvas.solver.add(c._x >= 0)
        # c.canvas.solver.add(c._y >= 0)
        # c.canvas.solver.add(c._w >= 0)
        # c.canvas.solver.add(c._h >= 0)

        self.cloned_to = copy

        return copy

    def add(self, obj: Object, offset=P(0, 0)) -> None:
        # If we're adding an Arrow with absolute coordinates, convert the absolute
        # coordinates to relative by updating offset
        if isinstance(obj, Arrow) and not obj.relative:
            offset += obj.start
            obj.start -= offset
            obj.end -= offset
            obj.relative = True
        super().add(obj, offset.add(self.style.padding))

    def render(self, renderer: Renderer) -> None:
        self.solver.add(self.x == 0)
        self.solver.add(self.y == 0)

        self.solver.add(self.width <= renderer.width())
        self.solver.add(self.height <= renderer.height())

        self.prepare(renderer)

        # for obj in self.children:
        #     self.solver.add(obj.x + obj.width <= renderer.width())
        #     self.solver.add(obj.y + obj.height <= renderer.height())

        self.solver.update()

        # print(self.solver.dumps())

        for obj in self.children:
            logger.debug(
                "Rendering %s %s %s",
                obj,
                P(obj.width.value(), obj.height.value()),
                obj.pos,
            )
            obj.render(renderer)

        for obj, offset in self.children.items():
            c = self.width >= offset.x + obj.width
            self.solver.add(c)
            self.solver.update()
            # print(c)
            obj.constraints.append(c)

            c = self.height >= offset.y + obj.height
            self.solver.add(c)
            self.solver.update()
            # print(c)
            obj.constraints.append(c)

        # TODO: How to crop consistently across all frames? Crop at the end?
        # renderer.set_dimensions(P(self.width.value() * 1.5, self.height.value() * 1.5))
