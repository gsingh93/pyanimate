from __future__ import annotations

import logging
import math
import traceback
import uuid
from collections import OrderedDict
from copy import deepcopy
from enum import Enum
from typing import Optional, Self

from .renderer import Renderer
from .shape import Point as P
from .style import Anchor, Style


class CustomAdapter(logging.LoggerAdapter):
    @staticmethod
    def indent():
        indentation_level = len(traceback.extract_stack())
        return indentation_level - 4  # Remove logging infrastructure frames

    def process(self, msg, kwargs):
        return "{i}{m}".format(i="  " * self.indent(), m=msg), kwargs


logger = CustomAdapter(logging.getLogger(__name__), {})


class Align(str, Enum):
    TOP = "top"
    CENTER = "center"
    BOTTOM = "bottom"
    RIGHT = "right"
    LEFT = "left"


class AbsPos:
    def __init__(self, obj: Object) -> None:
        self.obj = obj
        self.pos: Optional[P] = None
        self._offset = P(0, 0)

    def __add__(self, other: P) -> AbsPos:
        self._offset += other
        return self

    def __sub__(self, other: P) -> AbsPos:
        self._offset -= other
        return self

    def __str__(self) -> str:
        return f"{self.obj} @ {self.pos}"

    def resolve(self, pos: P) -> None:
        self.pos = pos + self._offset
        logger.debug("resolve %s %s", repr(self), self)

    def get(self) -> P:
        assert self.pos is not None
        return self.pos

    def ready(self):
        return self.pos is not None


