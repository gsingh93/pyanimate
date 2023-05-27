import pytest
from kiwisolver import UnsatisfiableConstraint

from pyanimate.layout import Line, Object, VLayout
from pyanimate.shape import RED
from pyanimate.shape import Point as P
from pyanimate.style import Style

from . import convert_to_ascii


class TestObject:
    def test_add(self, c) -> None:
        """
        Test that a child object is properly added to the parent object
        """
        parent = Object(c)
        child = Object(c)

        parent.add(child)

        assert child in parent.children
        # assert parent.children[child] == P(0, 0)
        assert child.parent == parent
        assert child.style.parent_obj_style == parent.style
        assert child.pos == P(0, 0)

    def test_add_twice(self, c) -> None:
        """
        Test that adding a child object twice raises an error
        """
        parent = Object(c)
        child = Object(c)

        parent.add(child)

        with pytest.raises(AssertionError):
            parent.add(child)

    def test_remove(self, c) -> None:
        obj = Object(c)
        c.add(obj)

        assert obj in c.children
        # assert c.children[obj] == P(0, 0)
        assert obj.parent == c
        assert obj.pos == P(0, 0)

        c.remove(obj)

        assert obj not in c.children
        assert obj.parent is None

        c.add(obj, P(10, 20))

        assert obj in c.children
        # assert c.children[obj] == P(10, 20)
        assert obj.parent == c
        # assert obj.pos == P(10, 20)

    def test_replace(self, c) -> None:
        pass

    def test_width(self, c, mock_renderer) -> None:
        obj = Object(c, width=10)
        obj.prepare(mock_renderer)
        assert obj.width.value() == 10

        obj = Object(c, width=10)
        obj.width = 20
        obj.prepare(mock_renderer)
        assert obj.width.value() == 20

        # TODO: Test setting width to constraint

    def test_height(self, c, mock_renderer) -> None:
        obj = Object(c, height=10)
        obj.prepare(mock_renderer)
        assert obj.height.value() == 10

        obj = Object(c, height=10)
        obj.height = 20
        obj.prepare(mock_renderer)
        assert obj.height.value() == 20

    def test_latest(self, c) -> None:
        """
        Test that latest() returns the latest object
        """
        parent = Object(c)

        assert parent.latest() == parent
        assert parent.latest() is parent

        cloned1 = parent.clone()

        assert parent.latest() == cloned1
        assert cloned1.latest() == cloned1

        assert parent.latest() is cloned1
        assert cloned1.latest() is cloned1

        cloned2 = parent.clone()

        assert parent.latest() == cloned2
        assert cloned1.latest() == cloned2
        assert cloned2.latest() == cloned2

        assert parent.latest() is cloned2
        assert cloned2.latest() is cloned2

        # TODO: Is this what we want?
        assert cloned1.latest() is not cloned2

    def test_clone(self, c) -> None:
        """
        Test that cloning an object replicates all attributes
        """
        parent = Object(c, width=10, height=20, style=Style(fill_color=RED, padding=5))

        cloned = parent.clone()

        assert cloned.width is not parent.width
        # assert cloned.width._var is parent.width._var
        # assert cloned.width.value() == 10
        # assert cloned.height.value() == 20
        assert cloned.style.fill_color == RED
        assert cloned.style.padding == 5

        assert parent.width is not cloned.width
        assert parent.height is not cloned.height
        assert parent.height is not cloned.height

        assert parent.canvas == cloned.canvas
        assert parent.canvas is not cloned.canvas
        assert parent.canvas.latest() is cloned.canvas

    def test_clone_unique(self, c) -> None:
        """
        Test that uniquely cloning an object creates a new object not equal to the
        original, but still correctly copies the attributes
        """
        parent = Object(c, width=10, height=20, style=Style(fill_color=RED, padding=5))

        assert parent.latest() == parent
        assert parent.latest() is parent

        cloned = parent.clone(unique=True)

        # assert cloned.width.value() == 10
        # assert cloned.height.value() == 20
        assert cloned.style.fill_color == RED
        assert cloned.style.padding == 5

        assert parent.canvas == cloned.canvas
        assert parent.canvas is not cloned.canvas
        assert parent.canvas.latest() is cloned.canvas

        assert parent.latest() != cloned
        assert parent.latest() == parent
        assert parent.latest() is parent
        assert parent != cloned
        assert parent is not cloned

        assert cloned.latest() == cloned
        assert cloned.latest() is cloned


class TestTextBoxDynamicSize:
    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, c) -> None:
        r = c.textbox(text="A", font_size=4)
        c.add(r)

    def test_correct_image(self, c_im, dim) -> None:
        assert c_im.size == dim
        assert convert_to_ascii(c_im) == [
            "wwwww",
            "wbbbw",
            "wb?bw",
            "wb?b?",
            "wbbb?",
        ]


class TestLineRelative:
    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, c) -> None:
        r = Line(canvas=c, start=P(0, 1), end=P(2, 1))
        c.add(r)

    def test_correct_image(self, c_im, dim) -> None:
        assert c_im.size == dim
        assert convert_to_ascii(c_im) == [
            "wwwww",
            "wbbbw",
            "wbbbw",
            "wbbbw",
            "wwwww",
        ]


