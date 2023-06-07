from __future__ import annotations

from enum import Enum
from typing import Any, NotRequired, TypedDict, Unpack

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


_default_style: Style | None = None


class StyleParams(TypedDict):
    padding: NotRequired[int | None]
    font: NotRequired[str | None]
    font_size: NotRequired[int | None]
    anchor: NotRequired[Anchor | None]
    stroke_color: NotRequired[Color | None]
    stroke_width: NotRequired[int | None]
    fill_color: NotRequired[Color | None]
    font_color: NotRequired[Color | None]
    alpha: NotRequired[int | None]


class Style:
    def __init__(
        self,
        *,
        parent: Style | None = None,
        padding: int | None = None,
        font: str | None = None,
        font_size: int | None = None,
        anchor: Anchor | None = None,
        stroke_color: Color | None = None,
        stroke_width: int | None = None,
        fill_color: Color | None = None,
        font_color: Color | None = None,
        alpha: int | None = None,
        parent_obj_style: Style | None = None,
    ) -> None:
        if parent is None:
            parent = _default_style

        self._parent = parent

        self._padding = padding
        self._font = font
        self._font_size = font_size
        self._anchor = anchor
        self._stroke_color = stroke_color
        self._stroke_width = stroke_width
        self._fill_color = fill_color
        self._font_color = font_color
        self._alpha = alpha

        self._parent_obj_style: Style | None = parent_obj_style

    def _attr(self, attr_name: str) -> Any:
        attr = getattr(self, attr_name)
        if attr is not None:
            return attr

        assert self._parent is not None

        # This seems like a pylint bug, protected access should be fine here
        return self._parent._attr(attr_name)  # pylint: disable=protected-access

    def _composite_color(self, attr: str) -> Color:
        color: Color = self._attr(attr)

        if self._parent_obj_style is None:
            return color

        parent_color = self._parent_obj_style._composite_color(attr)
        alpha_ratio = self.alpha / 255
        return parent_color.mul(1 - alpha_ratio) + color.mul(alpha_ratio)

    @property
    def parent_obj_style(self) -> Style | None:
        return self._parent_obj_style

    @parent_obj_style.setter
    def parent_obj_style(self, style: Style) -> None:
        self._parent_obj_style = style

    @property
    def padding(self) -> int:
        return self._attr("_padding")

    @property
    def font(self) -> str:
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
    def stroke_width(self) -> int:
        return self._attr("_stroke_width")

    @property
    def composite_stroke_color(self) -> Color:
        return self._composite_color("_stroke_color")

    @property
    def fill_color(self) -> Color:
        return self._attr("_fill_color")

    @property
    def composite_fill_color(self) -> Color:
        return self._composite_color("_fill_color")

    @property
    def font_color(self) -> Color:
        return self._attr("_font_color")

    @property
    def composite_font_color(self) -> Color:
        return self._composite_color("_font_color")

    @property
    def alpha(self) -> int:
        return int(self._attr("_alpha"))

    @property
    def composite_alpha(self) -> int:
        if self._parent_obj_style is None:
            return self.alpha

        return int(self._parent_obj_style.composite_alpha * self.alpha / 255)

    def clone(self, **kwargs: Unpack[StyleParams]) -> Style:
        # TODO: Should we be passing in the parent_obj_style here, or should it
        # automatically work if the parent is set?
        return Style(parent=self, parent_obj_style=self._parent_obj_style, **kwargs)

    def __str__(self) -> str:
        return str(self.__dict__)


_default_style = Style(
    padding=10,
    font="Roboto-Regular.ttf",
    font_size=32,
    anchor=Anchor.TOP_LEFT,
    stroke_color=BLACK,
    stroke_width=1,
    fill_color=WHITE,
    font_color=BLACK,
    alpha=255,
)


def set_style(style: Style) -> None:
    global _default_style
    _default_style = style
    # logger.debug('Default style: %s', repr(style))


# def default_style() -> Style:
#     return _default_style
