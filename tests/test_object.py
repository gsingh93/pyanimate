import pytest
from kiwisolver import UnsatisfiableConstraint

from pyanimate.layout import Object, VLayout
from pyanimate.shape import RED
from pyanimate.shape import Point as P
from pyanimate.style import Style


class TestObject:
    def test_add(self, c, mock_renderer) -> None:
        """
        Test that a child object is properly added to the parent object
        """
        parent = Object(c)
        child = Object(c)
        parent.add(child)

        parent.prepare(mock_renderer)

        assert child in parent.children
        assert parent.children[child] == P(0, 0)
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

    def test_remove(self, c, mock_renderer) -> None:
        parent = Object(c)
        child = Object(c)
        parent.add(child)

        parent.prepare(mock_renderer)

        assert child in parent.children
        assert parent.children[child] == P(0, 0)
        assert child.parent == parent
        assert child.pos == P(0, 0)

        parent.remove(child)

        assert child not in c.children
        assert child.parent is None

        parent.add(child, P(10, 20))

        parent.prepare(mock_renderer)

        assert child in parent.children
        assert parent.children[child] == P(10, 20)
        assert child.parent == parent
        assert child.pos == P(10, 20)

    @pytest.mark.xfail
    def test_replace(self, c) -> None:
        assert False

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
