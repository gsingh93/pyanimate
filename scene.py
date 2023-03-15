import logging
from functools import singledispatchmethod
from pathlib import Path

from animation import Animation, AnimationGroup
from renderer import PILRenderer, RenderContext

# TODO: Avoid defining this in two places
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

    def play(self, frame_rate=50):
        for anim in self.animations:
            anim.play(self.render, frame_rate)
