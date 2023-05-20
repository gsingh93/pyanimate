import pytest

from pyanimate.layout import Rectangle
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

    def test_composite_transparent(self, canvas, style) -> None:
        assert canvas.style.alpha == 255

        r = Rectangle(canvas=canvas, width=100, height=100, style=style.clone(alpha=0))
        canvas.add(r)

        assert r.style.alpha == 0

        assert canvas.style.stroke_color == BLACK
        assert canvas.style.fill_color == WHITE
        assert canvas.style.font_color == BLACK

        # When alpha is 0, the composite color is the parent color
        assert r.style.composite_stroke_color == BLACK
        assert r.style.composite_fill_color == WHITE
        assert r.style.composite_font_color == BLACK

    def test_composite_opaque(self, canvas, style) -> None:
        assert canvas.style.alpha == 255

        r = Rectangle(
            canvas=canvas, width=100, height=100, style=style.clone(alpha=255)
        )
        canvas.add(r)

        assert r.style.alpha == 255

        assert canvas.style.stroke_color == BLACK
        assert canvas.style.fill_color == WHITE
        assert canvas.style.font_color == BLACK

        # When alpha is 255, the composite color is the child color
        assert r.style.composite_stroke_color == BLUE
        assert r.style.composite_fill_color == RED
        assert r.style.composite_font_color == BLACK

    def test_composite_semi_transparent(self, canvas, style) -> None:
        assert canvas.style.alpha == 255

        r = Rectangle(
            canvas=canvas, width=100, height=100, style=style.clone(alpha=100)
        )
        canvas.add(r)

        assert r.style.alpha == 100

        assert canvas.style.stroke_color == BLACK
        assert canvas.style.fill_color == WHITE
        assert canvas.style.font_color == BLACK

        assert r.style.composite_stroke_color == Color(0, 0, 100)
        assert r.style.composite_fill_color == Color(255, 155, 155)
        assert r.style.composite_font_color == BLACK
