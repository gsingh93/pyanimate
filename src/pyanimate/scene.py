import logging
import shutil
from functools import singledispatchmethod
from pathlib import Path

from PIL import Image

from .animation import Animation, AnimationGroup
from .layout import Canvas
from .renderer import PILRenderer, RenderContext

logger = logging.getLogger(__name__)

FRAME_DIR = Path(".frames")

ctx = RenderContext(
    1920,
    1080,
    100,
    (300, 300),
    2,
)


# TODO: Probably not the right name for this class
class KeyFrame:
    def __init__(self, canvas) -> None:
        self.canvas = canvas
        self.animations: list[Animation] = []


class Scene:
    def __init__(self) -> None:
        self.keyframes: list[KeyFrame] = []
        self.cur_keyframe = None
        self.renderer = PILRenderer(ctx)
        self.frame_num = 0

    def keyframe(self) -> Canvas:
        if len(self.keyframes) == 0:
            self.cur_keyframe = KeyFrame(Canvas())
        else:
            self.cur_keyframe = KeyFrame(self.keyframes[-1].canvas.clone())

        self.keyframes.append(self.cur_keyframe)

        return self.cur_keyframe.canvas

    @singledispatchmethod
    def add(self, anim: Animation) -> None:
        assert self.cur_keyframe is not None
        self.cur_keyframe.animations.append(anim)

    @add.register
    def _(self, animations: list) -> None:
        assert self.cur_keyframe is not None
        self.cur_keyframe.animations.append(AnimationGroup(animations))

    def render(self) -> None:
        logger.debug("Rendering frame %d", self.frame_num)
        assert self.cur_keyframe is not None

        self.cur_keyframe.canvas.render(self.renderer)
        self.renderer.crop_to_fit()
        self.renderer.output(FRAME_DIR / f"frame-{self.frame_num}.png")
        self.frame_num += 1
        self.renderer.clear()

    def play(self, frame_rate=50, output_filename=None):
        # Validate output filename early so we can fail fast
        if output_filename:
            # GIFs don't support alpha transparency, WebP should work but gives
            # an error, and AVIF is not supported by PIL, so only PNG is
            # supported
            if Path(output_filename).suffix != ".png":
                raise ValueError(
                    f"Invalid output file {output_filename}, only PNG files are supported"
                )

        if FRAME_DIR.exists():
            logger.warning('Deleting existing "%s" directory', FRAME_DIR)
            assert FRAME_DIR.is_dir()
            shutil.rmtree(FRAME_DIR)

        FRAME_DIR.mkdir()

        for keyframe in self.keyframes:
            self.cur_keyframe = keyframe
            for anim in keyframe.animations:
                anim.play(self.render, frame_rate)

        logger.info(
            "Rendered %d frames at %d fps (%s seconds)",
            self.frame_num,
            frame_rate,
            self.frame_num / frame_rate,
        )

        if output_filename:
            self._save(1000 / frame_rate, output_filename)

    def _save(self, frame_duration_ms, output_filename) -> None:
        images = [
            Image.open(FRAME_DIR / f"frame-{i}.png") for i in range(0, self.frame_num)
        ]

        if len(images) == 0:
            logger.error("No frames found")
            return

        images[0].save(
            output_filename,
            save_all=True,
            append_images=images[1:],
            duration=frame_duration_ms,
            loop=0,
        )

        logger.info("Saved animation to %s", output_filename)
