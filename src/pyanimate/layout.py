from __future__ import annotations

import copy
import logging
import math
import uuid
from collections import OrderedDict
from enum import Enum
from typing import Optional, Self

from .renderer import Renderer
from .shape import Point as P
from .style import Anchor, Style

logger = logging.getLogger(__name__)


class Align(str, Enum):
    TOP = "top"
    CENTER = "center"
    BOTTOM = "bottom"
    RIGHT = "right"
    LEFT = "left"


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

        parent = old.parent
        assert parent is not None
        logger.debug(
            "Replacing %s with %s in parent %s", repr(old), repr(new), repr(parent)
        )

        # Preserve the order of items in the dictionary
        parent.children = OrderedDict(
            (new, value) if key == old else (key, value)
            for key, value in parent.children.items()
        )
        new.parent = parent
        new.style.parent_obj_style = parent.style

    def prepare(self, renderer: Renderer) -> None:
        for obj in self.children:
            obj.prepare(renderer)

    def render(self, renderer: Renderer, pos=(0, 0)) -> None:
        x, y = pos
        for obj, offset in self.children.items():
            logger.debug("%s %s", obj, offset)
            offx, offy = offset
            obj.render(renderer, P(x + offx, y + offy))

    def clone(self, unique: bool = False):
        c = copy.deepcopy(self)
        if unique:
            c._id = uuid.uuid4()

        return c

    def __str__(self) -> str:
        return f"{type(self).__name__}({self._w}, {self._h})"

    def __eq__(self, o: Self) -> bool:
        return self._id == o._id

    def __hash__(self):
        return hash(self._id)


class VLayout(Object):
    def __init__(self, align=Align.CENTER, **kwargs) -> None:
        super().__init__(**kwargs)
        self.align = align

    @property
    def width(self) -> int:
        self._w = 0
        for obj, offset in self.children.items():
            offx, _ = offset
            self._w = max(self._w, obj.width + offx)

        return self._w

    @width.setter
    def width(self, val) -> None:
        self._w = val

    @property
    def height(self) -> int:
        self._h = 0
        for obj, offset in self.children.items():
            _, offy = offset
            self._h += obj.height + offy

        return self._h

    @height.setter
    def height(self, val) -> None:
        self._h = val

    def render(self, renderer: Renderer, pos=(0, 0)) -> None:
        logger.debug("%s %s", self, pos)
        x, y = pos
        # TODO: implement the centering logic better
        # TODO: if align == Align.CENTER:
        centerx = x + (self.width // 2)
        logger.debug("center: %s", centerx)
        for obj, offset in self.children.items():
            logger.debug("%s %s", obj, offset)
            offx, offy = offset

            obj_posx = x + offx
            obj_centerx = obj_posx + (obj.width // 2)
            obj.render(renderer, P(obj_posx + centerx - obj_centerx, y + offy))
            y += obj.height + offy


class HLayout(Object):
    def __init__(self, align=Align.CENTER, **kwargs) -> None:
        super().__init__(**kwargs)
        self.align = align

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

    def render(self, renderer: Renderer, pos=P(0, 0)) -> None:
        x, y = pos
        for obj, offset in self.children.items():
            logger.debug("%s %s", obj, offset)
            offx, offy = offset
            obj.render(renderer, P(x + offx, y + offy))
            x += obj.width + offx


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
        width = max(start.x, end.x)
        height = max(start.y, end.y)
        super().__init__(width=width, height=height, **kwargs)

        self.start = start
        self.end = end

    def render(self, renderer: Renderer, pos=(0, 0)) -> None:
        renderer.line(self.start + pos, self.end + pos, self.style)


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

    # def prepare(self, renderer: Renderer):
    #     super().prepare(renderer)
    # if self.fit_height:
    #     t, _ = self.children[0]
    #     self.height = t.height

    def render(self, renderer: Renderer, pos=P(0, 0)) -> None:
        super().render(renderer, pos)


class Table(HLayout):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def prepare(self, renderer: Renderer) -> None:
        super().prepare(renderer)
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

    # TODO: the width and height may be misleading if the text is anchored in the center
    def prepare(self, renderer: Renderer) -> None:
        super().prepare(renderer)

        if not self._w or not self._h:
            _, _, right, bottom = renderer.text_bbox(self.text, self.style)
            self.width = self._w or right
            self.height = self._h or bottom

    def render(self, renderer: Renderer, pos=(0, 0)) -> None:
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
        return f"{type(self).__name__}({repr(self.text)}, {self._w}, {self._h})"


class Canvas(Object):
    def render(self, renderer: Renderer, pos=P(0, 0)) -> None:
        self.width = self.style.padding
        self.height = self.style.padding
        pos = pos.add(self.style.padding)
        for obj, offset in self.children.items():
            logger.debug("%s %s", obj, offset)
            obj.prepare(renderer)
            obj.render(renderer, pos + offset)

            # TODO: This only works for one object
            x, y = offset + pos
            self.width = max(self.width, obj.width + x)
            self.height = max(self.height, obj.height + y)

        self.width += self.style.padding
        self.height += self.style.padding

        # TODO: Should we set the renderer dimensions before we call render?
        renderer.set_dimensions(P(self.width, self.height))
