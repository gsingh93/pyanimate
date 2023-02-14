#!/usr/local/bin/python3
"""
TODO:
- Customize bit labels on top or bottom
- Option to add all bit labels, not just at the boundaries
- Option to add extra text below each field
- Option to generate ascii art instead of PNG
- Multiple lanes (see Vol 4, Part E, Figure 5.1)
"""

import logging
import math
import os
from argparse import ArgumentParser
from enum import Enum
from typing import Dict, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFont import FreeTypeFont

import layout
from layout import (
    Anchor, Arrow, Canvas, DottedLine, HLayout, Renderer, Spacer, Style, Table,
    Text, TextBox, VLayout
)
from point import Point as P

#from loguru import logger

logger = logging.getLogger(os.path.basename(__file__))


class RenderContext:
    def __init__(self, width, height, bit_width, dpi: Tuple[int, int], scale):
        self.scale = scale
        self.w = int(width * scale)
        self.h = int(height * scale)
        self.cell_height = int(100 * scale)
        self.bit_width = int(bit_width * scale)
        self.dpi = dpi

    def __repr__(self):
        return repr(ctx.__dict__)


# TODO: Set ImageDraw.ink and fill default properties
class PILRenderer(Renderer):
    def __init__(self, ctx: RenderContext):
        logger.debug('RenderContext: %s', repr(ctx))
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
        self.image.save(filename, dpi=ctx.dpi)

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


ctx: Optional[RenderContext] = None
default_style: Optional[Style] = None


class Mode(str, Enum):
    WIDTH = 'width'
    POSITION = 'position'

    def __str__(self):
        return self.value


class Endianness(str, Enum):
    BIG = 'big'
    LITTLE = 'little'

    def __str__(self):
        return self.value


def parse_args():
    parser = ArgumentParser(description='Description')
    parser.add_argument(
        '-r',
        '--relative',
        action='store_true',
        help=
        'Make the width of a bit as small as possible while preserving the relative sizes between fields'
    )
    parser.add_argument('-s', '--scale', default=2, type=int, help='TODO')
    parser.add_argument(
        '-m', '--mode', choices=list(Mode), default=Mode.WIDTH, help='TODO'
    )
    parser.add_argument(
        '-e',
        '--endianness',
        choices=list(Endianness),
        default=Endianness.LITTLE,
        help='TODO'
    )
    parser.add_argument('-w', '--width', default=1920, type=int, help='TODO')
    parser.add_argument('--height', default=1080, type=int, help='TODO')
    parser.add_argument('-c', '--crop', action='store_true', help='TODO')
    parser.add_argument('--bit-width', default=100, type=int, help='TODO')
    parser.add_argument('-p', '--padding', default=10, type=int, help='TODO')
    parser.add_argument('-f', '--font-size', default=32, type=int, help='TODO')
    parser.add_argument('-o', '--output', default="output.png", help='TODO')
    parser.add_argument(
        '--log-level',
        choices=['debug', 'info', 'warning', 'error', 'critical'],
        default='notset',
    )

    return parser.parse_args()


class Unit(str, Enum):
    BITS = "bit"
    BYTES = "byte"


class Field:
    def __init__(
        self,
        name,
        bits,
        display_bits=None,
        start_label=None,
        end_label=None,
        unit=Unit.BITS,
    ):
        if isinstance(bits, tuple):
            assert len(bits) == 2
            self.min = bits[0]
            self.max = bits[1]
        elif isinstance(bits, list):
            sorted_bits = sorted(bits)
            self.min = sorted_bits[0]
            self.max = sorted_bits[1]
        elif isinstance(bits, int):
            self.min = bits
            self.max = bits
        else:
            assert False

        if not display_bits:
            display_bits = self.max

        self.name = name
        self.bits = bits
        self.display_bits = display_bits
        self.start_label = start_label
        self.end_label = end_label
        self.unit = unit


def get_bit_label(bits, unit):
    if isinstance(bits, tuple):
        # A range from min to max
        assert len(bits) == 2
        return f"{bits[0]} - {bits[1]} {unit}s"
    elif isinstance(bits, list):
        # A set of specific values
        assert len(bits) > 1
        str_bits = list(map(str, bits))
        return ', '.join(str_bits[:-1]) + f' or {str_bits[-1]} {unit}s'
    elif isinstance(bits, int):
        # A single value
        s = f"{bits} {unit}"
        if bits != 1:
            s += "s"

        return s
    else:
        assert False


def phys_fields():
    return "Bluetooth BR/EDR Packet", [
        Field("Access Code", [68, 72], 3),
        Field("Packet\nHeader", 54, 2),
        Field("Payload", (0, 2790), 6),
    ]


def packet_header_fields():
    return "Bluetooth BR/EDR Packet Header", [
        Field("LT_ADDR", 3),
        Field("Type", 4),
        Field("Flow", 1),
        Field("ARQN", 1),
        Field("SEQN", 1),
        Field("HEC", 8, 6),
    ]


