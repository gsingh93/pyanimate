#!/usr/bin/env python3
import sys

sys.path.insert(0, '..')

import logging
import os
from argparse import ArgumentParser

import style as sty
from animation import FadeIn, RgbTransform, Translate
from layout import Arrow, Canvas, TextBox, VLayout
from PIL import Image
from point import Point as P
from renderer import RenderContext
from scene import Scene

ctx = RenderContext(
    1920,
    1080,
    100,
    (300, 300),
    2,
)

style = sty.Style(padding=20, font='Roboto-Regular.ttf', font_size=32)
sty.set_style(style)

logger = logging.getLogger(os.path.basename(__file__))


def parse_args():
    parser = ArgumentParser(description='TODO: Description')
    parser.add_argument(
        '-f',
        '--frame-rate',
        default=20,
        type=int,
        help='The number of frames per second',
    )
    # TODO: use this
    parser.add_argument('-s', '--scale', default=2, type=int, help='TODO')
    parser.add_argument('-o', '--output', default="output.png", help='TODO')
    parser.add_argument(
        '--log-level',
        choices=['debug', 'info', 'warning', 'error', 'critical'],
        default='warning',
    )

    return parser.parse_args()


def create_scene() -> Scene:
    c = Canvas()
    s = Scene(c)

    col1 = (0, 255, 0)
    col2 = (255, 255, 0)
    col3 = (255, 0, 255)
    col4 = (0, 255, 255)

    ###################################################
    #                  Initial Scene                  #
    ###################################################
    vlayout = VLayout()
    t = TextBox(
        'prev stack frame',
        width=250,
        height=120,
        style=style.clone(fill_color=(80, 80, 80))
    )
    vlayout.add(t)

    t = TextBox('RIP', width=250, height=50, style=style.clone(fill_color=col1))
    vlayout.add(t)

    # t = t.clone()
    # # TODO: uncommenting the following line results in text fading not working
    # #t.style = style.clone()
    # t.set_text("RBP")
    # vlayout.add(t)

    t = TextBox('RBP', width=250, height=50, style=style.clone(fill_color=col4))
    vlayout.add(t)

    t = TextBox(
        'canary', width=250, height=50, style=style.clone(fill_color=col2)
    )
    vlayout.add(t)

    buf_tb = TextBox(
        'char buf[16]',
        width=250,
        height=100,
        style=style.clone(fill_color=col3)
    )
    vlayout.add(buf_tb)

    c.add(vlayout)

    # TODO: Figure out how to avoid a negative arrow length
    arrow = Arrow(end=P(0, 0), start=P(100, 0), arrow_length=-10)
    c.add(arrow, P(300, vlayout.height))

    s.add(FadeIn(c))

    ###################################################
    #               Overflow buffer                   #
    ###################################################

    s.add(
        [
            Translate(c, arrow, P(0, -100), relative=True),
            RgbTransform(buf_tb, col3, (255, 0, 0))
        ]
    )

    # TODO: Change content of buffer to "AAAAAAAAAAAAAAAAAA"

    # TODO: c.translate(r2, P(140, 0)) ? The downside is a lot of logic now goes in Canvas when it doesn't need to
    # s.add(Translate(c, r1, P(100, 0)))
    # s.add(Translate(c, r2, P(140, 0)))

    return s


def main():
    args = parse_args()

    logging.basicConfig(
        level=args.log_level.upper(),
        format=
        "[%(filename)s:%(lineno)s - %(funcName)s()] %(levelname)s: %(message)s"
    )

    if args.frame_rate < 1 or args.frame_rate > 60:
        logger.error('Frame rate must be between 1 and 60, inclusive')
        sys.exit(1)

    s = create_scene()
    s.play(args.frame_rate, args.output)

    with Image.open(args.output) as im:
        im.show()


if __name__ == '__main__':
    main()
