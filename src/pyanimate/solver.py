from typing import Optional

import kiwisolver
from kiwisolver import Constraint, Expression, Term, UnsatisfiableConstraint, Variable


def copy_constraint(v: Variable, c: Constraint) -> tuple[Variable, Constraint]:
    e = c.expression()
    terms = []

    new_var = Variable()
    for term in e.terms():
        if term.variable() is v:
            terms.append(Term(new_var, term.coefficient()))
        else:
            terms.append(Term(term.variable(), term.coefficient()))

    return new_var, Constraint(Expression(terms, e.constant()), c.op(), c.strength())


class Solver:
    def __init__(self):
        self._solver = kiwisolver.Solver()
        self._constraints = set()

    def _find(self, v: str) -> tuple[Optional[Variable], set[Constraint]]:
        res = set()
        res_strs = set()
        var = None
        for c in self._constraints:
            for term in c.expression().terms():
                if term.variable().name() == v:
                    var = term.variable()

                    # Skip duplicate constraints
                    if str(c) in res_strs:
                        continue

                    res_strs.add(str(c))
                    res.add(c)

        return var, res

    def add(self, c: Constraint) -> None:
        self._constraints.add(c)
        self._solver.addConstraint(c)

    def remove(self, c: Constraint) -> None:
        self._constraints.remove(c)
        self._solver.removeConstraint(c)

    def hasConstraint(self, c: Constraint) -> bool:
        return self._solver.hasConstraint(c)

    def update(self) -> None:
        self._solver.updateVariables()

    def analyze(
        self, e: UnsatisfiableConstraint
    ) -> list[tuple[Variable, set[Constraint]]]:
        variables = []

        msg = str(e)
        constraint, _ = msg.split(" | ")
        op = None
        for _op in [" <= ", " >= ", " == "]:
            if _op in constraint:
                op = _op
                break

        assert op is not None

        expr, constant = constraint.split(op)
        assert constant == "0"
        terms = expr.split(" + ")
        for term in terms:
            res = term.split(" * ")
            if len(res) == 2:
                _, var = res
                variables.append(self._find(var))

        return variables
