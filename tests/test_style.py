import pytest

from pyanimate.shape import BLACK, BLUE, RED, WHITE, Color
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
            stroke_width=2,
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
        assert style.stroke_width == 2
        assert style.fill_color == RED
        assert style.font_color == BLACK
        assert style.alpha == 255

    def test_parent_style(self, style) -> None:
        child_style = style.clone()

        assert child_style.padding == 5
        assert child_style.font == "Roboto-Regular.ttf"
        assert child_style.font_size == 24
        assert child_style.anchor == Anchor.TOP_LEFT
        assert child_style.stroke_color == BLUE
        assert child_style.stroke_width == 2
        assert child_style.fill_color == RED
        assert child_style.font_color == BLACK
        assert child_style.alpha == 255

    def test_parent_style_override(self, style) -> None:
        child_style = style.clone(padding=10)
        assert style.padding == 5

        assert child_style.padding == 10
        assert child_style.font == "Roboto-Regular.ttf"
        assert child_style.font_size == 24
        assert child_style.anchor == Anchor.TOP_LEFT
        assert child_style.alpha == 255
        assert child_style.stroke_color == BLUE
        assert child_style.stroke_width == 2
        assert child_style.fill_color == RED
        assert child_style.font_color == BLACK

    def test_composite_transparent(self, c, style) -> None:
        assert c.style.alpha == 255

        r = c.rectangle(width=100, height=100, style=style.clone(alpha=0))
        c.add(r)

        assert r.style.alpha == 0

        assert c.style.stroke_color == BLACK
        assert c.style.fill_color == WHITE
        assert c.style.font_color == BLACK

        # When alpha is 0, the composite color is the parent color
        assert r.style.composite_stroke_color == BLACK
        assert r.style.composite_fill_color == WHITE
        assert r.style.composite_font_color == BLACK

    def test_composite_opaque(self, c, style) -> None:
        assert c.style.alpha == 255

        r = c.rectangle(width=100, height=100, style=style.clone(alpha=255))
        c.add(r)

        assert r.style.alpha == 255

        assert c.style.stroke_color == BLACK
        assert c.style.fill_color == WHITE
        assert c.style.font_color == BLACK

        # When alpha is 255, the composite color is the child color
        assert r.style.composite_stroke_color == BLUE
        assert r.style.composite_fill_color == RED
        assert r.style.composite_font_color == BLACK

    def test_composite_semi_transparent(self, c, style) -> None:
        assert c.style.alpha == 255

        r = c.rectangle(width=100, height=100, style=style.clone(alpha=100))
        c.add(r)

        assert r.style.alpha == 100

        assert c.style.stroke_color == BLACK
        assert c.style.fill_color == WHITE
        assert c.style.font_color == BLACK

        assert r.style.composite_stroke_color == Color(0, 0, 100)
        assert r.style.composite_fill_color == Color(255, 155, 155)
        assert r.style.composite_font_color == BLACK
