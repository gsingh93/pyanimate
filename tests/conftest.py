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
from pyanimate.style import Style

style = Style(
    padding=1, font=str(Path("./tests/Roboto-Regular.ttf").resolve()), font_size=8
)
sty.set_style(style)


def is_ci() -> bool:
    return os.getenv("CI") == "true"


def pytest_configure(config: pytest.Config):
    if is_ci():
        config.option.log_cli_level = "verbose"


@pytest.fixture(autouse=True)
def no_output(capsys):
    yield

    # Verify that no output was printed to stdout when running tests on CI
    if is_ci():
        out, _ = capsys.readouterr()
        if out:
            pytest.fail(f"Output captured: {out}")


class MockRenderer(Renderer):
    def output(self, filename) -> None:
        raise NotImplementedError()

    def rectangle(self, p1, p2, style: Style) -> None:
        raise NotImplementedError()

    def text(self, text: str, p, style: Style) -> None:
        raise NotImplementedError()

    def text_bbox(self, text: str, style: Style) -> tuple[int, int, int, int]:
        raise NotImplementedError()

    def line(self, p1, p2, style: Style) -> None:
        raise NotImplementedError()

    def set_dimensions(self, dim) -> None:
        raise NotImplementedError()

    def crop_to_fit(self) -> None:
        raise NotImplementedError()

    @property
    def width(self) -> int:
        raise NotImplementedError()

    @property
    def height(self) -> int:
        raise NotImplementedError()


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


@pytest.fixture(scope="class")
def mock_renderer() -> Renderer:
    return MockRenderer()


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
        assert s.cur_keyframe
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
