from abc import ABC, abstractmethod
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFont import FreeTypeFont

from . import get_logger
from .shape import Color
from .shape import Point as P
from .style import Style

logger = get_logger(__name__)


class RenderContext:
    def __init__(
        self, width: int, height: int, dpi: tuple[int, int], scale: float
    ) -> None:
        self.scale = scale
        self.w = width
        self.h = height
        self.dpi = dpi

    def __str__(self) -> str:
        return (
            f"RenderContext(w={self.w}, h={self.h}, dpi={self.dpi}, scale={self.scale})"
        )


class Renderer(ABC):
    @abstractmethod
    def output(self, filename: str | Path) -> None:
        raise NotImplementedError()

    @abstractmethod
    def rectangle(self, p1: P, p2: P, style: Style) -> None:
        raise NotImplementedError()

    @abstractmethod
    def text(self, text: str, p: P, style: Style) -> None:
        raise NotImplementedError()

    @abstractmethod
    def text_bbox(self, text: str, style: Style) -> tuple[int, int, int, int]:
        raise NotImplementedError()

    @abstractmethod
    def line(self, p1: P, p2: P, style: Style) -> None:
        raise NotImplementedError()

    @abstractmethod
    def set_dimensions(self, dim: P) -> None:
        raise NotImplementedError()

    @abstractmethod
    def crop(self, width, height) -> None:
        raise NotImplementedError()

    @property
    @abstractmethod
    def context(self) -> RenderContext:
        raise NotImplementedError()

    @property
    @abstractmethod
    def width(self) -> int:
        raise NotImplementedError()

    @property
    @abstractmethod
    def height(self) -> int:
        raise NotImplementedError()


# TODO: Set ImageDraw.ink and fill default properties
class PILRenderer(Renderer):
    def __init__(self, ctx: RenderContext) -> None:
        logger.info("%s", ctx)

        self.ctx = ctx

        self._w = int(ctx.w * ctx.scale)
        self._h = int(ctx.h * ctx.scale)

        # TODO: Make configurable
        self.background = Color(255, 255, 255, 255)

        self.image = Image.new("RGBA", (self._w, self._h), self.background)
        self.draw = ImageDraw.Draw(self.image)
        self.fonts: dict[tuple[str, int], FreeTypeFont] = {}

    @property
    def context(self) -> RenderContext:
        return self.ctx

    @property
    def width(self) -> int:
        return self._w

    @property
    def height(self) -> int:
        return self._h

    def _get_font(self, font: str, font_size: int) -> FreeTypeFont:
        key = (font, font_size)
        if key not in self.fonts:
            self.fonts[key] = ImageFont.truetype(*key)

        return self.fonts[key]

    def _composite_background(self, c: Color, a: int) -> Color:
        return self.background.mul(1 - (a / 255)) + c

    def set_dimensions(self, dim: P) -> None:
        logger.debug("Setting dimensions: %s", dim)
        # TODO: no scaling is applied here, it causes problems
        self._w, self._h = map(int, dim)

    def show(self) -> None:
        self.image.show()

    def output(self, filename: str | Path) -> None:
        # TODO: Font sizes don't seem to be scaled properly
        # self.image = self.image.resize(
        #     (self._w // ctx.scale, self._h // ctx.scale),
        #     resample=Resampling.LANCZOS
        # )
        # if ctx.scale != 1:
        #     logger.warning(
        #         f'Not resizing image, output will be {ctx.scale} times larger than requested'
        #     )
        self.image.save(filename, dpi=self.ctx.dpi)

    def crop(self, dim: P[int] | None = None, offset: P[int] = P(0, 0)) -> None:
        if dim is None:
            width, height = self._w - offset.x, self._h - offset.y
        else:
            width, height = dim

        assert width > 0 and height > 0, "Invalid crop dimensions"
        assert offset.x >= 0 and offset.y >= 0, "Invalid crop offset"
        assert (
            width + offset.x <= self._w and height + offset.y <= self._h
        ), "Crop out of bounds"

        logger.debug("Cropping to %dx%d", width, height)
        self.image = self.image.crop(
            (
                int(offset.x * self.ctx.scale),
                int(offset.y * self.ctx.scale),
                int(width * self.ctx.scale),
                int(height * self.ctx.scale),
            ),
        )

    def rectangle(self, p1: P, p2: P, style: Style) -> None:
        logger.verbose("Rectangle: %s %s", p1, p2)

        fill_color = self._composite_background(
            style.composite_fill_color, style.composite_alpha
        )
        stroke_color = self._composite_background(
            style.composite_stroke_color, style.composite_alpha
        )
        self.draw.rectangle(
            (p1.mul(self.ctx.scale), p2.mul(self.ctx.scale)),
            fill=fill_color,
            outline=stroke_color,
            width=int(style.stroke_width * self.ctx.scale),
        )

    def text(self, text: str, p: P, style: Style) -> None:
        logger.verbose("Text: %s %s", repr(text), p)
        font = self._get_font(style.font, int(style.font_size * self.ctx.scale))
        font_color = self._composite_background(
            style.composite_font_color, style.composite_alpha
        )
        self.draw.multiline_text(
            p.mul(self.ctx.scale),
            text,
            font=font,
            anchor=style.anchor,
            fill=font_color,
            align="center",
        )

    def text_bbox(self, text: str, style: Style) -> tuple[int, int, int, int]:
        # Since we're returning this information to the caller, we shouldn't scale it
        font = self._get_font(style.font, int(style.font_size))
        t = self.draw.textbbox((0, 0), text, font=font)
        return t

    def line(self, p1: P, p2: P, style: Style) -> None:
        # Dotted line is too verbose
        logger.verbose("Line: %s %s", p1, p2)
        logger.verbose(
            "Line scaled by %s: %s %s",
            self.ctx.scale,
            p1.mul(self.ctx.scale),
            p2.mul(self.ctx.scale),
        )
        stroke_color = self._composite_background(
            style.composite_stroke_color, style.composite_alpha
        )

        self.draw.line(
            [p1.mul(self.ctx.scale), p2.mul(self.ctx.scale)],
            fill=stroke_color,
            width=int(style.stroke_width * self.ctx.scale),
        )

    def clear(self) -> None:
        self.image = Image.new("RGBA", (self._w, self._h), self.background)
        self.draw = ImageDraw.Draw(self.image)
