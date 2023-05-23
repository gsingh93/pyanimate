import logging
from pathlib import Path

import pytest

from pyanimate.animation import FadeIn, StaticAnimation, Translate
from pyanimate.layout import Line, Rectangle, TextBox
from pyanimate.shape import BLACK, RED, WHITE
from pyanimate.shape import Point as P

from . import AnimationTestBase, convert_to_ascii

logger = logging.getLogger(__name__)


class TestEmptyScene:
    def test_no_file_created(self, s) -> None:
        p = Path("output.png")
        s.play(20, p)
        assert not p.exists()


# class TestNonPng:
#     def test_exception(self, s) -> None:
#         with pytest.raises(ValueError):
#             s.play(20, "output.gif")

#         with pytest.raises(ValueError):
#             s.play(20, "output.webp")

#         with pytest.raises(ValueError):
#             s.play(20, "output.avif")


class TestStaticAnimation5x5(AnimationTestBase):
    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, s) -> None:
        c = s.keyframe()
        r = Rectangle(canvas=c, width=3, height=3, fill_color=RED)
        c.add(r)
        s.add(StaticAnimation(r))

    def num_frames(self) -> int:
        return 1

    def frame(self, _: int) -> list[str]:
        return [
            "wwwww",
            "wbbbw",
            "wbRbw",
            "wbbbw",
            "wwwww",
        ]


class TestStaticAnimation6x6(AnimationTestBase):
    @pytest.fixture(scope="class")
    def dim(self) -> tuple[int, int]:
        return 6, 6

    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, s) -> None:
        c = s.keyframe()
        r = Rectangle(canvas=c, width=3, height=3, fill_color=RED)
        c.add(r)
        s.add(StaticAnimation(r))

    def num_frames(self) -> int:
        return 1

    def frame(self, _: int) -> list[str]:
        return [
            "wwwwww",
            "wbbbww",
            "wbRbww",
            "wbbbww",
            "wwwwww",
            "wwwwww",
        ]


class TestTranslateDown(AnimationTestBase):
    @pytest.fixture(scope="class")
    def dim(self) -> tuple[int, int]:
        return 6, 6

    @pytest.fixture(scope="class")
    def frame_rate(self) -> int:
        return 2

    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, s) -> None:
        c = s.keyframe()
        r = Rectangle(canvas=c, width=3, height=3, fill_color=RED)
        c.add(r)
        s.add(Translate(c, r, P(0, 2), relative=True))

    def num_frames(self) -> int:
        return 2

    def frame(self, frame_num: int) -> list[str]:
        if frame_num == 0:
            return [
                "wwwwww",
                "wbbbww",
                "wbRbww",
                "wbbbww",
                "wwwwww",
                "wwwwww",
            ]

        assert frame_num == 1
        return [
            "wwwwww",
            "wwwwww",
            "wbbbww",
            "wbRbww",
            "wbbbww",
            "wwwwww",
        ]


class TestTranslateUp(AnimationTestBase):
    @pytest.fixture(scope="class")
    def dim(self) -> tuple[int, int]:
        return 6, 6

    @pytest.fixture(scope="class")
    def frame_rate(self) -> int:
        return 2

    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, s) -> None:
        c = s.keyframe()
        r = Rectangle(canvas=c, width=3, height=3, fill_color=RED)
        c.add(r)
        s.add(Translate(c, r, P(0, -2), relative=True))

    def num_frames(self) -> int:
        return 2

    def frame(self, frame_num: int) -> list[str]:
        if frame_num == 0:
            return [
                "wwwwww",
                "wbbbww",
                "wbRbww",
                "wbbbww",
                "wwwwww",
                "wwwwww",
            ]

        assert frame_num == 1
        return [
            "wbbbww",
            "wbRbww",
            "wbbbww",
            "wwwwww",
            "wwwwww",
            "wwwwww",
        ]


class TestTranslateUpConstraint(AnimationTestBase):
    @pytest.fixture(scope="class")
    def dim(self) -> tuple[int, int]:
        return 6, 6

    @pytest.fixture(scope="class")
    def frame_rate(self) -> int:
        return 2

    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, s) -> None:
        c = s.keyframe()
        r1 = Rectangle(canvas=c, width=2, height=2)
        r2 = Rectangle(canvas=c, width=2, height=2)
        c.add(r1)
        c.add(r2, P(r1.width, r1.height))
        s.add(StaticAnimation(c))

        p = c.children[r2]
        c = s.keyframe()

        # print("w, h", r1.width, r1.height)
        # print("latest w, h", r1.latest().width, r1.latest().height)

        assert p.x.variables()[0]._var is r1.width._var
        assert p.y.variables()[0]._var is r1.height._var

        # p makes sense based on the logging output from deepcopy, but it doesn't match
        # the latest values of r1.width and r1.height. The variables should be the same
        # ('is' relation)
        p = c.children[r2.latest()]
        # print("p.x, p.y", p.x, p.y)
        # print("p.x, p.y vars", p.x.variables()[0], p.y.variables()[0])

        assert p.x.variables()[0]._var is r1.latest().width._var
        assert p.y.variables()[0]._var is r1.latest().height._var

        s.add(Translate(c, r2.latest(), P(0, -2), relative=True))

    def num_frames(self) -> int:
        return 2

    def frame(self, frame_num: int) -> list[str]:
        if frame_num == 0:
            return [
                "wwwwww",
                "wbbwww",
                "wbbwww",
                "wwwbbw",
                "wwwbbw",
                "wwwwww",
            ]

        assert frame_num == 1
        return [
            "wwwwww",
            "wbbwww",
            "wbbbbw",
            "wwwbbw",
            "wwwwww",
            "wwwwww",
        ]


class TestTranslateLine(AnimationTestBase):
    @pytest.fixture(scope="class")
    def dim(self) -> tuple[int, int]:
        return 6, 6

    @pytest.fixture(scope="class")
    def frame_rate(self) -> int:
        return 2

    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, s) -> None:
        c = s.keyframe()
        l = Line(canvas=c, end=P(3, 2), start=P(1, 2), fill_color=RED)
        c.add(l)
        s.add(Translate(c, l, P(0, -1), relative=True))

    def num_frames(self) -> int:
        return 2

    def frame(self, frame_num: int) -> list[str]:
        if frame_num == 0:
            return [
                "wwwwww",
                "wwwwww",
                "wwbbbw",
                "wwbbbw",
                "wwbbbw",
                "wwwwww",
            ]

        assert frame_num == 1
        return [
            "wwwwww",
            "wwbbbw",
            "wwbbbw",
            "wwbbbw",
            "wwwwww",
            "wwwwww",
        ]
