import logging
import time

from layout import Object
from point import Point as P

logger = logging.getLogger(__name__)


class Animation:
    def __init__(self, duration=1.0):
        self.duration: float = duration
        self.elapsed_time: float = 0.0
        self.start_time: float = 0.0

    def step(self):
        raise NotImplementedError()

    def play(self, render, frame_rate=50):
        frame_duration = 1 / frame_rate

        self.start_time = time.time()
        last_frame = self.start_time - frame_duration

        while self.elapsed_time < self.duration:
            cur_time = time.time()

            if cur_time - last_frame >= frame_duration:
                last_frame = cur_time

                self.step()
                # TODO: is there a better way to render other than a callback?
                render()
                self.elapsed_time = cur_time - self.start_time


class AnimationGroup(Animation):
    def __init__(self, animations: list[Animation]):
        super().__init__()
        self.animations = animations
        self.duration = max(anim.duration for anim in animations)

    def step(self):
        for anim in self.animations:
            # TODO: Is there a better way then setting this fields manually?
            anim.start_time = self.start_time
            anim.elapsed_time = self.elapsed_time
            anim.step()


class StaticAnimation(Animation):
    def __init__(self, obj: Object):
        super().__init__()
        self.obj = obj

    def step(self):
        pass


# TODO: Make abstract base class
class Transform(Animation):
    def __init__(self, obj, start_val, end_val):
        super().__init__()
        self.obj = obj
        self.start_val = start_val
        self.val_diff = 0  # TODO: handle tuples
        if not isinstance(end_val, tuple):
            self.val_diff = end_val - start_val

    def step(self):
        progress = self.elapsed_time / self.duration
        new_val = self.calculate_new_val(progress)
        self.update_val(new_val)

    def calculate_new_val(self, progress):
        return self.start_val + (self.val_diff * progress)

    def update_val(self, val):
        raise NotImplementedError()


class StyleTransform(Transform):
    def __init__(self, obj, start_val, end_val, property_name):
        super().__init__(obj, start_val, end_val)
        self.property_name = property_name

    def update_val(self, val):
        # TODO: style should be immutable? but creating a new style object every
        # frame is expensive
        setattr(self.obj.style, self.property_name, val)


class RgbTransform(StyleTransform):
    def __init__(self, obj, start_color, end_color):
        super().__init__(obj, start_color, end_color, '_fill_color')
        # TODO: Improve this
        self.val_diff = tuple(x - y for x, y in zip(end_color, start_color))

    def calculate_new_val(self, progress):
        new_color = tuple(
            int(y + z) for y, z in
            zip(self.start_val, tuple(x * progress for x in self.val_diff))
        )
        return new_color


class AlphaTransform(StyleTransform):
    def __init__(self, obj, start_alpha, end_alpha):
        super().__init__(obj, start_alpha, end_alpha, '_alpha')


class FadeIn(AlphaTransform):
    def __init__(self, obj: Object, start_alpha=0, end_alpha=255):
        assert start_alpha < end_alpha
        super().__init__(obj, start_alpha, end_alpha)


class FadeOut(AlphaTransform):
    def __init__(self, obj: Object, start_alpha=255, end_alpha=0):
        assert start_alpha > end_alpha
        super().__init__(obj, start_alpha, end_alpha)


class Translate(Transform):
    def __init__(
        self, parent: Object, child: Object, dest: P, *, relative=False
    ):
        super().__init__(child, parent.children[child], dest)
        self.parent = parent
        # TODO: remove this special case
        if relative:
            self.val_diff = dest

    def update_val(self, val):
        self.parent.add(self.obj, val)


# TODO
class Rotate(Transform):
    def __init__(self, obj, start_angle, end_angle):
        super().__init__(obj, start_angle, end_angle)

    def update_val(self, val):
        pass


# TODO
class Scale(Transform):
    def __init__(self, obj, start_scale, end_scale):
        super().__init__(obj, start_scale, end_scale)

    def update_val(self, val):
        pass
