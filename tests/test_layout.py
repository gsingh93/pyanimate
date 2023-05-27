import pytest
from kiwisolver import UnsatisfiableConstraint

from pyanimate.layout import Object, VLayout
from pyanimate.shape import Point as P


class TestVLayout:
    @pytest.fixture(scope="class")
    def children(self, c) -> tuple[Object, Object]:
        child1 = Object(canvas=c, width=20, height=10)
        child2 = Object(canvas=c, width=40, height=30)

        return child1, child2

    @pytest.fixture(scope="class")
    def parent(self, c, children, mock_renderer) -> VLayout:
        parent = c.vlayout()

        child1, child2 = children

        parent.add(child1)
        parent.add(child2, P(5, 15))

        parent.prepare(mock_renderer)

        return parent

    @pytest.mark.dependency(name="dimensions")
    def test_dimensions(self, parent) -> None:
        """
        Test that VLayout dimensions are properly calculated
        """
        # Max child width is 40, but it's offset by 5 so the parent width is 45
        assert parent.width.value() == 45

        # Child heights are 10 and 30, but the second child is offset by 15 so the
        # parent height is 55
        assert parent.height.value() == 55

    @pytest.mark.dependency(name="children_position", depends=["dimensions"])
    def test_children_position(self, parent, children) -> None:
        """
        Test that VLayout children positions are properly calculated
        """
        child1, child2 = children
        center = int(parent.width.value() / 2)

        assert child1.pos == P(center - 10, 0)

        # `child2` would normally start 20 to the left of center, but it's offset by 5
        # And it starts 15 below `child1`, which has a height of 10, so y is 25
        assert child2.pos == P(center - 20 + 5, 25)


class TestHLayout:
    @pytest.fixture(scope="class")
    def children(self, c) -> tuple[Object, Object]:
        child1 = Object(canvas=c, width=20, height=10)
        child2 = Object(canvas=c, width=40, height=30)

        return child1, child2

    @pytest.fixture(scope="class")
    def parent(self, c, children, mock_renderer) -> VLayout:
        parent = c.hlayout()

        child1, child2 = children

        parent.add(child1)
        parent.add(child2, P(5, 15))

        parent.prepare(mock_renderer)

        return parent

    def test_dimensions(self, parent) -> None:
        """
        Test that HLayout dimensions are properly calculated
        """
        # Child widths are 20 and 40, but the second child is offset by 5 so the parent
        # width is 65
        assert parent.width.value() == 65

        # Max child height is 30, but it's offset by 15 so the parent height is 45
        assert parent.height.value() == 45

    def test_children_position(self, parent, children) -> None:
        """
        Test that HLayout children positions are properly calculated
        """
        child1, child2 = children
        center = int(parent.height.value() / 2)

        assert child1.pos == P(0, center - 5)

        # `child2` starts 5 to the right of `child1`, which has a width of 20, so x is
        # 25. And it would normally start 15 above center, but it's offset by 15
        assert child2.pos == P(25, center - 15 + 15)


class TestNestedVLayout:
    def test_nested_vlayout(self, c, mock_renderer) -> None:
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


class TestUnsatisfiableConstraint:
    def test_vlayout_unsatisfiable(self, c, mock_renderer) -> None:
        """
        Test that unsatisfiable constraints raise an error
        """
        vlayout = c.vlayout(width=10)
        obj = Object(c, width=20)
        vlayout.add(obj)

        with pytest.raises(UnsatisfiableConstraint):
            vlayout.prepare(mock_renderer)

    def test_hlayout_unsatisfiable(self, c, mock_renderer) -> None:
        """
        Test that unsatisfiable constraints raise an error
        """
        hlayout = c.hlayout(height=10)
        obj = Object(c, height=20)
        hlayout.add(obj)

        with pytest.raises(UnsatisfiableConstraint):
            hlayout.prepare(mock_renderer)
