import shutil
from functools import singledispatchmethod
from pathlib import Path

from PIL import GifImagePlugin, Image

from . import get_logger
from .animation import Animation, AnimationGroup
from .layout import Canvas, Proxy
from .renderer import PILRenderer, RenderContext

logger = get_logger(__name__)

FRAME_DIR = Path(".frames")

default_render_ctx = RenderContext(
    1920,
    1080,
    (300, 300),
    2,
)


# TODO: Probably not the right name for this class
class KeyFrame:
    def __init__(self, canvas: Canvas) -> None:
        self.canvas = canvas
        self.animations: list[Animation] = []


class Scene:
    def __init__(self, render_ctx: RenderContext = default_render_ctx) -> None:
        self.keyframes: list[KeyFrame] = []
        self.cur_keyframe = None
        self.renderer = PILRenderer(render_ctx)
        self.frame_num = 0

    def keyframe(self) -> Canvas:
        if len(self.keyframes) == 0:
            self.cur_keyframe = KeyFrame(Canvas())
        else:
            self.cur_keyframe = KeyFrame(self.keyframes[-1].canvas.clone())

        self.keyframes.append(self.cur_keyframe)

        return Proxy(self.cur_keyframe.canvas)
        # return self.cur_keyframe.canvas

    @singledispatchmethod
    def add(self, anim: Animation) -> None:
        assert self.cur_keyframe is not None
        self.cur_keyframe.animations.append(anim)

    @add.register
    def _(self, animations: list) -> None:
        assert self.cur_keyframe is not None
        self.cur_keyframe.animations.append(AnimationGroup(animations))

    def render(self) -> None:
        logger.info("Rendering frame %d", self.frame_num)
        assert self.cur_keyframe is not None

        logger.verbose("Canvas:\n%s", self.cur_keyframe.canvas.dump())
        self.cur_keyframe.canvas.render(self.renderer)

        self.renderer.output(FRAME_DIR / f"frame-{self.frame_num}.png")
        self.frame_num += 1
        self.renderer.clear()

    def play(
        self, frame_rate: int = 50, output_filename: str | Path | None = None
    ) -> None:
        if FRAME_DIR.exists():
            logger.warning('Deleting existing "%s" directory', FRAME_DIR)
            assert FRAME_DIR.is_dir()
            shutil.rmtree(FRAME_DIR)

        FRAME_DIR.mkdir()

        for keyframe in self.keyframes:
            self.cur_keyframe = keyframe
            for anim in keyframe.animations:
                logger.debug("Playing animation %s", anim)
                anim.play(self.render, frame_rate)
                logger.debug("Finished animation %s", anim)

        logger.info(
            "Rendered %d frames at %d fps (%s seconds)",
            self.frame_num,
            frame_rate,
            self.frame_num / frame_rate,
        )

        if output_filename:
            self._save(1000 / frame_rate, output_filename)

    def _save(self, frame_duration_ms: float, output_filename: str | Path) -> None:
        images = [
            Image.open(FRAME_DIR / f"frame-{i}.png") for i in range(0, self.frame_num)
        ]

        if len(images) == 0:
            logger.error("No frames found")
            return

        # TODO: Not sure what disposal should be, different values work better for GIF
        # vs PNG
        if Path(output_filename).suffix == ".gif":
            disposal = 2
            # By default the GIF will be in palette mode ("P"), and converting to this
            # from RGB will throw an exception
            GifImagePlugin.LOADING_STRATEGY = GifImagePlugin.LoadingStrategy.RGB_ALWAYS
        else:
            disposal = 0
        images[0].save(
            output_filename,
            save_all=True,
            append_images=images[1:],
            duration=frame_duration_ms,
            disposal=disposal,
            loop=1,
        )

        logger.info("Saved animation to %s", output_filename)
