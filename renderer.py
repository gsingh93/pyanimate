import logging
from abc import ABC, abstractmethod
from typing import Dict, Tuple

from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFont import FreeTypeFont

from style import Style

logger = logging.getLogger(__name__)


class RenderContext:
    def __init__(self, width, height, bit_width, dpi: Tuple[int, int], scale):
        self.scale = scale
        self.w = int(width * scale)
        self.h = int(height * scale)
        self.cell_height = int(100 * scale)
        self.bit_width = int(bit_width * scale)
        self.dpi = dpi

    def __repr__(self):
        return repr(self.__dict__)


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
    def __init__(self, ctx: RenderContext):
        logger.debug('RenderContext: %s', repr(ctx))

        self.ctx = ctx

        self._w = ctx.w
        self._h = ctx.h

        self.image = Image.new("RGB", (self._w, self._h), "white")
        self.draw = ImageDraw.Draw(self.image)
        self.fonts: Dict[Tuple[str, int], FreeTypeFont] = {}

    def _get_font(self, font: str, font_size: int) -> FreeTypeFont:
        key = (font, font_size)
        if key not in self.fonts:
            self.fonts[key] = ImageFont.truetype(*key)

        return self.fonts[key]

    def set_dimensions(self, dim):
        self._w, self._h = dim

    def show(self):
        self.image.show()

    def output(self, filename: str):
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

    def crop_to_fit(self):
        self.image = self.image.crop((0, 0, self._w, self._h))

    def rectangle(self, p1, p2, style: Style):
        logger.debug("Rectangle: %s %s", p1, p2)
        self.draw.rectangle(
            (p1, p2), fill=style.fill_color, outline=style.stroke_color
        )

    def text(self, text, p, style: Style):
        logger.debug("Text: %s %s", repr(text), p)
        font = self._get_font(style.font, style.font_size)
        self.draw.multiline_text(
            p,
            text,
            font=font,
            anchor=style.anchor,
            fill=style.font_color,
            align="center",
        )

    def text_bbox(self, text, style) -> Tuple[int, int, int, int]:
        font = self._get_font(style.font, style.font_size)
        return self.draw.textbbox((0, 0), text, font=font)

    def line(self, p1, p2, style):
        # Dotted line is too verbose
        # logger.debug("Line: %s %s", p1, p2)
        self.draw.line([p1, p2], fill=style.stroke_color, width=1)
