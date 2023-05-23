import logging
from pathlib import Path

import pytest

from pyanimate.animation import StaticAnimation, Translate
from pyanimate.layout import Line, Rectangle, VLayout
from pyanimate.shape import RED
from pyanimate.shape import Point as P

from . import AnimationTestBase

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
        assert p.x.variables()[0]._var is r1.width._var
        assert p.y.variables()[0]._var is r1.height._var

        c = s.keyframe()

        p = c.children[r2.latest()]
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


class TestTranslateUpVLayoutConstraint2(AnimationTestBase):
    show = True

    @pytest.fixture(scope="class")
    def dim(self) -> tuple[int, int]:
        return 7, 7

    @pytest.fixture(scope="class")
    def frame_rate(self) -> int:
        return 2

    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, s) -> None:
        c = s.keyframe()
        vlayout = VLayout(canvas=c)
        r1 = Rectangle(canvas=c, width=2, height=2)
        r2 = Rectangle(canvas=c, width=2, height=2)
        vlayout.add(r1)
        c.add(vlayout)
        c.add(r2, P(r1.width, r1.height))

        s.add(StaticAnimation(c))

        c = s.keyframe()

        s.add(Translate(c, r2.latest(), P(0, -2), relative=True))

    def num_frames(self) -> int:
        return 4

    def frame(self, frame_num: int) -> list[str]:
        if frame_num == 0:
            return [
                "wwwwwww",
                "wbbwwww",
                "wbbwwww",
                "wwwbbww",
                "wwwbbww",
                "wwwwwww",
                "wwwwwww",
            ]
        elif frame_num == 1:
            return [
                "wwwwwww",
                "wwbbwww",
                "wwbbwww",
                "wwwbbww",
                "wwwbbww",
                "wwwwwww",
                "wwwwwww",
            ]
        elif frame_num == 2:
            return [
                "wwwwwww",
                "wbbwwww",
                "wbbwwww",
                "wwwbbww",
                "wwwbbww",
                "wwwwwww",
                "wwwwwww",
            ]

        assert frame_num == 3
        return [
            "wwwwwww",
            "wwwbbww",
            "wwwbbww",
            "wwwbbww",
            "wwwwwww",
            "wwwwwww",
            "wwwwwww",
        ]


@pytest.mark.skip("Need to debug why test is failing")
class TestTranslateUpVLayoutConstraint(AnimationTestBase):
    @pytest.fixture(scope="class")
    def dim(self) -> tuple[int, int]:
        return 7, 7

    @pytest.fixture(scope="class")
    def frame_rate(self) -> int:
        return 2

    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, s) -> None:
        c = s.keyframe()
        vlayout = VLayout(canvas=c)
        r1 = Rectangle(canvas=c, width=2, height=2)
        r2 = Rectangle(canvas=c, width=2, height=2)
        vlayout.add(r1)
        vlayout.add(r2, P(r1.width, r1.height))
        c.add(vlayout)
        s.add(StaticAnimation(c))

        # p = vlayout.children[r2]
        # assert p.x.variables()[0]._var is r1.width._var
        # assert p.y.variables()[0]._var is r1.height._var

        c = s.keyframe()

        # p = vlayout.children[r2.latest()]
        # assert p.x.variables()[0]._var is r1.latest().width._var
        # assert p.y.variables()[0]._var is r1.latest().height._var

        s.add(Translate(vlayout, r2.latest(), P(0, -2), relative=True))

    def num_frames(self) -> int:
        return 2

    def frame(self, frame_num: int) -> list[str]:
        if frame_num == 0:
            return [
                "wwwwwww",
                "wwbbwww",
                "wwbbwww",
                "wwwwwww",
                "wwwwwww",
                "wwwwbbw",
                "wwwwbbw",
            ]

        assert frame_num == 1
        return [
            "wwwwwww",
            "wwbbwww",
            "wwbbwww",
            "wwwwwww",
            "wwwwbbw",
            "wwwwbbw",
            "wwwwwww",
        ]
        # return [
        #     "wwwwwww",
        #     "wwwbbww",
        #     "wwwbbww",
        #     "wwwwwww",
        #     "wwwwwww",
        #     "wwwwwbb",
        #     "wwwwwbb",
        # ]


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


@pytest.mark.xfail
class TestAnimationGroup(AnimationTestBase):
    def num_frames(self) -> int:
        assert False

    def frame(self, frame_num: int) -> list[str]:
        assert False
