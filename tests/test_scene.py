import logging
from pathlib import Path

import pytest

from pyanimate.animation import StaticAnimation, Translate
from pyanimate.shape import RED
from pyanimate.shape import Point as P

from . import AnimationTestBase

logger = logging.getLogger(__name__)


class TestEmptyScene:
    def test_no_file_created(self, s) -> None:
        p = Path("output.png")
        s.play(20, p)
        assert not p.exists()


class TestStaticAnimation5x5(AnimationTestBase):
    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, s) -> None:
        c = s.keyframe()
        r = c.rectangle(width=3, height=3, fill_color=RED)
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
        r = c.rectangle(width=3, height=3, fill_color=RED)
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
        r = c.rectangle(width=3, height=3, fill_color=RED)
        c.add(r)
        s.add(Translate(r, P(0, 2), relative=True))

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
        r = c.rectangle(width=3, height=3, fill_color=RED)
        c.add(r)
        s.add(Translate(r, P(0, -2), relative=True))

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
        r1 = c.rectangle(width=2, height=2)
        r2 = c.rectangle(width=2, height=2)
        c.add(r1)
        c.add(r2, P(r1.width, r1.height))
        s.add(StaticAnimation(c))

        # TODO: Should I overwrite getitem to work with proxies?
        p = c.children[r2.latest()]
        assert p.x.variables()[0]._var is r1.width._var
        assert p.y.variables()[0]._var is r1.height._var

        c = s.keyframe()

        p = c.children[r2.latest()]
        assert p.x.variables()[0]._var is r1.width._var
        assert p.y.variables()[0]._var is r1.height._var

        s.add(Translate(r2, P(0, -2), relative=True))

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
        vlayout = c.vlayout()
        r1 = c.rectangle(width=2, height=2)
        r2 = c.rectangle(width=2, height=2)
        vlayout.add(r1)
        vlayout.add(r2, P(r1.width, r1.height))
        c.add(vlayout)
        s.add(StaticAnimation(c))

        c = s.keyframe()

        s.add(Translate(r2, P(0, -2), relative=True))

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


class TestTranslateUpCanvasConstraint(AnimationTestBase):
    @pytest.fixture(scope="class")
    def dim(self) -> tuple[int, int]:
        return 7, 7

    @pytest.fixture(scope="class")
    def frame_rate(self) -> int:
        return 2

    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, s) -> None:
        c = s.keyframe()
        vlayout = c.vlayout()
        r1 = c.rectangle(width=2, height=2)
        r2 = c.rectangle(width=2, height=2)
        vlayout.add(r1)
        c.add(vlayout)
        c.add(r2, P(r1.width, r1.height))

        s.add(StaticAnimation(c))

        c = s.keyframe()

        s.add(Translate(r2, P(0, -2), relative=True))

    def num_frames(self) -> int:
        return 2

    def frame(self, frame_num: int) -> list[str]:
        if frame_num == 0:
            return [
                "wwwwwww",
                "wwbbwww",
                "wwbbwww",
                "wwwbbww",
                "wwwbbww",
                "wwwwwww",
                "wwwwwww",
            ]
        assert frame_num == 1
        return [
            "wwwwwww",
            "wwbbwww",
            "wwbbbww",
            "wwwbbww",
            "wwwwwww",
            "wwwwwww",
            "wwwwwww",
        ]


class TestTranslateLine(AnimationTestBase):
    @pytest.fixture(scope="class")
    def dim(self) -> tuple[int, int]:
        return 7, 5

    @pytest.fixture(scope="class")
    def frame_rate(self) -> int:
        return 2

    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, s) -> None:
        c = s.keyframe()

        end = P(3, 1)
        start = P(1, 1)
        l = c.line(vec=end - start, fill_color=RED)
        c.add(l, start)

        s.add(Translate(l, P(0, -2), relative=True))

    def num_frames(self) -> int:
        return 2

    def frame(self, frame_num: int) -> list[str]:
        if frame_num == 0:
            return [
                "wwwwwww",
                "wwwwwww",
                "wwbbbww",
                "wwwwwww",
                "wwwwwww",
            ]

        assert frame_num == 1
        return [
            "wwwwwww",
            "wwbbbww",
            "wwwwwww",
            "wwwwwww",
            "wwwwwww",
        ]


@pytest.mark.xfail
class TestAnimationGroup(AnimationTestBase):
    def num_frames(self) -> int:
        assert False

    def frame(self, frame_num: int) -> list[str]:
        assert False
