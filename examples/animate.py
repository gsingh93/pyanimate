#!/usr/bin/env python3

import logging
import sys
from argparse import ArgumentParser

import kiwisolver
from PIL import Image

from pyanimate import style as sty
from pyanimate.animation import StaticAnimation, Translate
from pyanimate.layout import Arrow, TextBox, VLayout
from pyanimate.renderer import RenderContext
from pyanimate.scene import Scene
from pyanimate.shape import MAGENTA
from pyanimate.shape import Point as P

style = sty.Style(padding=20, font="Roboto-Regular.ttf", font_size=32)
sty.set_style(style)

logger = logging.getLogger(__name__)


def parse_args():
    parser = ArgumentParser(description="TODO: Description")
    parser.add_argument(
        "-f",
        "--frame-rate",
        default=20,
        type=int,
        help="The number of frames per second",
    )
    parser.add_argument("-w", "--width", default=1920, type=int, help="TODO")
    parser.add_argument("--height", default=1080, type=int, help="TODO")
    parser.add_argument("-s", "--scale", default=2, type=int, help="TODO")
    parser.add_argument("-o", "--output", default="output.png", help="TODO")
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error", "critical"],
        default="warning",
    )

    return parser.parse_args()


def create_scene(ctx: RenderContext) -> Scene:
    s = Scene(ctx)
    c = s.keyframe()

    ###################################################
    #                  Initial Scene                  #
    ###################################################
    vlayout = VLayout(canvas=c)
    # t = TextBox(
    #     "prev stack frame",
    #     canvas=c,
    #     width=250,
    #     height=120,
    #     style=style.clone(fill_color=Color(80, 80, 80)),
    # )
    # vlayout.add(t)

    # t = TextBox(
    #     "RIP", canvas=c, width=250, height=50, style=style.clone(fill_color=GREEN)
    # )
    # vlayout.add(t)

    # # t = t.clone()
    # # # TODO: uncommenting the following line results in text fading not working
    # # #t.style = style.clone()
    # # t.set_text("RBP")
    # # vlayout.add(t)

    # t = TextBox(
    #     "RBP", canvas=c, width=250, height=50, style=style.clone(fill_color=CYAN)
    # )
    # vlayout.add(t)

    # t = TextBox(
    #     "canary", canvas=c, width=250, height=50, style=style.clone(fill_color=YELLOW)
    # )
    # vlayout.add(t)

    buf_tb = TextBox(
        "char buf[16]",
        canvas=c,
        width=250,
        height=100,
        style=style.clone(fill_color=MAGENTA),
    )
    # vlayout.add(buf_tb)

    c.add(buf_tb)
    # c.add(vlayout)

    # arrow = Rectangle(canvas=c, width=50, height=50)
    arrow = Arrow(
        canvas=c,
        end=P(buf_tb.x + buf_tb.width + 20, buf_tb.y + buf_tb.height),
        start=P(buf_tb.x + buf_tb.width * 2, buf_tb.y + buf_tb.height),
        relative=False,
    )
    c.add(
        arrow,  # P(buf_tb.x + buf_tb.width * 2, buf_tb.y + buf_tb.height)  # P(100, 100)
    )

    s.add(StaticAnimation(c))
    # s.add(FadeIn(arrow, duration=2))

    ###################################################
    #               Overflow buffer                   #
    ###################################################

    c = s.keyframe()

    s.add(Translate(c, arrow.latest(), P(0, -100), relative=True))

    # s.add(
    #     [
    #         Translate(c, arrow, P(0, -100), relative=True),
    #         RgbTransform(buf_tb, MAGENTA, RED),
    #     ]
    # )

    # TODO: Change content of buffer to "AAAAAAAAAAAAAAAAAA"

    # TODO: c.translate(r2, P(140, 0)) ? The downside is a lot of logic now goes in Canvas when it doesn't need to
    # s.add(Translate(c, r1, P(100, 0)))
    # s.add(Translate(c, r2, P(140, 0)))

    return s


def main() -> None:
    args = parse_args()

    logging.basicConfig(
        level=args.log_level.upper(),
        format="[%(filename)s:%(lineno)s - %(funcName)s()] %(levelname)s: %(message)s",
    )

    if args.frame_rate < 1 or args.frame_rate > 60:
        logger.error("Frame rate must be between 1 and 60, inclusive")
        sys.exit(1)

    ctx = RenderContext(args.width, args.height, 100, (300, 300), args.scale)

    try:
        s = create_scene(ctx)
        s.play(args.frame_rate, args.output)
    except kiwisolver.UnsatisfiableConstraint as e:
        logger.exception(e)

        res = s.cur_keyframe.canvas.solver.analyze(e)
        print("Exception analysis:")
        for var, constraints in res:
            print("Variable: ", var, var.value())
            for c in constraints:
                print(c)

        sys.exit(1)

        # logger.error("\n%s", )
        # raise

    with Image.open(args.output) as im:
        im.show()


if __name__ == "__main__":
    main()
