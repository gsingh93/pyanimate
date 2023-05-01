import copy
import logging
from enum import Enum
from typing import Dict

from point import Point as P
from renderer import Renderer
from style import Anchor, Style

logger = logging.getLogger(__name__)


class Align(str, Enum):
    TOP = "top"
    CENTER = "center"
    BOTTOM = "bottom"
    RIGHT = "right"
    LEFT = "left"


class Object:
    def __init__(self, width=None, height=None, style=None, **kwargs):
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
        self.children: Dict[Object, P] = {}
        self.parent = None

    @property
    def width(self) -> int:
        assert self._w is not None
        return self._w

    @width.setter
    def width(self, val):
        self._w = val

    @property
    def height(self) -> int:
        assert self._h is not None
        return self._h

    @height.setter
    def height(self, val):
        self._h = val

    def add(self, obj, pos=P(0, 0)):
        self.children[obj] = pos
        obj.parent = self
        obj.style._parent_obj_style = self.style

    def prepare(self, renderer: Renderer):
        for obj in self.children:
            obj.prepare(renderer)

    def render(self, renderer: Renderer, pos=(0, 0)):
        x, y = pos
        for (obj, offset) in self.children.items():
            logger.debug('%s %s', obj, offset)
            offx, offy = offset
            obj.render(renderer, P(x + offx, y + offy))

    def clone(self):
        return copy.deepcopy(self)

    def __str__(self):
        return f"{type(self).__name__}({self._w}, {self._h})"


