import pytest

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
            "wb?b?",
            "wbbb?",
        ]


class TestLineRelative(ImageTestBase):
    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, c) -> None:
        r = c.line(start=P(0, 1), end=P(2, 1))
        c.add(r)

    def frame(self) -> list[str]:
        return [
            "wwwww",
            "wbbbw",
            "wbbbw",
            "wbbbw",
            "wwwww",
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


@pytest.mark.xfail
class TestDottedLine(ImageTestBase):
    def frame(self) -> list[str]:
        assert False


@pytest.mark.xfail
class TestArrow(ImageTestBase):
    def frame(self) -> list[str]:
        assert False


@pytest.mark.xfail
class TestGrid(ImageTestBase):
    def frame(self) -> list[str]:
        assert False


@pytest.mark.xfail
class TestSpacer(ImageTestBase):
    def frame(self) -> list[str]:
        assert False
