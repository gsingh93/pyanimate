import copy

from pyanimate.solver import Solver, Variable


class TestSolver:
    def test_clone(self) -> None:
        s1 = Solver()
        x = Variable("x")
        y = Variable("y")

        s1.add(x == y)
        s2 = copy.deepcopy(s1)

        assert len(s1._constraints) == len(s2._constraints) == 1
        for c in s1._constraints:
            assert c not in s2._constraints

    # def test_clone_canvas(self) -> None:
    #     c1 = Canvas()
    #     for c in [c1._w, c1._h, c1._x, c1._y]:
    #         assert c in c1.solver.variables()

    #     c2 = c1.clone()

    #     for c in [c1._w, c1._h, c1._x, c1._y]:
    #         assert c in c1.solver.variables()

    #     for c in [c2._w, c2._h, c2._x, c2._y]:
    #         assert c in c2.solver.variables()

    #     assert len(c1.solver._constraints) == len(c2.solver._constraints) == 4
    #     for c in c1.solver._constraints:
    #         assert c not in c2.solver._constraints