class VLayout(Object):
    def __init__(self, align=Align.CENTER, **kwargs):
        super().__init__(**kwargs)
        self.align = align

    @property
    def width(self) -> int:
        self._w = 0
        for (obj, offset) in self.children.items():
            offx, _ = offset
            self._w = max(self._w, obj.width + offx)

        return self._w

    @width.setter
    def width(self, val):
        self._w = val

    @property
    def height(self) -> int:
        self._h = 0
        for (obj, offset) in self.children.items():
            _, offy = offset
            self._h += obj.height + offy

        return self._h

    @height.setter
    def height(self, val):
        self._h = val

    def render(self, renderer: Renderer, pos=(0, 0)):
        logger.debug('%s %s', self, pos)
        x, y = pos
        # TODO: implement the centering logic better
        # TODO: if align == Align.CENTER:
        centerx = x + (self.width // 2)
        logger.debug('center: %s', centerx)
        for (obj, offset) in self.children.items():
            logger.debug('%s %s', obj, offset)
            offx, offy = offset

            obj_posx = x + offx
            obj_centerx = obj_posx + (obj.width // 2)
            obj.render(renderer, P(obj_posx + centerx - obj_centerx, y + offy))
            y += obj.height + offy


class HLayout(Object):
    def __init__(self, align=Align.CENTER, **kwargs):
        super().__init__(**kwargs)
        self.align = align

    @property
    def width(self) -> int:

        self._w = 0
        for (obj, offset) in self.children.items():
            offx, _ = offset
            self._w += obj.width + offx

        return self._w

    @width.setter
    def width(self, val):
        self._w = val

    @property
    def height(self) -> int:
        self._h = 0
        for (obj, offset) in self.children.items():
            _, offy = offset
            self._h = max(self._h, obj.height + offy)

        return self._h

    @height.setter
    def height(self, val):
        self._h = val

    def render(self, renderer: Renderer, pos=P(0, 0)):
        x, y = pos
        for (obj, offset) in self.children.items():
            logger.debug('%s %s', obj, offset)
            offx, offy = offset
            obj.render(renderer, P(x + offx, y + offy))
            x += obj.width + offx


# TODO: width and height are actually one pixel larger than requested
class Rectangle(Object):
    def render(self, renderer: Renderer, pos=P(0, 0)):
        x, y = pos
        renderer.rectangle((x, y), (x + self._w, y + self._h), self.style)
        super().render(renderer, pos)


class Line(Object):
    # TODO: Support polar coordinates
    def __init__(self, *, end, start=P(0, 0), **kwargs):
        width = max(start.x, end.x)
        height = max(start.y, end.y)
        super().__init__(width=width, height=height, **kwargs)

        self.start = start
        self.end = end

    def render(self, renderer: Renderer, pos=(0, 0)):
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
    def __init__(self, text, align=Anchor.MIDDLE_MIDDLE, **kwargs):
        super().__init__(**kwargs)

        pos = (0, 0)
        style = self.style
        if align == Anchor.MIDDLE_MIDDLE:
            style = self.style.clone(anchor=Anchor.MIDDLE_MIDDLE)
            pos = (self.width // 2, self.height // 2)

        self.text_obj = Text(
            text, style=style, width=self.width, height=self.height
        )
        self.add(self.text_obj, pos)

    @property
    def width(self) -> int:
        assert self._w is not None
        return self._w

    @width.setter
    def width(self, val):
        self._w = val

    @property
    def height(self) -> int:
        assert self._h is not None
        return self._h

    @height.setter
    def height(self, val):
        self._h = val

        # Recenter text
        self.add(self.text_obj, P(self.width // 2, self.height // 2))

    def set_text(self, text):
        self.text_obj.text = text

    # def prepare(self, renderer: Renderer):
    #     super().prepare(renderer)
    # if self.fit_height:
    #     t, _ = self.children[0]
    #     self.height = t.height

    def render(self, renderer: Renderer, pos=P(0, 0)):
        super().render(renderer, pos)


class Table(HLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def prepare(self, renderer: Renderer):
        super().prepare(renderer)
        self._h = 0
        for (obj, _) in self.children.items():
            self._h = max(self._h, obj.height)

        # Set all cells to the same height
        for (obj, _) in self.children.items():
            obj.height = self._h


class DottedLine(Line):
    def __init__(self, dash_len=10, **kwargs):
        super().__init__(**kwargs)
        self.dash_len = dash_len

    def render(self, renderer: Renderer, pos=P(0, 0)):
        length = (
            (self.end.x - self.start.x)**2 + (self.end.y - self.start.y)**2
        )**0.5

        if self.end.x != self.start.x:
            u = (self.end - self.start) / length
        else:
            u = P(0, 1)

        xy1 = self.start + pos
        for _ in range(0, int(length), self.dash_len):
            xy2 = xy1 + (u * (self.dash_len // 2))
            renderer.line(xy1, xy2, self.style)
            xy1 = xy1 + u * self.dash_len


class Arrow(Line):
    def __init__(self, double_sided=False, arrow_length=10, **kwargs):
        super().__init__(**kwargs)
        self.double_sided = double_sided
        self.alen = arrow_length

    def render(self, renderer: Renderer, pos=P(0, 0)):
        renderer.line(self.start + pos, self.end + pos, self.style)

        renderer.line(pos + self.end, pos + self.end - self.alen, self.style)
        renderer.line(
            pos + self.end, pos + self.end + P(-self.alen, self.alen),
            self.style
        )

        if self.double_sided:
            renderer.line(
                pos + self.start, pos + self.start + P(self.alen, -self.alen),
                self.style
            )
            renderer.line(
                pos + self.start, pos + self.start + self.alen, self.style
            )


class Spacer(Object):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.width = self._w or self.style.padding
        self.height = self._h or self.style.padding


class Text(Object):
    def __init__(self, text: str, align=Align.LEFT, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.align = align

    # TODO: the width and height may be misleading if the text is anchored in the center
    def prepare(self, renderer: Renderer):
        super().prepare(renderer)

        if not self._w or not self._h:
            _, _, right, bottom = renderer.text_bbox(self.text, self.style)
            self.width = self._w or right
            self.height = self._h or bottom

    def render(self, renderer: Renderer, pos=(0, 0)):
        if self.align == "right":
            pos = pos + P(self.width, 0)
            renderer.text(
                self.text, pos, self.style.clone(anchor=Anchor.TOP_RIGHT)
            )
        else:
            renderer.text(self.text, pos, self.style)

    def __str__(self):
        return f"{type(self).__name__}({repr(self.text)}, {self._w}, {self._h})"


class Canvas(Object):
    def render(self, renderer: Renderer, pos=P(0, 0)):
        self.width = self.style.padding
        self.height = self.style.padding
        pos = pos + self.style.padding
        for (obj, offset) in self.children.items():
            logger.debug('%s %s', obj, offset)
            obj.prepare(renderer)
            obj.render(renderer, pos + offset)

            # TODO: This only works for one object
            x, y = offset + pos
            self.width = max(self.width, obj.width + x)
            self.height = max(self.height, obj.height + y)

        self.width += self.style.padding
        self.height += self.style.padding

        # TODO: Should we set the renderer dimensions before we call render?
        renderer.set_dimensions((self.width, self.height))
