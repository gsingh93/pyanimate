#!/usr/bin/env python3

import logging
import math
import os
from argparse import ArgumentParser
from enum import Enum

from kiwisolver import UnsatisfiableConstraint

import pyanimate.style
from pyanimate.layout import Align, Canvas, Table
from pyanimate.renderer import PILRenderer, RenderContext
from pyanimate.shape import Point as P
from pyanimate.style import Anchor, Style

logger = logging.getLogger(os.path.basename(__file__))

# These global variables will be initialized in main, so we assume they are not Optional
# types
ctx: RenderContext = None  # type: ignore[reportGeneralTypeIssues]
default_style: Style = None  # type: ignore[reportGeneralTypeIssues]


class Mode(str, Enum):
    WIDTH = "width"
    POSITION = "position"

    def __str__(self) -> str:
        return self.value


class Endianness(str, Enum):
    BIG = "big"
    LITTLE = "little"

    def __str__(self) -> str:
        return self.value


def parse_args():
    parser = ArgumentParser(description="TODO: Description")
    parser.add_argument(
        "-r",
        "--relative",
        action="store_true",
        help="Make the width of a bit as small as possible while preserving the relative sizes between fields",
    )
    parser.add_argument("-s", "--scale", default=2, type=int, help="TODO")
    parser.add_argument(
        "-m", "--mode", choices=list(Mode), default=Mode.WIDTH, help="TODO"
    )
    parser.add_argument(
        "-e",
        "--endianness",
        choices=list(Endianness),
        default=Endianness.LITTLE,
        help="TODO",
    )
    parser.add_argument("--no-show", action="store_true", help="TODO")
    parser.add_argument("-w", "--width", default=1920, type=int, help="TODO")
    parser.add_argument("--height", default=1080, type=int, help="TODO")
    parser.add_argument("-c", "--crop", action="store_true", help="TODO")
    parser.add_argument("--bit-width", default=100, type=int, help="TODO")
    parser.add_argument("-p", "--padding", default=10, type=int, help="TODO")
    parser.add_argument("-f", "--font-size", default=32, type=int, help="TODO")
    parser.add_argument("-o", "--output", default="output.png", help="TODO")
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error", "critical"],
        default="warning",
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
    ) -> None:
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
        return ", ".join(str_bits[:-1]) + f" or {str_bits[-1]} {unit}s"
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
        Field("LLID", 2),
        Field("Flow", 1),
        Field("Length", 5),
    ]


def acl_payload_format_fields():
    return "Bluetooth ACL Payload", [
        Field("Payload\nHeader", 8, 2),
        Field("Payload Body", (0, 2790), 6),
        Field("MIC", 32, 4),
        Field("CRC", 16, 3),
    ]


def bdaddr_fields():
    return "Bluetooth Device Address", [
        Field("NAP", 16),
        Field("UAP", 8),
        Field("LAP", 24),
    ]


def create_canvas(title, fields, mode: Mode, endianness: Endianness, style) -> Canvas:
    c = Canvas()

    v = c.vlayout(align=Align.CENTER)

    # Title
    logger.info("Laying out title")
    v.add(c.textbox(title, style=default_style.clone(anchor=Anchor.TOP_LEFT)))

    # LSB/MSB
    logger.info("Laying out LSB/MSB")
    lsb_msb = c.hlayout(width=1000)

    if endianness == Endianness.LITTLE:
        left_text = "LSB"
        right_text = "MSB"
    else:
        left_text = "MSB"
        right_text = "LSB"
        fields.reverse()

    lsb_msb.add(c.textbox(left_text, width=750, align=Align.LEFT, stroke_width=0))
    lsb_msb.add(c.textbox(right_text, width=750, align=Align.RIGHT, stroke_width=0))

    v.add(lsb_msb)
    v.add(c.spacer())

    # Table
    logger.info("Laying out table")
    t = Table(canvas=c)
    for field in fields:
        cell_width = ctx.bit_width * field.display_bits
        text = f"{field.name}\n({field.max})"
        if mode == Mode.WIDTH:
            text = f"{field.name}"
        t.add(
            c.textbox(
                text,
                align=Anchor.MIDDLE_MIDDLE,
                width=cell_width,
                height=75,
            )
        )

    # Labels
    logger.info("Laying out labels")
    h = c.hlayout()
    current_bit = 0
    for field in fields:
        cell_width = ctx.bit_width * field.display_bits

        if mode == Mode.WIDTH:
            h.add(c.dotted_line(vec=P(0, 50)))

            label = get_bit_label(field.bits, field.unit.value)
            label_tb = c.textbox(label, height=50)

            arrow_length = (
                cell_width - label_tb.width - (default_style.padding * 4)
            ) / 2
            arrow1 = c.arrow(double_sided=True, vec=P(label_tb.width, 0))
            arrow2 = c.arrow(
                double_sided=True, vec=P(arrow_length, 0)
            )  # arrow1.clone(True)

            # TODO: See if we can use clone here
            s1 = c.spacer()
            s2 = c.spacer()  # s1.clone(True)
            s3 = c.spacer()  # s1.clone(True)
            s4 = c.spacer()  # s1.clone(True)

            bit_label = c.hlayout()
            bit_label.add(s1)
            bit_label.add(arrow1, offset=P(0, 20))
            bit_label.add(s2)
            bit_label.add(label_tb)
            bit_label.add(s3)
            bit_label.add(arrow2, offset=P(0, 20))
            bit_label.add(s4)

            h.add(bit_label)
        else:
            h.add(c.textbox(str(current_bit), width=cell_width, height=50))

        current_bit += field.max

    h.add(c.dotted_line(vec=P(0, 50)))

    v.add(t)
    v.add(h, offset=P(0, style.padding))

    c.add(v)

    return c


def main() -> None:
    global ctx, default_style
    args = parse_args()

    logging.basicConfig(
        level=args.log_level.upper(),
        format="[%(filename)s:%(lineno)s - %(funcName)s()] %(levelname)s: %(message)s",
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
        font="./examples/Roboto-Regular.ttf",
        font_size=args.font_size * args.scale,
    )
    pyanimate.style.set_style(default_style)

    # title, fields = phys_fields()
    # title, fields = packet_header_fields()
    # title, fields = payload_header_fields()
    title, fields = bdaddr_fields()
    # title, fields = acl_payload_format_fields()

    if args.relative:
        display_bits = list(map(lambda f: f.display_bits, fields))
        gcd = math.gcd(*display_bits)
        fields = list(
            map(lambda f: Field(f.name, f.bits, f.display_bits // gcd), fields)
        )
        if gcd == 1:
            logger.warning("Warning: gcd is 1")

    canvas = create_canvas(title, fields, args.mode, args.endianness, default_style)

    logger.info("Starting rendering")
    renderer = PILRenderer(ctx)
    try:
        canvas.render(renderer)
    except UnsatisfiableConstraint:
        logger.error("\n%s", canvas.solver.dumps())
        raise

    if args.crop:
        renderer.crop_to_fit()

    if not args.no_show:
        renderer.show()
    renderer.output(args.output)


if __name__ == "__main__":
    main()
