from __future__ import annotations

from enum import Enum
from typing import Optional

from .shape import BLACK, WHITE, Color


class Anchor(str, Enum):
    TOP_LEFT = "la"
    TOP_MIDDLE = "ma"
    TOP_RIGHT = "ra"

    MIDDLE_LEFT = "lm"
    MIDDLE_MIDDLE = "mm"
    MIDDLE_RIGHT = "rm"

    BOTTOM_LEFT = "ld"
    BOTTOM_MIDDLE = "md"
    BOTTOM_RIGHT = "rd"


_default_style: Optional[Style] = None


class Style:
    def __init__(
        self,
        *,
        parent: Optional[Style] = None,
        padding: Optional[int] = None,
        font: Optional[str] = None,
        font_size: Optional[int] = None,
        anchor: Optional[Anchor] = None,
        stroke_color: Optional[Color[int]] = None,
        fill_color: Optional[Color[int]] = None,
        font_color: Optional[Color[int]] = None,
        alpha: Optional[int] = None,
    ) -> None:
        if parent is None:
            parent = _default_style

        self._parent = parent

        self._padding = padding
        self._font = font
        self._font_size = font_size
        self._anchor = anchor
        self._stroke_color = stroke_color
        self._fill_color = fill_color
        self._font_color = font_color
        self._alpha = alpha

        self._parent_obj_style: Optional[Style] = None

    def _attr(self, attr_name: str):
        attr = getattr(self, attr_name)
        if attr is not None:
            return attr

        assert self._parent is not None

        # This seems like a pylint bug, protected access should be fine here
        return self._parent._attr(attr_name)  # pylint: disable=protected-access

    @property
    def padding(self) -> int:
        return self._attr("_padding")

    @property
    def font(self):
        return self._attr("_font")

    @property
    def font_size(self) -> int:
        return self._attr("_font_size")

    @property
    def anchor(self) -> Anchor:
        return self._attr("_anchor")

    @property
    def stroke_color(self) -> Color:
        return self._attr("_stroke_color")

    @property
    def fill_color(self) -> Color:
        return self._attr("_fill_color")

    @property
    def font_color(self) -> Color:
        return self._attr("_font_color")

    @property
    def alpha(self) -> int:
        return int(self._attr("_alpha"))

    @property
    def composite_alpha(self) -> int:
        if self._parent_obj_style is None:
            return self.alpha

        return int(self._parent_obj_style.composite_alpha * self.alpha / 255)

    def clone(self, **kwargs):
        return Style(parent=self, **kwargs)

    def __str__(self) -> str:
        return str(self.__dict__)


_default_style = Style(
    padding=10,
    font="Roboto-Regular.ttf",
    font_size=32,
    anchor=Anchor.TOP_LEFT,
    stroke_color=BLACK,
    fill_color=WHITE,
    font_color=BLACK,
    alpha=255,
)


def set_style(style) -> None:
    global _default_style
    _default_style = style
    # logger.debug('Default style: %s', repr(style))


# def default_style() -> Style:
#     return _default_style
