from abc import ABC, abstractmethod
from typing import Callable

from . import get_logger
from .layout import Object, ObjectProxy, _Proxy
from .shape import Color
from .shape import Point as P

logger = get_logger(__name__)


class Animation(ABC):
    def __init__(self, duration: float = 1.0) -> None:
        """
        Initialize an Animation object.

        Args:
        - duration: float, the duration of the animation in seconds

        Attributes:
        - duration: float, the duration of the animation in seconds
        - elapsed_time: float, the elapsed time of the animation in seconds
        """
        self.duration: float = duration
        self.elapsed_time: float = 0.0

    @abstractmethod
    def step(self) -> None:
        raise NotImplementedError()

    def play(self, render: Callable[[], None], frame_rate: int = 50) -> None:
        """
        Play the animation.

        Args:
        - render: function, a function that renders the animation
        - frame_rate: int, the number of frames per second

        This method plays the animation by repeatedly calling the `step` method and the `render` function.
        """
        frame_duration = 1 / frame_rate

        while self.elapsed_time < self.duration:
            self.step()
            # TODO: is there a better way to render other than a callback?
            render()
            self.elapsed_time += frame_duration

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(duration={self.duration})"


class AnimationGroup(Animation):
    def __init__(self, animations: list[Animation], **kwargs) -> None:
        """
        Initialize an AnimationGroup object.

        Args:
        - animations: list of Animation objects

        Attributes:
        - animations: list of Animation objects
        - duration: float, the duration of the animation in seconds (the maximum duration of all animations)
        """
        super().__init__(**kwargs)
        self.animations = animations
        self.duration = max(anim.duration for anim in animations)

    def step(self) -> None:
        """
        Update the state of all child animations by calling their `step` methods.
        """
        for anim in self.animations:
            # TODO: Is there a better way then setting this field manually?
            anim.elapsed_time = self.elapsed_time
            anim.step()


class StaticAnimation(Animation):
    def __init__(self, obj: Object, **kwargs) -> None:
        """
        Initialize a StaticAnimation object.

        Args:
        - obj: Object, the object to animate

        Attributes:
        - obj: Object, the object to animate
        """
        super().__init__(**kwargs)

        assert isinstance(obj, _Proxy)
        self.obj: Object = obj.latest()

    def step(self) -> None:
        pass


class Transform(Animation):
    def __init__(self, obj: Object | ObjectProxy, start_val, end_val, **kwargs) -> None:
        """
        Initialize a Transform object.

        Args:
        - obj: Object, the object to transform
        - start_val: float or tuple of floats, the start value of the transform
        - end_val: float or tuple of floats, the end value of the transform

        Attributes:
        - obj: Object, the object to transform
        - start_val: float or tuple of floats, the start value of the transform
        - val_diff: float or tuple of floats, the difference between the end value and the start value
        """
        super().__init__(**kwargs)
        if isinstance(obj, _Proxy):
            obj = obj.latest()
        self.obj: Object = obj
        self.start_val = start_val
        self.val_diff = end_val - start_val

    def step(self) -> None:
        """
        Calculate the new value of the transform and update the object by calling the `update_val` method.
        """
        progress = self.elapsed_time / self.duration
        new_val = self.calculate_new_val(progress)
        self.update_val(new_val)

    def calculate_new_val(self, progress: float):
        """
        Calculate the new value of the transform.

        Args:
        - progress: float, the progress of the animation (between 0 and 1)

        Returns:
        - float or tuple of floats, the new value of the transform
        """
        # TODO: Remove this special case
        if isinstance(self.val_diff, (Color, P)):
            logger.debug(
                "%s %s %s %s",
                self.start_val,
                self.val_diff,
                progress,
                self.val_diff.mul(progress),
            )
            return self.start_val + (self.val_diff.mul(progress))

        return self.start_val + (self.val_diff * progress)

    @abstractmethod
    def update_val(self, val) -> None:
        raise NotImplementedError()


class StyleTransform(Transform):
    def __init__(
        self,
        obj: Object | ObjectProxy,
        start_val,
        end_val,
        property_name: str,
        **kwargs,
    ) -> None:
        """
        Initialize a StyleTransform object.

        Args:
        - obj: Object, the object to transform
        - start_val: float or tuple of floats, the start value of the transform
        - end_val: float or tuple of floats, the end value of the transform
        - property_name: str, the name of the style property to update

        Attributes:
        - obj: Object, TODO
        """
        if isinstance(obj, _Proxy):
            obj = obj.latest()
        super().__init__(obj, start_val, end_val, **kwargs)
        self.property_name = property_name

    def update_val(self, val) -> None:
        # TODO: style should be immutable? but creating a new style object every
        # frame is expensive
        logger.verbose(
            "Updating %s.style.%s to %s",
            self.obj.__class__.__name__,
            self.property_name,
            val,
        )
        setattr(self.obj.style, self.property_name, val)


class RgbTransform(StyleTransform):
    def __init__(
        self, obj: Object | ObjectProxy, start_color: Color, end_color: Color, **kwargs
    ) -> None:
        if isinstance(obj, _Proxy):
            obj = obj.latest()
        super().__init__(obj, start_color, end_color, "_fill_color", **kwargs)

    def calculate_new_val(self, progress: float) -> Color:
        new_color = tuple(
            int(y + z)
            for y, z in zip(self.start_val, tuple(x * progress for x in self.val_diff))
        )
        return Color(*new_color)


class AlphaTransform(StyleTransform):
    def __init__(
        self, obj: Object | ObjectProxy, start_alpha: int, end_alpha: int, **kwargs
    ) -> None:
        if isinstance(obj, _Proxy):
            obj = obj.latest()
        super().__init__(obj, start_alpha, end_alpha, "_alpha", **kwargs)


class FadeIn(AlphaTransform):
    def __init__(
        self, obj: Object | ObjectProxy, start_alpha=0, end_alpha=255, **kwargs
    ) -> None:
        assert start_alpha < end_alpha
        if isinstance(obj, _Proxy):
            obj = obj.latest()
        super().__init__(obj, start_alpha, end_alpha, **kwargs)


class FadeOut(AlphaTransform):
    def __init__(
        self, obj: Object | ObjectProxy, start_alpha=255, end_alpha=0, **kwargs
    ) -> None:
        assert start_alpha > end_alpha
        if isinstance(obj, _Proxy):
            obj = obj.latest()
        super().__init__(obj, start_alpha, end_alpha, **kwargs)


class Translate(Transform):
    def __init__(
        self, obj: Object | ObjectProxy, dest: P, *, relative=False, **kwargs
    ) -> None:
        if isinstance(obj, _Proxy):
            obj = obj.latest()
        assert obj.parent is not None
        super().__init__(obj, obj.parent.children[obj], dest, **kwargs)
        # TODO: remove this special case
        if relative:
            self.val_diff = dest

    def update_val(self, val) -> None:
        parent = self.obj.parent
        assert parent is not None
        logger.debug(
            "Updating %s offset (parent %s) from %r to %r",
            self.obj,
            parent,
            parent.children[self.obj],
            val,
        )
        parent.children[self.obj] = val


# TODO
# class Rotate(Transform):
#     def __init__(self, obj, start_angle, end_angle) -> None:
#         super().__init__(obj, start_angle, end_angle)

#     def update_val(self, val) -> None:
#         pass


# TODO
# class Scale(Transform):
#     def __init__(self, obj, start_scale, end_scale) -> None:
#         super().__init__(obj, start_scale, end_scale)

#     def update_val(self, val) -> None:
#         pass
