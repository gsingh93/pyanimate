import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Tuple

from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFont import FreeTypeFont

from .shape import Color
from .shape import Point as P
from .style import Style

logger = logging.getLogger(__name__)


class RenderContext:
    def __init__(
        self, width: int, height: int, bit_width: int, dpi: Tuple[int, int], scale: int
    ) -> None:
        self.scale = scale
        self.w = width
        self.h = height
        self.cell_height = int(100 * scale)
        self.bit_width = int(bit_width * scale)
        self.dpi = dpi

    def __str__(self) -> str:
        return (
            f"RenderContext(w={self.w}, h={self.h}, dpi={self.dpi}, scale={self.scale})"
        )


class Renderer(ABC):
    @abstractmethod
    def rectangle(self, p1, p2, style: Style):
        raise NotImplementedError()

    @abstractmethod
    def text(self, text: str, p, style: Style):
        raise NotImplementedError()

    @abstractmethod
    def text_bbox(self, text: str, style: Style) -> Tuple[int, int, int, int]:
        raise NotImplementedError()

    @abstractmethod
    def line(self, p1, p2, style: Style):
        raise NotImplementedError()

    @abstractmethod
    def set_dimensions(self, dim):
        raise NotImplementedError()


# TODO: Set ImageDraw.ink and fill default properties
class PILRenderer(Renderer):
    def __init__(self, ctx: RenderContext) -> None:
        logger.info("%s", ctx)

        self.ctx = ctx

        self._w = ctx.w * ctx.scale
        self._h = ctx.h * ctx.scale

        # TODO: Make configurable
        self.background = Color(255, 255, 255, 255)

        self.image = Image.new("RGBA", (self._w, self._h), self.background)
        self.draw = ImageDraw.Draw(self.image)
        self.fonts: Dict[Tuple[str, int], FreeTypeFont] = {}

    def _get_font(self, font: str, font_size: int) -> FreeTypeFont:
        key = (font, font_size)
        if key not in self.fonts:
            self.fonts[key] = ImageFont.truetype(*key)

        return self.fonts[key]

    def set_dimensions(self, dim: P) -> None:
        self._w, self._h = map(int, dim.mul(self.ctx.scale))

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

    def crop_to_fit(self) -> None:
        logger.debug("Cropping to %dx%d", self._w, self._h)
        self.image = self.image.crop((0, 0, self._w, self._h))

    def rectangle(self, p1: P, p2: P, style: Style) -> None:
        logger.debug("Rectangle: %s %s", p1, p2)
        fill_color = style.fill_color + Color.from_alpha(style.composite_alpha)
        stroke_color = style.stroke_color + Color.from_alpha(style.composite_alpha)
        self.draw.rectangle(
            (p1.mul(self.ctx.scale), p2.mul(self.ctx.scale)),
            fill=fill_color,
            outline=stroke_color,
        )

    def text(self, text, p: P, style: Style) -> None:
        logger.debug("Text: %s %s", repr(text), p)
        font = self._get_font(style.font, style.font_size * self.ctx.scale)
        font_color = style.font_color + Color.from_alpha(style.composite_alpha)
        self.draw.multiline_text(
            p.mul(self.ctx.scale),
            text,
            font=font,
            anchor=style.anchor,
            fill=font_color,
            align="center",
        )

    def text_bbox(self, text, style) -> Tuple[int, int, int, int]:
        font = self._get_font(style.font, style.font_size * self.ctx.scale)
        return self.draw.textbbox((0, 0), text, font=font)

    def line(self, p1: P, p2: P, style) -> None:
        # Dotted line is too verbose
        # logger.debug("Line: %s %s", p1, p2)
        stroke_color = style.stroke_color + Color.from_alpha(style.composite_alpha)
        self.draw.line(
            [p1.mul(self.ctx.scale), p2.mul(self.ctx.scale)],
            fill=stroke_color,
            width=3,  # TODO: Make configurable
        )

    def clear(self) -> None:
        self.image = Image.new("RGBA", (self._w, self._h), self.background)
        self.draw = ImageDraw.Draw(self.image)
