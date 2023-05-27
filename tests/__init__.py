from abc import ABC, abstractmethod

import pytest


def normalize_expected_output(expected: list[str], actual: list[str]) -> list[str]:
    # A '.' in the expected image means that the pixel may vary between multiple
    # renders, so we replace it with the actual pixel value.
    for i, row in enumerate(expected):
        for j, val in enumerate(row):
            if val == ".":
                row = row[:j] + actual[i][j] + row[j + 1 :]
                expected[i] = row

    return expected


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
            expected = normalize_expected_output(self.frame(i), actual)
            assert actual == expected

    @abstractmethod
    def frame(self, frame_num) -> list[str]:
        raise NotImplementedError()

    @abstractmethod
    def num_frames(self) -> int:
        raise NotImplementedError()


class ImageTestBase(ABC):
    show = False

    @pytest.mark.dependency(name="dimensions")
    def test_dimensions(self, c_im, dim):
        actual = c_im.size
        expected = dim
        assert actual == expected

    @pytest.mark.dependency(name="correct_frames", depends=["dimensions"])
    def test_correct_frames(self, c_im) -> None:
        actual = convert_to_ascii(c_im)
        expected = normalize_expected_output(self.frame(), actual)

        assert actual == expected

    @abstractmethod
    def frame(self) -> list[str]:
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
