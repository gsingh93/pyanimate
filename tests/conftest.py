import os
import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
from PIL import Image
from PIL.Image import Image as ImageT

from pyanimate import style as sty
from pyanimate.layout import Canvas
from pyanimate.renderer import PILRenderer, RenderContext, Renderer
from pyanimate.scene import Scene

style = sty.Style(padding=1, font="Roboto-Regular.ttf", font_size=8)
sty.set_style(style)


@pytest.fixture(scope="class")
def dim() -> tuple[int, int]:
    return 5, 5


@pytest.fixture(scope="class")
def render_ctx(dim) -> RenderContext:
    return RenderContext(dim[0], dim[1], 1, (300, 300), 1)


@pytest.fixture(scope="class", name="c")
def canvas() -> Canvas:
    return Canvas()


@pytest.fixture(scope="class", name="s")
def scene(render_ctx: RenderContext) -> Scene:
    return Scene(render_ctx)


@pytest.fixture(scope="class")
def renderer(render_ctx) -> Renderer:
    return PILRenderer(render_ctx)


@pytest.fixture(scope="class", name="c_im")
def canvas_image(c: Canvas, renderer: Renderer) -> Generator[ImageT, None, None]:
    p = Path("output.png")

    c.render(renderer)
    renderer.crop_to_fit()
    renderer.output(p)
    assert p.exists(), f"File {p.absolute()} does not exist"
    with Image.open(p) as im:
        yield im


@pytest.fixture(scope="class")
def frame_rate() -> int:
    return 5


@pytest.fixture(scope="class", name="s_im")
def scene_image(s: Scene, frame_rate: int) -> Generator[ImageT, None, None]:
    p = Path("output.png")
    import kiwisolver

    try:
        s.play(frame_rate, p)
    except kiwisolver.UnsatisfiableConstraint as e:
        res = s.cur_keyframe.canvas.solver.analyze(e)
        print("Exception analysis:")
        for var, constraints in res:
            print("Variable: ", var, var.value())
            for c in constraints:
                print(c)
        raise

    assert p.exists(), f"File {p.absolute()} does not exist"
    with Image.open(p) as im:
        yield im


@pytest.fixture(scope="class", autouse=True)
def clean_dir() -> Generator[None, None, None]:
    old_cwd = os.getcwd()
    new_path = tempfile.mkdtemp()
    os.chdir(new_path)
    yield
    os.chdir(old_cwd)
    shutil.rmtree(new_path)
