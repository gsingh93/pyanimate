from enum import Enum
from typing import NamedTuple


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


class Style(NamedTuple):
    padding: int = 10
    font: str = 'Roboto-Regular.ttf'
    font_size: int = 32
    anchor: Anchor = Anchor.TOP_LEFT
    stroke_color: str = "black"
    fill_color: str = "white"
    font_color: str = "black"