def payload_header_fields():
    return "Bluetooth BR/EDR Payload Header", [
        Field('LLID', 2),
        Field('Flow', 1),
        Field('Length', 5),
    ]


def acl_payload_format_fields():
    return "Bluetooth ACL Payload", [
        Field('Payload\nHeader', 8, 2),
        Field('Payload Body', (0, 2790), 6),
        Field('MIC', 32, 4),
        Field('CRC', 16, 3),
    ]


def bdaddr_fields():
    return "Bluetooth Device Address", [
        Field('NAP', 16),
        Field('UAP', 8),
        Field('LAP', 24),
    ]


def create_canvas(
    title, fields, mode: Mode, endianness: Endianness, style
) -> Canvas:
    c = Canvas()

    v = VLayout(align="center")

    # Title
    logger.info("Laying out title")
    v.add(Text(title, style=default_style._replace(anchor=Anchor.TOP_LEFT)))

    # LSB/MSB
    logger.info("Laying out LSB/MSB")
    # TODO: Find a better way of scaling all of these dimensions
    lsb_msb = HLayout(width=1000, height=50)

    if endianness == Endianness.LITTLE:
        left_text = "LSB"
        right_text = "MSB"
    else:
        left_text = "MSB"
        right_text = "LSB"
        fields.reverse()

    lsb_msb.add(Text(left_text, width=750 * ctx.scale, align="left"))
    lsb_msb.add(Text(right_text, width=750 * ctx.scale, align="right"))

    v.add(lsb_msb)
    v.add(Spacer())

    # Table
    logger.info("Laying out table")
    t = Table()
    for field in fields:
        cell_width = ctx.bit_width * field.display_bits
        text = f"{field.name}\n({field.max})"
        if mode == Mode.WIDTH:
            text = f"{field.name}"
        t.add(
            TextBox(
                text,
                align=Anchor.MIDDLE_MIDDLE,
                width=cell_width,
                height=75 * ctx.scale
            )
        )

    # Labels
    logger.info("Laying out labels")
    h = HLayout()
    current_bit = 0
    for field in fields:
        cell_width = ctx.bit_width * field.display_bits

        if mode == Mode.WIDTH:
            h.add(DottedLine(end=P(0, 50 * ctx.scale)))

            label = get_bit_label(field.bits, field.unit.value)

            # TODO: We're cheating here to get the text width
            renderer = PILRenderer(ctx)
            _, _, text_width, _ = renderer.text_bbox(label, default_style)
            arrow_length = (
                cell_width - text_width - (default_style.padding * 4)
            ) // 2
            arrow = Arrow(double_sided=True, end=P(arrow_length, 0))

            spacer = Spacer()
            bit_label = HLayout()
            bit_label.add(spacer)
            bit_label.add(arrow, pos=(0, 20 * ctx.scale))
            bit_label.add(spacer)
            bit_label.add(Text(label, width=text_width, height=50 * ctx.scale))
            bit_label.add(spacer)
            bit_label.add(arrow, pos=(0, 20 * ctx.scale))
            bit_label.add(spacer)

            h.add(bit_label)
        else:
            h.add(
                Text(str(current_bit), width=cell_width, height=50 * ctx.scale)
            )

        current_bit += field.max
    h.add(DottedLine(end=P(0, 50 * ctx.scale)))

    v.add(t)
    v.add(h, pos=(0, style.padding))

    c.add(v)

    return c


def main():
    global ctx, default_style
    args = parse_args()

    logging.basicConfig(
        level=args.log_level.upper(),
        format="[%(filename)s:%(lineno)s - %(funcName)s()] %(message)s"
    )

    ctx = RenderContext(
        args.width,
        args.height,
        args.bit_width,
        (300, 300),
        args.scale,
    )
    default_style = Style(
        padding=args.padding * args.scale,
        font='Roboto-Regular.ttf',
        font_size=args.font_size * args.scale,
    )
    layout.set_style(default_style)

    #title, fields = phys_fields()
    #title, fields = packet_header_fields()
    #title, fields = payload_header_fields()
    #title, fields = bdaddr_fields()
    title, fields = acl_payload_format_fields()

    if args.relative:
        display_bits = list(map(lambda f: f.display_bits, fields))
        gcd = math.gcd(*display_bits)
        fields = list(
            map(lambda f: Field(f.name, f.bits, f.display_bits // gcd), fields)
        )
        if gcd == 1:
            logger.warning('Warning: gcd is 1')

    canvas = create_canvas(
        title, fields, args.mode, args.endianness, default_style
    )

    logger.info("Starting rendering")
    renderer = PILRenderer(ctx)
    canvas.render(renderer)

    if args.crop:
        renderer.crop_to_fit()

    renderer.show()
    renderer.output(args.output)


if __name__ == '__main__':
    main()
