from abc import ABC, abstractmethod

import pytest


class AnimationTestBase(ABC):
    show = False

    @pytest.mark.dependency(name="num_frames")
    def test_num_frames(self, s_im) -> None:
        if self.show:
            s_im.show()
        actual = s_im.n_frames
        expected = self.num_frames()
        assert actual == expected

    @pytest.mark.dependency(name="dimensions")
    def test_dimensions(self, s_im, dim):
        actual = s_im.size
        expected = dim
        assert actual == expected

    @pytest.mark.dependency(name="correct_frames", depends=["num_frames", "dimensions"])
    def test_correct_frames(self, s_im) -> None:
        for i in range(s_im.n_frames):
            s_im.seek(i)
            actual = convert_to_ascii(s_im)
            expected = self.frame(i)
            assert actual == expected

    @abstractmethod
    def frame(self, frame_num) -> list[str]:
        raise NotImplementedError()

    @abstractmethod
    def num_frames(self) -> int:
        raise NotImplementedError()


def convert_to_ascii(image):
    ascii_pixels = []

    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    for y in range(image.height):
        for x in range(image.width):
            pixel = image.getpixel((x, y))[:3]
            # yapf: disable
            ascii_pixels.append(
                'R' if pixel == RED else
                'G' if pixel == GREEN else
                'B' if pixel == BLUE else
                'w' if pixel == WHITE else
                'b' if pixel == BLACK else
                '?'
            )
            # yapf: enable

    ascii_pixels = [
        "".join(ascii_pixels[i : i + image.width])
        for i in range(0, len(ascii_pixels), image.width)
    ]

    return ascii_pixels
