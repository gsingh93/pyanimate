import pytest

from pyanimate.layout import Spacer
from pyanimate.renderer import PILRenderer, RenderContext
from pyanimate.shape import RED, WHITE
from pyanimate.shape import Point as P

from . import ImageTestBase


class TestRenderer:
    def test_render_context(self) -> None:
        ctx = RenderContext(width=10, height=20, bit_width=2, dpi=(300, 300), scale=2)

        assert ctx.scale == 2
        assert ctx.w == 10
        assert ctx.h == 20
        assert ctx.dpi == (300, 300)

    def test_pil_renderer(self) -> None:
        ctx = RenderContext(width=10, height=20, bit_width=2, dpi=(300, 300), scale=2)
        renderer = PILRenderer(ctx)

        assert renderer.ctx == ctx
        assert renderer._w == 20
        assert renderer._h == 40
        assert renderer.background == WHITE
        assert renderer.image.mode == "RGBA"
        assert renderer.image.size == (20, 40)


class TestTextBoxDynamicSize(ImageTestBase):
    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, c) -> None:
        r = c.textbox(text="A", font_size=4)
        c.add(r)

    def frame(self) -> list[str]:
        return [
            "wwwww",
            "wbbbw",
            "wb?bw",
            "wb?b.",
            "wbbb.",
        ]


class TestRectangle2x2(ImageTestBase):
    @pytest.fixture(scope="class")
    def dim(self) -> tuple[int, int]:
        return 4, 4

    # TODO: Is it guaranteed that clean_dir will be called first?
    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, c) -> None:
        r = c.rectangle(width=2, height=2, fill_color=RED)
        c.add(r)

    def frame(self) -> list[str]:
        return [
            "wwww",
            "wbbw",
            "wbbw",
            "wwww",
        ]


class TestRectangle3x3(ImageTestBase):
    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, c) -> None:
        r = c.rectangle(width=3, height=3, fill_color=RED)
        c.add(r)

    def frame(self) -> list[str]:
        return [
            "wwwww",
            "wbbbw",
            "wbRbw",
            "wbbbw",
            "wwwww",
        ]


class TestRectangleNoBorder3x3(ImageTestBase):
    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, c) -> None:
        r = c.rectangle(width=3, height=3, fill_color=RED, stroke_width=0)
        c.add(r)

    def frame(self) -> list[str]:
        return [
            "wwwww",
            "wRRRw",
            "wRRRw",
            "wRRRw",
            "wwwww",
        ]


class TestRectangleConstraint(ImageTestBase):
    @pytest.fixture(scope="class")
    def dim(self) -> tuple[int, int]:
        return 5, 6

    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, c) -> None:
        r1 = c.rectangle(width=2, height=2)
        r2 = c.rectangle(width=2, height=2)
        c.add(r1)
        c.add(r2, P(0, r1.height + 1))

    def frame(self) -> list[str]:
        return [
            "wwwww",
            "wbbww",
            "wbbww",
            "wwwww",
            "wbbww",
            "wbbww",
        ]


class TestLineRelative(ImageTestBase):
    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, c) -> None:
        r = c.line(start=P(0, 1), end=P(2, 1))
        c.add(r)

    def frame(self) -> list[str]:
        return [
            "wwwww",
            "wwwww",
            "wbbbw",
            "wwwww",
            "wwwww",
        ]


class TestDottedLine(ImageTestBase):
    @pytest.fixture(scope="class")
    def dim(self) -> tuple[int, int]:
        return 15, 5

    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, c) -> None:
        r = c.dotted_line(start=P(0, 2), end=P(13, 2), dash_len=4)
        c.add(r)

    def frame(self) -> list[str]:
        return [
            "wwwwwwwwwwwwwww",
            "wwwwwwwwwwwwwww",
            "bbbwbbbwbbbwbbb",
            "wwwwwwwwwwwwwww",
            "wwwwwwwwwwwwwww",
        ]


class TestArrow(ImageTestBase):
    @pytest.fixture(scope="class")
    def dim(self) -> tuple[int, int]:
        return 12, 11

    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, c) -> None:
        r = c.arrow(start=P(5, 0), end=P(5, 8), arrowhead_ratio=0.5)
        c.add(r)

    def frame(self) -> list[str]:
        return [
            "wwwwwwwwwwww",
            "wwwwwwbwwwww",
            "wwwwwwbwwwww",
            "wwwwwwbwwwww",
            "wwwwwwbwwwww",
            "wwwwwwbwwwww",
            "wwwbwwbwbwww",
            "wwwwbwbbwwww",
            "wwwwwbbbwwww",
            "wwwwwwbwwwww",
            "wwwwwwwwwwww",
        ]


