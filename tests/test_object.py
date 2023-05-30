import pytest

from pyanimate.layout import Object
from pyanimate.shape import RED
from pyanimate.shape import Point as P
from pyanimate.style import Style


class TestObject:
    def test_width(self, c, mock_renderer) -> None:
        """
        Test that width is properly set
        """
        obj = Object(c, width=10)
        obj.prepare(mock_renderer)
        assert obj.width.value() == 10

        obj = Object(c, width=10)
        obj.width = 20
        obj.prepare(mock_renderer)
        assert obj.width.value() == 20

    @pytest.mark.xfail
    def test_width_constraint(self, _c, _mock_renderer):
        assert False

    def test_height(self, c, mock_renderer) -> None:
        """
        Test that height is properly set
        """
        obj = Object(c, height=10)
        obj.prepare(mock_renderer)
        assert obj.height.value() == 10

        obj = Object(c, height=10)
        obj.height = 20
        obj.prepare(mock_renderer)
        assert obj.height.value() == 20

    @pytest.mark.xfail
    def test_height_constraint(self, _c, _mock_renderer):
        assert False


class TestParentChildObject:
    @pytest.fixture
    def child(self, c) -> Object:
        return Object(c)

    @pytest.fixture
    def parent(self, c, child, mock_renderer) -> Object:
        parent = Object(c)

        parent.add(child)

        # Initialize the Solver
        c.prepare(mock_renderer)

        parent.prepare(mock_renderer)

        return parent

    def test_add(self, parent, child) -> None:
        """
        Test that a child object is properly added to the parent object
        """
        assert child in parent.children
        assert parent.children[child] == P(0, 0)
        assert child.parent == parent
        assert child.style.parent_obj_style == parent.style
        assert child.pos == P(0, 0)

    def test_add_twice(self, parent, child) -> None:
        """
        Test that adding a child object twice raises an error
        """
        with pytest.raises(AssertionError):
            parent.add(child)

    def test_remove(self, parent, child, mock_renderer) -> None:
        assert child in parent.children
        assert parent.children[child] == P(0, 0)
        assert child.parent == parent
        assert child.pos == P(0, 0)

        parent.remove(child)

        # Reinitialize the Solver
        parent.canvas.prepare(mock_renderer)

        assert child not in parent.children
        assert child.parent is None

        parent.add(child, P(10, 20))

        parent.prepare(mock_renderer)

        assert child in parent.children
        assert parent.children[child] == P(10, 20)
        assert child.parent == parent
        assert child.pos == P(10, 20)

    def test_remove_twice(self, parent, child) -> None:
        """
        Test that removing a child object twice raises an error
        """
        parent.remove(child)

        with pytest.raises(ValueError):
            parent.remove(child)


class TestLatestObject:
    @pytest.fixture
    def parent(self, c) -> Object:
        return Object(c)

    @pytest.fixture
    def cloned(self, parent) -> Object:
        return parent.clone()

    @pytest.mark.dependency(name="latest_is_self")
    def test_latest_is_self(self, parent) -> None:
        """
        Test that latest() returns self before any clones
        """
        assert parent.latest() == parent
        assert parent.latest() is parent

    @pytest.mark.dependency(name="latest", depends=["latest_is_self"])
    def test_latest(self, parent, cloned) -> None:
        """
        Test that latest() returns the latest object
        """
        cloned1 = cloned

        assert parent.latest() == cloned1
        assert cloned1.latest() == cloned1

        assert parent.latest() is cloned1
        assert cloned1.latest() is cloned1

        cloned2 = cloned1.clone()

        assert parent.latest() == cloned2
        assert cloned1.latest() == cloned2
        assert cloned2.latest() == cloned2

        assert parent.latest() is cloned2
        assert cloned1.latest() is cloned2
        assert cloned2.latest() is cloned2

    @pytest.mark.dependency(depends=["latest"])
    def test_diverging_clone(self, parent, cloned) -> None:
        cloned1 = cloned
        cloned2 = parent.clone()

        assert parent.latest() == cloned2
        assert cloned1.latest() == cloned2
        assert cloned2.latest() == cloned2

        assert parent.latest() is cloned2
        assert cloned2.latest() is cloned2

        # TODO: Is this what we want?
        assert cloned1.latest() is not cloned2


class TestCloneObject:
    def test_clone(self, c, mock_renderer) -> None:
        """
        Test that cloning an object replicates all attributes
        """
        parent = Object(c, width=10, height=20, style=Style(fill_color=RED, padding=5))

        cloned = parent.clone()

        cloned.prepare(mock_renderer)
        parent.prepare(mock_renderer)

        assert cloned.width is not parent.width
        assert cloned.width.value() == 10
        assert cloned.height.value() == 20
        assert cloned.style.fill_color == RED
        assert cloned.style.padding == 5

        assert parent.width is not cloned.width
        assert parent.height is not cloned.height
        assert parent.height is not cloned.height

        assert parent.canvas == cloned.canvas
        assert parent.canvas is not cloned.canvas
        assert parent.canvas.latest() is cloned.canvas

    def test_clone_unique(self, c, mock_renderer) -> None:
        """
        Test that uniquely cloning an object creates a new object not equal to the
        original, but still correctly copies the attributes
        """
        parent = Object(c, width=10, height=20, style=Style(fill_color=RED, padding=5))

        assert parent.latest() == parent
        assert parent.latest() is parent

        cloned = parent.clone(unique=True)

        cloned.prepare(mock_renderer)
        parent.prepare(mock_renderer)

        assert cloned.width.value() == 10
        assert cloned.height.value() == 20
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
