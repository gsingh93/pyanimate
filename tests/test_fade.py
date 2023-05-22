import pytest

from pyanimate.animation import FadeIn
from pyanimate.layout import Rectangle, TextBox, VLayout
from pyanimate.shape import BLACK, RED, WHITE

from . import AnimationTestBase


class FadeInTestBase(AnimationTestBase):
    pass
    # @pytest.mark.dependency(depends=["correct_frames"])
    # def test_increasing_alpha(self, s_im) -> None:
    #     prev_r_alpha = -1
    #     prev_b_alpha = -1
    #     for i in range(s_im.n_frames):
    #         already_set_b_alpha = False
    #         s_im.seek(i)

    #         for r in range(s_im.height):
    #             for c in range(s_im.width):
    #                 pixel = s_im.getpixel((r, c))
    #                 if pixel[:3] == RED[:3]:
    #                     alpha = pixel[3]
    #                     assert alpha > prev_r_alpha
    #                     prev_r_alpha = alpha

    #                     assert already_set_b_alpha
    #                     assert prev_r_alpha == prev_b_alpha
    #                 elif pixel[:3] == BLACK[:3]:
    #                     alpha = pixel[3]
    #                     if already_set_b_alpha:
    #                         # All black pixels should have the same alpha
    #                         assert alpha == prev_b_alpha
    #                     else:
    #                         assert alpha > prev_b_alpha
    #                         prev_b_alpha = alpha

    #                         already_set_b_alpha = True
    #                 elif pixel[:3] == WHITE[:3]:
    #                     assert pixel[3] == 0
    #                 else:
    #                     assert False


class TestFadeInRectangle(FadeInTestBase):
    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, s) -> None:
        c = s.keyframe()
        r = Rectangle(canvas=c, width=3, height=3, fill_color=RED)
        c.add(r)
        s.add(FadeIn(r))

    def num_frames(self) -> int:
        return 5

    def frame(self, num) -> list[str]:
        if num == 0:
            return [
                "wwwww",
                "wwwww",
                "wwwww",
                "wwwww",
                "wwwww",
            ]

        return [
            "wwwww",
            "w???w",
            "w???w",
            "w???w",
            "wwwww",
        ]


class TestFadeInCanvas(FadeInTestBase):
    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, s) -> None:
        c = s.keyframe()
        r = TextBox(canvas=c, text="A", font_size=4)
        vlayout = VLayout(canvas=c)
        vlayout.add(r)
        c.add(vlayout)
        s.add(FadeIn(vlayout, duration=2))

    def num_frames(self) -> int:
        return 11

    def frame(self, num) -> list[str]:
        if num == 0:
            return [
                "wwwww",
                "wwwww",
                "wwwww",
                "wwwww",
                "wwwww",
            ]

        return [
            "wwwww",
            "w???w",
            "w???w",
            "w???w",
            "wwwww",
        ]


class TestFadeInText(FadeInTestBase):
    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, s) -> None:
        c = s.keyframe()
        t = TextBox(canvas=c, text="A", font_size=4)
        c.add(t)
        s.add(FadeIn(t))

    def num_frames(self) -> int:
        return 5

    def frame(self, num) -> list[str]:
        if num == 0:
            return [
                "wwwww",
                "wwwww",
                "wwwww",
                "wwwww",
                "wwwww",
            ]

        return [
            "wwwww",
            "w???w",
            "w???w",
            "w???w",
            "w???w",
        ]