class TestDoubleSidedArrow(ImageTestBase):
    @pytest.fixture(scope="class")
    def dim(self) -> tuple[int, int]:
        return 12, 11

    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, c) -> None:
        r = c.arrow(start=P(5, 0), end=P(5, 8), arrowhead_ratio=0.5, double_sided=True)
        c.add(r)

    def frame(self) -> list[str]:
        return [
            "wwwwwwwwwwww",
            "wwwwwwbwwwww",
            "wwwwbbbbwwww",
            "wwwbwwbwbwww",
            "wwwwwwbwwwww",
            "wwwwwwbwwwww",
            "wwwbwwbwbwww",
            "wwwwbwbbwwww",
            "wwwwwbbbwwww",
            "wwwwwwbwwwww",
            "wwwwwwwwwwww",
        ]


class TestGrid(ImageTestBase):
    @pytest.fixture(scope="class")
    def dim(self) -> tuple[int, int]:
        return 13, 13

    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, c, dim) -> None:
        c.add(c.grid(step_size=4, width=dim[0] - 4, height=dim[1] - 4), P(1, 1))

    def frame(self) -> list[str]:
        return [
            "wwwwwwwwwwwww",
            "wwwwwwwwwwwww",
            "wwbbbbbbbbbww",
            "wwbwwwbwwwbww",
            "wwbwwwbwwwbww",
            "wwbwwwbwwwbww",
            "wwbbbbbbbbbww",
            "wwbwwwbwwwbww",
            "wwbwwwbwwwbww",
            "wwbwwwbwwwbww",
            "wwbbbbbbbbwww",
            "wwwwwwwwwwwww",
            "wwwwwwwwwwwww",
        ]


class TestDynamicSizeGrid(ImageTestBase):
    @pytest.fixture(scope="class")
    def dim(self) -> tuple[int, int]:
        return 13, 13

    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, c) -> None:
        c.add(c.grid(step_size=4))

    def frame(self) -> list[str]:
        return [
            "wwwwwwwwwwwww",
            "wbbbbbbbbbbbb",
            "wbwwwbwwwbwww",
            "wbwwwbwwwbwww",
            "wbwwwbwwwbwww",
            "wbbbbbbbbbbbb",
            "wbwwwbwwwbwww",
            "wbwwwbwwwbwww",
            "wbwwwbwwwbwww",
            "wbbbbbbbbbbbb",
            "wbwwwbwwwbwww",
            "wbwwwbwwwbwww",
            "wbwwwbwwwbwww",
        ]


class TestSpacerSize1(ImageTestBase):
    @pytest.fixture(scope="class")
    def dim(self) -> tuple[int, int]:
        return 6, 4

    @pytest.fixture(scope="class", autouse=True)
    def spacer(self, c) -> Spacer:
        return c.spacer(width=1)

    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, c, spacer) -> None:
        hlayout = c.hlayout()

        r1 = c.rectangle(width=2, height=2)
        r2 = c.rectangle(width=2, height=2)

        hlayout.add(r1)
        hlayout.add(spacer)
        hlayout.add(r2)

        c.add(hlayout)

    def test_spacer_size(self, spacer) -> None:
        assert spacer.width == 1
        assert spacer.height == 1

    def frame(self) -> list[str]:
        return [
            "wwwwww",
            "wbbwbb",
            "wbbwbb",
            "wwwwww",
        ]


class TestSpacerSize2(ImageTestBase):
    @pytest.fixture(scope="class")
    def dim(self) -> tuple[int, int]:
        return 4, 7

    @pytest.fixture(scope="class", autouse=True)
    def spacer(self, c) -> Spacer:
        return c.spacer(height=2)

    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, c) -> None:
        vlayout = c.vlayout()

        r1 = c.rectangle(width=2, height=2)
        r2 = c.rectangle(width=2, height=2)

        vlayout.add(r1)
        vlayout.add(c.spacer(height=2))
        vlayout.add(r2)

        c.add(vlayout)

    def test_spacer_size(self, spacer) -> None:
        assert spacer.width == 1
        assert spacer.height == 2

    def frame(self) -> list[str]:
        return [
            "wwww",
            "wbbw",
            "wbbw",
            "wwww",
            "wwww",
            "wbbw",
            "wbbw",
        ]
