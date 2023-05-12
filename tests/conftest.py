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
from pyanimate.scene import Scene

style = sty.Style(padding=1, font="Roboto-Regular.ttf", font_size=8)
sty.set_style(style)


@pytest.fixture(scope="class")
def canvas() -> Canvas:
    return Canvas()


@pytest.fixture(scope="class")
def scene(canvas) -> Scene:
    return Scene(canvas)


@pytest.fixture(scope="class", name="im")
def image(scene) -> Generator[ImageT, None, None]:
    p = Path("output.png")
    scene.play(20, p)
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