@pytest.mark.xfail
class TestDottedLine:
    def test_correct_image(self, c_im, dim) -> None:
        assert False


@pytest.mark.xfail
class TestArrow:
    def test_correct_image(self, c_im, dim) -> None:
        assert False


@pytest.mark.xfail
class TestGrid:
    def test_correct_image(self, c_im, dim) -> None:
        assert False


@pytest.mark.xfail
class TestSpacer:
    def test_correct_image(self, c_im, dim) -> None:
        assert False


class TestConstraints:
    @pytest.mark.xfail
    def test_unsatisfiable(self, c) -> None:
        """
        Test that unsatisfiable constraints raise an error
        """
        vlayout = VLayout(canvas=c, width=10)
        obj = Object(c, width=20)

        with pytest.raises(UnsatisfiableConstraint):
            vlayout.add(obj)


class TestRectangle2x2:
    @pytest.fixture(scope="class")
    def dim(self) -> tuple[int, int]:
        return 4, 4

    # TODO: Is it guaranteed that clean_dir will be called first?
    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, c) -> None:
        r = c.rectangle(width=2, height=2, fill_color=RED)
        c.add(r)

    def test_correct_image(self, c_im, dim) -> None:
        assert c_im.size == dim
        assert convert_to_ascii(c_im) == [
            "wwww",
            "wbbw",
            "wbbw",
            "wwww",
        ]


class TestRectangle3x3:
    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, c) -> None:
        r = c.rectangle(width=3, height=3, fill_color=RED)
        c.add(r)

    def test_correct_image(self, c_im, dim) -> None:
        assert c_im.size == dim
        assert convert_to_ascii(c_im) == [
            "wwwww",
            "wbbbw",
            "wbRbw",
            "wbbbw",
            "wwwww",
        ]


class TestRectangleConstraint:
    @pytest.fixture(scope="class")
    def dim(self) -> tuple[int, int]:
        return 5, 6

    @pytest.fixture(scope="class", autouse=True)
    def setup_scene(self, c) -> None:
        r1 = c.rectangle(width=2, height=2)
        r2 = c.rectangle(width=2, height=2)
        c.add(r1)
        c.add(r2, P(0, r1.height + 1))

    def test_correct_image(self, c_im, dim) -> None:
        assert c_im.size == dim
        assert convert_to_ascii(c_im) == [
            "wwwww",
            "wbbww",
            "wbbww",
            "wwwww",
            "wbbww",
            "wbbww",
        ]


class TestLayout:
    def test_vlayout_dimensions(self, c, mock_renderer) -> None:
        """
        Test that VLayout dimensions are properly calculated
        """
        parent = c.vlayout()

        child1 = Object(canvas=c, width=20, height=10)
        child2 = Object(canvas=c, width=40, height=30)

        parent.add(child1)
        parent.add(child2, P(5, 15))

        parent.prepare(mock_renderer)

        assert parent.width.value() == 45
        assert parent.height.value() == 55

    def test_hlayout_dimensions(self, c, mock_renderer) -> None:
        """
        Test that HLayout dimensions are properly calculated
        """
        parent = c.hlayout()

        child1 = Object(canvas=c, width=20, height=10)
        child2 = Object(canvas=c, width=40, height=30)

        parent.add(child1)
        parent.add(child2, P(5, 15))

        parent.prepare(mock_renderer)

        assert parent.width.value() == 65
        assert parent.height.value() == 45


class TestLayoutPrepare:
    def test_vlayout_prepare(self, c, mock_renderer) -> None:
        """
        Test that VLayout renders children in the correct position
        """
        parent = c.vlayout(width=50)

        child1 = Object(canvas=c, width=20, height=10)
        child2 = Object(canvas=c, width=40, height=30)

        parent.add(child1)
        parent.add(child2)

        parent.prepare(mock_renderer)

        assert parent.width.value() == 50
        assert parent.height.value() == 40

        assert child1.pos == P(15, 0)
        assert child2.pos == P(5, 10)

    def test_nested_vlayout_prepare(self, c, mock_renderer) -> None:
        """
        Test that nested VLayout renders children in the correct position
        """
        parent = c.vlayout(width=50)

        nested = c.vlayout()

        child1 = Object(canvas=c, width=20, height=10)
        child2 = Object(canvas=c, width=40, height=30)

        nested.add(child1)
        nested.add(child2)

        child3 = Object(canvas=c, width=25, height=15)
        parent.add(nested)
        parent.add(child3)

        parent.prepare(mock_renderer)

        assert parent.width.value() == 50
        assert parent.height.value() == 55

        assert nested.width.value() == 40
        assert nested.height.value() == 40
        assert nested.pos == P(5, 0)

        assert child1.pos == P(15, 0)
        assert child2.pos == P(5, 10)
        assert child3.pos == P(12, 40)

    def test_hlayout_prepare(self, c, mock_renderer) -> None:
        """
        Test that HLayout renders children in the correct position
        """
        parent = c.hlayout()

        child1 = Object(canvas=c, width=20, height=10)
        child2 = Object(canvas=c, width=40, height=30)

        parent.add(child1)
        parent.add(child2, P(5, 15))

        parent.prepare(mock_renderer)

        assert child1.pos == P(0, 17)
        assert child2.pos == P(25, 22)
