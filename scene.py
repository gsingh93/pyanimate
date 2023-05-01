import logging
import shutil
from functools import singledispatchmethod
from pathlib import Path

from PIL import Image

from animation import Animation, AnimationGroup
from renderer import PILRenderer, RenderContext

logger = logging.getLogger(__name__)

FRAME_DIR = Path('.frames')

ctx = RenderContext(
    1920,
    1080,
    100,
    (300, 300),
    2,
)


class Scene:
    def __init__(self, canvas):
        self.animations: list[Animation] = []
        self.renderer = PILRenderer(ctx)
        self.canvas = canvas
        self.frame_num = 0

    @singledispatchmethod
    def add(self, anim: Animation):
        self.animations.append(anim)

    @add.register
    def _(self, animations: list):
        self.animations.append(AnimationGroup(animations))

    def render(self):
        self.canvas.render(self.renderer)
        self.renderer.crop_to_fit()
        self.renderer.output(FRAME_DIR / f'frame-{self.frame_num}.png')
        self.frame_num += 1
        self.renderer.clear()

    def play(self, frame_rate=50, output_filename=None):
        if FRAME_DIR.exists():
            logger.warning('Deleting existing "%s" directory', FRAME_DIR)
            assert FRAME_DIR.is_dir()
            shutil.rmtree(FRAME_DIR)

        FRAME_DIR.mkdir()

        for anim in self.animations:
            anim.play(self.render, frame_rate)

        logger.info(
            'Rendered %d frames at %d fps (%s seconds)', self.frame_num,
            frame_rate, self.frame_num / frame_rate
        )

        if output_filename:
            # GIFs don't support alpha transparency, WebP should work but gives
            # an error, and AVIF is not supported by PIL, so only PNG is
            # supported
            if Path(output_filename).suffix != '.png':
                raise ValueError(
                    f'Invalid output file {output_filename}, only PNG files are supported'
                )

            self._save(1000 / frame_rate, output_filename)

    def _save(self, frame_duration_ms, output_filename):
        images = [
            Image.open(FRAME_DIR / f'frame-{i}.png')
            for i in range(0, self.frame_num)
        ]

        images[0].save(
            output_filename,
            save_all=True,
            append_images=images[1:],
            duration=frame_duration_ms,
            loop=0,
        )

        logger.info("Saved animation to %s", output_filename)
