import logging
from pathlib import Path

import pytest

import pyanimate.style as sty
from pyanimate.animation import FadeIn, StaticAnimation
from pyanimate.layout import Rectangle
from pyanimate.shape import BLACK, RED, WHITE

from . import convert_to_ascii

logger = logging.getLogger(__name__)


class TestEmptyScene:
    def test_no_file_created(self, scene) -> None:
        p = Path("output.png")
        scene.play(20, p)
        assert not p.exists()


class TestNonPng:
    def test_exception(self, scene) -> None:
        with pytest.raises(ValueError):
            scene.play(20, "output.gif")

        with pytest.raises(ValueError):
            scene.play(20, "output.webp")

        with pytest.raises(ValueError):
            scene.play(20, "output.avif")


class TestSingleFrameRectangleScene2x2:
    # TODO: Is it guaranteed that clean_dir will be called first?
    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, scene, canvas) -> None:
        r = Rectangle(2, 2, fill_color=RED)
        canvas.add(r)
        scene.add(StaticAnimation(r))

    def test_single_frame(self, im) -> None:
        assert im.n_frames == 1

    def test_correct_image(self, im) -> None:
        assert im.size == (4, 4)
        assert convert_to_ascii(im) == [
            "wwww",
            "wbbw",
            "wbbw",
            "wwww",
        ]


class TestSingleFrameRectangleScene3x3:
    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, scene, canvas) -> None:
        r = Rectangle(3, 3, fill_color=RED)
        canvas.add(r)
        scene.add(StaticAnimation(r))

    def test_single_frame(self, im) -> None:
        assert im.n_frames == 1

    def test_correct_image(self, im) -> None:
        assert im.size == (5, 5)
        assert convert_to_ascii(im) == [
            "wwwww",
            "wbbbw",
            "wbRbw",
            "wbbbw",
            "wwwww",
        ]


class TestFadeIn:
    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, scene, canvas) -> None:
        r = Rectangle(3, 3, fill_color=RED)
        canvas.add(r)
        scene.add(FadeIn(r))

    def test_num_frames(self, im) -> None:
        assert im.n_frames == 20

    def test_correct_frames(self, im) -> None:
        assert im.size == (5, 5)
        for i in range(im.n_frames):
            im.seek(i)
            assert convert_to_ascii(im) == [
                "wwwww",
                "wbbbw",
                "wbRbw",
                "wbbbw",
                "wwwww",
            ]

    def test_increasing_alpha(self, im) -> None:
        prev_r_alpha = -1
        prev_b_alpha = -1
        for i in range(im.n_frames):
            already_set_b_alpha = False
            im.seek(i)

            for r in range(im.height):
                for c in range(im.width):
                    pixel = im.getpixel((r, c))
                    if pixel[:3] == RED[:3]:
                        alpha = pixel[3]
                        assert alpha > prev_r_alpha
                        prev_r_alpha = alpha

                        assert already_set_b_alpha
                        assert prev_r_alpha == prev_b_alpha
                    elif pixel[:3] == BLACK[:3]:
                        alpha = pixel[3]
                        if already_set_b_alpha:
                            # All black pixels should have the same alpha
                            assert alpha == prev_b_alpha
                        else:
                            assert alpha > prev_b_alpha
                            prev_b_alpha = alpha

                            already_set_b_alpha = True
                    elif pixel[:3] == WHITE[:3]:
                        assert pixel[3] == 0
                    else:
                        assert False