class Object:
    def __init__(self, width=None, height=None, style=None, **kwargs) -> None:
        # Construct a new Style that inherits from the parent
        if not style:
            # This will inherit from the default style
            style = Style(**kwargs)

        if kwargs:
            # This will inherit from the user-supplied style
            style = style.clone(**kwargs)

        self.style = style
        self._w = width
        self._h = height
        self.children: OrderedDict[Object, P] = OrderedDict()
        self.parent: Optional[Object] = None

        self._id = uuid.uuid4()

        self.abs_pos = AbsPos(self)
        self.prepared_size = False
        self.prepared_pos = False

        self.cloned_to = None

    @property
    def width(self) -> int:
        assert self._w is not None
        return self._w

    @width.setter
    def width(self, val) -> None:
        self._w = val

    @property
    def height(self) -> int:
        assert self._h is not None
        return self._h

    @height.setter
    def height(self, val) -> None:
        self._h = val

    def add(self, obj, pos=P(0, 0)) -> None:
        self.children[obj] = pos
        assert obj.parent is None
        obj.parent = self
        obj.style.parent_obj_style = self.style

    def find(self, obj: Object, remove: bool = False) -> Optional[Object]:
        for child in self.children:
            if child == obj:
                if remove:
                    del self.children[obj]

                return child

        for child in self.children:
            result = child.find(obj, remove)
            if result:
                return result

        return None

    def remove(self, obj: Object) -> None:
        self.find(obj, remove=True)

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

    def prepare(self, renderer: Renderer, pos) -> bool:
        """
        Prepare the object for rendering by resolving any dynamically calculated
        positions or dimensions.

        Before `prepare` is called, the object's position and dimensions are not
        guaranteed to exist, and `obj.children` may not contain correct values. After
        `prepare` is called, these values must exist and be accurate.
        """
        res = self.prepare_size(renderer)
        res &= self.prepare_pos(pos)
        return res

        # res = self.prepared_size and self.prepared_pos
        # for child, offset in self.children.items():
        #     if not child.prepared_size or not child.prepared_pos:
        #         logger.debug("preparing child %s", child)
        #         res &= child.prepare(renderer, pos + offset)

        # return res
        # return True
        # return self.prepared

    def prepare_size(self, renderer) -> bool:
        if not self.prepared_size:
            self.prepared_size = self.prepare_size_impl(renderer)

        res = self.prepared_size

        for child in self.children:
            if not child.prepared_size:
                logger.debug("preparing child size %s", child)
                res &= child.prepare_size(renderer)

        return res

    def prepare_size_impl(self, renderer):
        return True

    def prepare_pos_impl(self, pos):
        self.abs_pos.resolve(pos)
        return True

    def prepare_pos(self, pos) -> bool:
        if not self.prepared_pos:
            self.prepared_pos = self.prepare_pos_impl(pos)

        res = self.prepared_pos

        for child, offset in self.children.items():
            if self.prepared_pos and not child.prepared_pos:
                logger.debug("preparing child pos %s", child)
                res &= child.prepare_pos(pos + offset)

        return res

    def render(self, renderer: Renderer, pos=P(0, 0)) -> None:
        x, y = pos
        for obj, offset in self.children.items():
            logger.debug("%s %s", obj, offset)
            offx, offy = offset
            obj.render(renderer, P(x + offx, y + offy))

    def get_pos(self) -> AbsPos:
        return self.abs_pos

    def dump(self, indent: int = 0) -> None:
        print(" " * indent, end="")
        print(self)
        for child in self.children:
            child.dump(indent + 1)

    def clone(self, unique: bool = False):
        logger.info("Cloning %s", self)
        c = deepcopy(self)

        if unique:
            c._id = uuid.uuid4()

        return c

    # TODO: It's not a good user experience for them to call `latest` all the time
    def latest(self):
        if self.cloned_to:
            return self.cloned_to.latest()

        return self

    def __deepcopy__(self, memo):
        copy = object.__new__(self.__class__)

        # Because `__hash__` uses `self._id`, we need to copy that manually first before
        # calling `deepcopy`, otherwise the `deepcopy` implementation will throw some
        # exceptions
        copy._id = self._id
        logger.debug(
            "copying %s %s %s to %s %s %s",
            self.__class__,
            id(self),
            hex(id(self)),
            copy.__class__,
            id(copy),
            hex(id(copy)),
        )

        memo[id(self)] = copy

        copy.cloned_to = None

        # TODO: Every time a field is added this needs to be updated, is there a better
        # way to do this?
        copy.children = deepcopy(self.children, memo)
        copy.parent = deepcopy(self.parent, memo)
        copy.style = deepcopy(self.style, memo)
        copy._w = deepcopy(self._w, memo)
        copy._h = deepcopy(self._h, memo)

        copy.prepared_size = self.prepared_size
        copy.prepared_pos = self.prepared_pos
        copy.abs_pos = self.abs_pos
        logger.debug("abs_pos %r %r", self.abs_pos, copy.abs_pos)

        self.cloned_to = copy

        return copy

    def __str__(self) -> str:
        return f"{type(self).__name__}({str(self._id)[:4]}, {self._w}, {self._h}) [{hex(id(self))}]"

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

    @property
    def width(self) -> int:
        # self._w = 0
        # for obj, offset in self.children.items():
        #     offx, _ = offset
        #     self._w = max(self._w, obj.width + offx)

        return self._w

    @width.setter
    def width(self, val) -> None:
        self._w = val

    @property
    def height(self) -> int:
        # self._h = 0
        # for obj, offset in self.children.items():
        #     _, offy = offset
        #     self._h += obj.height + offy

        return self._h

    @height.setter
    def height(self, val) -> None:
        self._h = val

    def prepare_size_impl(self, renderer) -> bool:
        if self.prepared_size:
            return True

        for obj in self.children:
            if not obj.prepared_size:
                return False

        # We need to compute the sizes of all child objects before we can compute the
        # size of a VLayout
        self._w = 0
        self._h = 0
        for obj, offset in self.children.items():
            self._w = max(self._w, obj.width + offset.x)
            self._h += obj.height + offset.y

        return True

    def prepare_pos_impl(self, pos):
        if self.prepared_pos:
            return True

        logger.debug("%s %s", self, pos)

        if not self.prepared_size:
            return False

        for obj in self.children:
            if not obj.prepared_size:
                return False

        y = 0

        self.abs_pos.resolve(pos)
        centerx = self.width // 2
        logger.debug("centerx: %s", centerx)
        for obj, offset in self.children.items():
            logger.debug("%s %s", obj, offset)

            # These will usually be zero for dynamically sized layouts, but child
            # objects are still allowed to add offsets
            offx, offy = offset

            y += offy

            self.children[obj] = P(offx + centerx - (obj.width // 2), y)

            y += obj.height

        return True

    # def prepare_pos_impl(self):
    #     for obj, offset in self.children.items():
    #         obj.prepare_pos_impl()

    # The default implementation of `prepare` assumes that the child offsets are
    # correct, but this is not true for dynamically sized layouts. We need to calculate
    # the correct offsets before calling the superclass implementation.
    # def prepare(self, renderer: Renderer, pos) -> None:
    #     # After this, we can access the width and height of this object and all child
    #     # objects
    #     print(self)
    #     print(self.children)
    #     self.prepare_size_impl()
    #     # TODO: implement the centering logic better
    #     # TODO: Only do this `if align == Align.CENTER:`

    # super().prepare(renderer, pos)

    # def render(self, renderer: Renderer, pos=P(0, 0)) -> None:
    #     logger.debug("%s %s", self, pos)
    #     x, y = pos
    #     # TODO: implement the centering logic better
    #     # TODO: if align == Align.CENTER:
    #     centerx = x + (self.width // 2)
    #     logger.debug("center: %s", centerx)
    #     for obj, offset in self.children.items():
    #         logger.debug("%s %s", obj, offset)
    #         offx, offy = offset

    #         obj_posx = x + offx
    #         obj_centerx = obj_posx + (obj.width // 2)
    #         obj.render(renderer, P(obj_posx + centerx - obj_centerx, y + offy))
    #         y += obj.height + offy


class HLayout(Object):
    def __init__(self, align=Align.CENTER, **kwargs) -> None:
        super().__init__(**kwargs)
        self.align = align

    def __deepcopy__(self, memo):
        copy = super().__deepcopy__(memo)
        copy.align = deepcopy(self.align, memo)

        return copy

    def prepare_size_impl(self, renderer):
        if self.prepared_size:
            return True

        for obj in self.children:
            if not obj.prepared_size:
                return False

        # We need to compute the sizes of all child objects before we can compute the
        # size of an HLayout
        self._w = 0
        self._h = 0
        for obj, offset in self.children.items():
            self._w += obj.width + offset.x
            self._h = max(self._h, obj.height + offset.y)

        return True

    def prepare_pos_impl(self, pos):
        if self.prepared_pos:
            return True

        if not self.prepared_size:
            return False

        for obj in self.children:
            if not obj.prepared_size:
                logger.debug("HLayout waiting for obj size: %s", obj)
                return False

        x = 0

        self.abs_pos.resolve(pos)
        centery = self.height // 2
        logger.debug("centery: %s", centery)
        for obj, offset in self.children.items():
            logger.debug("%s %s", obj, offset)

            # These will usually be zero for dynamically sized layouts, but child
            # objects are still allowed to add offsets
            offx, offy = offset

            x += offx

            self.children[obj] = P(x, offy + centery - (obj.height // 2))

            x += obj.width

        return True

    @property
    def width(self) -> int:
        self._w = 0
        for obj, offset in self.children.items():
            offx, _ = offset
            self._w += obj.width + offx

        return self._w

    @width.setter
    def width(self, val) -> None:
        self._w = val

    @property
    def height(self) -> int:
        self._h = 0
        for obj, offset in self.children.items():
            _, offy = offset
            self._h = max(self._h, obj.height + offy)

        return self._h

    @height.setter
    def height(self, val) -> None:
        self._h = val

    # def render(self, renderer: Renderer, pos=P(0, 0)) -> None:
    #     x, y = pos
    #     for obj, offset in self.children.items():
    #         logger.debug("%s %s", obj, offset)
    #         offx, offy = offset
    #         obj.render(renderer, P(x + offx, y + offy))
    #         x += obj.width + offx


class Rectangle(Object):
    def render(self, renderer: Renderer, pos=P(0, 0)) -> None:
        # Borders are mandatory at the moment, so the minimum size is 2x2
        assert self.width >= 2 and self.height >= 2

        x, y = pos
        renderer.rectangle(
            pos,
            # Subtract one from width and height to account for the border
            P(x + self.width - 1, y + self.height - 1),
            self.style,
        )
        super().render(renderer, pos)


class Line(Object):
    # TODO: Support polar coordinates
    def __init__(self, *, end, start=P(0, 0), **kwargs) -> None:
        if isinstance(end, P) and isinstance(start, P):
            width = max(start.x, end.x)
            height = max(start.y, end.y)
            super().__init__(width=width, height=height, **kwargs)
        else:
            # TODO
            super().__init__(width=1, height=1, **kwargs)

        self.start = start
        self.end = end

    def __deepcopy__(self, memo):
        copy = super().__deepcopy__(memo)

        if isinstance(self.start, AbsPos):
            print("before", repr(self.start), self.start.obj, self.end.obj)

        copy.start = self.start  # deepcopy(self.start, memo)
        copy.end = self.end  # deepcopy(self.end, memo)

        if isinstance(self.start, AbsPos):
            print("after", repr(self.start), copy.start.obj, copy.end.obj)

        return copy

    # def prepare_size_impl(self, renderer):
    #     if self.prepared_size:
    #         return True

    #     if isinstance(self.start, P) and isinstance(self.end, P):
    #         self._w = max(self.start.x, self.end.x)
    #         self._h = max(self.start.y, self.end.y)

    #         return True

    #     return False

    def prepare_pos_impl(self, pos) -> bool:
        if self.prepared_pos:
            return True

        if isinstance(self.start, AbsPos) and self.start.ready():
            print("start", repr(self.start), self.start, self.start.obj.latest())
            self.start = self.start.obj.latest().get_pos().get()
        if isinstance(self.end, AbsPos) and self.end.ready():
            print("end", repr(self.end), self.end, self.end.obj.latest())
            self.end = self.end.obj.latest().get_pos().get()

        print(repr(self.start), self.start, repr(self.end), self.end)
        if isinstance(self.start, P) and isinstance(self.end, P):
            self.abs_pos.resolve(self.start)
            return True

        return False

    def render(self, renderer: Renderer, pos=P(0, 0)) -> None:
        # if isinstance(self.start, AbsPos):
        #     self.start = self.start.get()

        # if isinstance(self.end, AbsPos):
        #     self.end = self.end.get()

        # renderer.line(self.start + pos, self.end + pos, self.style)
        renderer.line(self.start, self.end, self.style)


# class Grid(Object):
#     def prepare(self, renderer: Renderer):
#         self._w = self._w or renderer._w
#         self._h = self._h or renderer._h

#     def render(self, renderer: Renderer, pos=P(0, 0)):
#         pos = P(pos)
#         for i in range(0, renderer._w, 100):
#             renderer.line((i + pos.x, pos.y), (i + pos.x, self._h), self.style)


class TextBox(Rectangle):
    def __init__(self, text, align=Anchor.MIDDLE_MIDDLE, **kwargs) -> None:
        super().__init__(**kwargs)

        pos = P(0, 0)
        style = self.style
        if align == Anchor.MIDDLE_MIDDLE:
            style = self.style.clone(anchor=Anchor.MIDDLE_MIDDLE)
            pos = P(self.width // 2, self.height // 2)

        self.text_obj = Text(text, style=style, width=self.width, height=self.height)
        self.add(self.text_obj, pos)

    @property
    def width(self) -> int:
        assert self._w is not None
        return self._w

    @width.setter
    def width(self, val) -> None:
        self._w = val

    @property
    def height(self) -> int:
        assert self._h is not None
        return self._h

    @height.setter
    def height(self, val) -> None:
        self._h = val

        # Recenter text
        self.add(self.text_obj, P(self.width // 2, self.height // 2))

    def set_text(self, text) -> None:
        self.text_obj.text = text

    def __deepcopy__(self, memo):
        copy = super().__deepcopy__(memo)
        copy.text_obj = deepcopy(self.text_obj, memo)
        print("deepcopy", hex(id(self)), copy)

        return copy

    def __str__(self) -> str:
        return f"{type(self).__name__}({str(self._id)[:4]}, {repr(self.text_obj.text)}, {self._w}, {self._h}) [{hex(id(self))}]"

    # def prepare(self, renderer: Renderer):
    #     super().prepare(renderer)
    # if self.fit_height:
    #     t, _ = self.children[0]
    #     self.height = t.height

    # def render(self, renderer: Renderer, pos=P(0, 0)) -> None:
    #     super().render(renderer, pos)


class Table(HLayout):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def prepare(self, renderer: Renderer, pos) -> None:
        super().prepare(renderer, pos)
        self._h = 0
        for obj, _ in self.children.items():
            self._h = max(self._h, obj.height)

        # Set all cells to the same height
        for obj, _ in self.children.items():
            obj.height = self._h


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

    def render(self, renderer: Renderer, pos=P(0, 0)) -> None:
        renderer.line(self.start + pos, self.end + pos, self.style)

        d = self.end - self.start
        length = d.mag()
        angle = d.radians()

        head_length = length * self.aratio
        head_angle = math.pi / 4  # 45 degrees in radians

        head_dx1 = head_length * math.cos(angle + head_angle)
        head_dy1 = head_length * math.sin(angle + head_angle)
        head_dx2 = head_length * math.cos(angle - head_angle)
        head_dy2 = head_length * math.sin(angle - head_angle)

        renderer.line(
            pos + self.end, pos + self.end - P(head_dx1, head_dy1), self.style
        )
        renderer.line(
            pos + self.end, pos + self.end - P(head_dx2, head_dy2), self.style
        )

        if self.double_sided:
            renderer.line(
                pos + self.start,
                pos + self.start + P(head_dx1, head_dy1),
                self.style,
            )
            renderer.line(
                pos + self.start, pos + self.start + P(head_dx2, head_dy2), self.style
            )


class Spacer(Object):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.width = self._w or self.style.padding
        self.height = self._h or self.style.padding


class Text(Object):
    def __init__(self, text: str, align=Align.LEFT, **kwargs) -> None:
        super().__init__(**kwargs)
        self.text = text
        self.align = align

    def __deepcopy__(self, memo):
        copy = super().__deepcopy__(memo)
        copy.text = deepcopy(self.text, memo)
        copy.align = deepcopy(self.align, memo)
        return copy

    # TODO: the width and height may be misleading if the text is anchored in the center
    def prepare_size_impl(self, renderer: Renderer) -> bool:
        if self.prepared_size:
            return True

        if not self._w or not self._h:
            _, _, right, bottom = renderer.text_bbox(self.text, self.style)
            self.width = self._w or right
            self.height = self._h or bottom

        return True

    def render(self, renderer: Renderer, pos=P(0, 0)) -> None:
        if self.align == Align.RIGHT:
            pos = pos + P(self.width, 0)
            renderer.text(self.text, pos, self.style.clone(anchor=Anchor.TOP_RIGHT))
        elif self.align == Align.CENTER:
            renderer.text(
                self.text,
                (pos + P(self.width, self.height).floordiv(2)),
                self.style.clone(anchor=Anchor.MIDDLE_MIDDLE),
            )
        else:
            renderer.text(self.text, pos, self.style)

    def __str__(self) -> str:
        return f"{type(self).__name__}({str(self._id)[:4]}, {repr(self.text)}, {self._w}, {self._h}) [{hex(id(self))}]"


class Canvas(Object):
    def render(self, renderer: Renderer, pos=P(0, 0)) -> None:
        self.width = self.style.padding
        self.height = self.style.padding
        pos = pos.add(self.style.padding)
        for obj, offset in self.children.items():
            logger.debug("%s %s", obj, offset)
            # obj.prepare(renderer, pos + offset)
            obj.render(renderer, pos + offset)

            # TODO: This only works for one object
            x, y = offset + pos
            self.width = max(self.width, obj.width + x)
            self.height = max(self.height, obj.height + y)

        self.width += self.style.padding
        self.height += self.style.padding

        # TODO: Should we set the renderer dimensions before we call render?
        renderer.set_dimensions(P(self.width, self.height))

    def prepare(self, renderer: Renderer, pos) -> bool:
        i = 0
        self.prepared = False
        pos = pos.add(self.style.padding)
        while not self.prepared:
            res = True
            for obj, offset in self.children.items():
                logger.debug("preparing %s", obj)
                res1 = obj.prepare(renderer, pos + offset)
                res &= res1
                logger.debug("prepared %s, result %s, overall %s", obj, res1, res)

            self.prepared = res

            i += 1
            logger.debug("%d iterations", i)

            if i > 8:
                exit(1)

        return self.prepared
