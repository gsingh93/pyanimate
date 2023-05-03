import pytest

from pyanimate.shape import BLACK, BLUE, RED
from pyanimate.style import Anchor, Style


class TestStyle:
    @pytest.fixture
    def style(self):
        return Style(
            parent=None,
            padding=5,
            font="Roboto-Regular.ttf",
            font_size=24,
            anchor=Anchor.TOP_LEFT,
            stroke_color=BLUE,
            fill_color=RED,
            font_color=BLACK,
            alpha=255,
        )

    def test_attributes(self, style) -> None:
        assert style.padding == 5
        assert style.font == "Roboto-Regular.ttf"
        assert style.font_size == 24
        assert style.anchor == Anchor.TOP_LEFT
        assert style.stroke_color == BLUE
        assert style.fill_color == RED
        assert style.font_color == BLACK
        assert style.alpha == 255

    def test_parent_style(self, style) -> None:
        child_style = style.clone()
        assert child_style.padding == 5
        assert child_style.font == "Roboto-Regular.ttf"
        assert child_style.font_size == 24
        assert child_style.anchor == Anchor.TOP_LEFT
        assert style.stroke_color == BLUE
        assert style.fill_color == RED
        assert style.font_color == BLACK
        assert child_style.alpha == 255

    def test_parent_style_override(self, style) -> None:
        child_style = style.clone(padding=10)
        assert style.padding == 5

        assert child_style.padding == 10
        assert child_style.font == "Roboto-Regular.ttf"
        assert child_style.font_size == 24
        assert child_style.anchor == Anchor.TOP_LEFT
        assert style.stroke_color == BLUE
        assert style.fill_color == RED
        assert style.font_color == BLACK
        assert child_style.alpha == 255
