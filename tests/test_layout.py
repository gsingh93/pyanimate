from pyanimate.layout import HLayout, Object, VLayout
from pyanimate.renderer import Renderer
from pyanimate.shape import RED
from pyanimate.shape import Point as P
from pyanimate.style import Style


class MockRenderer(Renderer):
    def rectangle(self, p1, p2, style: Style):
        raise NotImplementedError()

    def text(self, text: str, p, style: Style):
        raise NotImplementedError()

    def text_bbox(self, text: str, style: Style) -> tuple[int, int, int, int]:
        raise NotImplementedError()

    def line(self, p1, p2, style: Style):
        raise NotImplementedError()

    def set_dimensions(self, dim):
        raise NotImplementedError()


class TestObject:
    def test_add(self) -> None:
        """
        Test that a child object is properly added to the parent object
        """
        parent = Object()
        child = Object()

        parent.add(child)

        assert child in parent.children
        assert child.parent == parent
        assert child.style._parent_obj_style == parent.style

    def test_clone(self) -> None:
        """
        Test that cloning an object replicates all attributes
        """
        parent = Object(width=10, height=20, style=Style(fill_color=RED, padding=5))

        cloned = parent.clone()

        assert cloned.width == 10
        assert cloned.height == 20
        assert cloned.style.fill_color == RED
        assert cloned.style.padding == 5


class TestLayout:
    def test_vlayout_dimensions(self) -> None:
        """
        Test that VLayout dimensions are properly calculated
        """
        parent = VLayout()

        child1 = Object(width=20, height=10)
        child2 = Object(width=40, height=30)

        parent.add(child1)
        parent.add(child2, P(5, 15))

        assert parent.width == 45
        assert parent.height == 55

    def test_hlayout_dimensions(self) -> None:
        """
        Test that HLayout dimensions are properly calculated
        """
        parent = HLayout()

        child1 = Object(width=20, height=10)
        child2 = Object(width=40, height=30)

        parent.add(child1)
        parent.add(child2, P(5, 15))

        assert parent.width == 65
        assert parent.height == 45
