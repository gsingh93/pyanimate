from __future__ import annotations

from copy import deepcopy
from typing import Literal, Optional

import kiwisolver as kiwi
from kiwisolver import UnsatisfiableConstraint

from . import get_logger

# def copy_expression(
#     v: kiwi.Variable, e: kiwi.Expression
# ) -> tuple[kiwi.Variable, kiwi.Expression]:
#     terms = []

#     new_var = kiwi.Variable()
#     for term in e.terms():
#         if term.variable() is v:
#             terms.append(Term(new_var, term.coefficient()))
#         else:
#             terms.append(Term(term.variable(), term.coefficient()))

#     return new_var, kiwi.Expression(terms, e.constant())


# def copy_constraint(
#     v: kiwi.Variable, c: kiwi.Constraint
# ) -> tuple[kiwi.Variable, kiwi.Constraint]:
#     e = c.expression()
#     new_var, new_e = copy_expression(v, e)

#     return new_var, kiwi.Constraint(new_e, c.op(), c.strength())

logger = get_logger(__name__)


class Variable:
    def __init__(self, name: Optional[str] = None):
        self._name = name
        if name:
            self._var = kiwi.Variable(name)
        else:
            self._var = kiwi.Variable()
        # logger.warning(
        #     f"Made variable {self._var} [{hex(id(self._var))}]", stack_info=True
        # )

    @staticmethod
    def from_variable(variable: kiwi.Variable) -> Variable:
        v = Variable.__new__(Variable)
        v._name = variable.name()
        v._var = variable
        return v

    def value(self) -> float:
        return self._var.value()

    def __eq__(self, other: int | float | Variable | Expression) -> Constraint:
        if isinstance(other, (int, float)):
            c = self._var == other
        elif isinstance(other, Variable):
            c = self._var == other._var
        elif isinstance(other, Expression):
            c = self._var == other._expr

        return Constraint.from_constraint(c)

    def __hash__(self) -> int:
        return id(self._var)

    def __le__(self, other: int | float | Variable | Expression) -> Constraint:
        if isinstance(other, (int, float)):
            c = self._var <= other
        elif isinstance(other, Variable):
            c = self._var <= other._var
        elif isinstance(other, Expression):
            c = self._var <= other._expr

        return Constraint.from_constraint(c)

    def __ge__(self, other: int | float | Variable | Expression) -> Constraint:
        if isinstance(other, (int, float)):
            c = self._var >= other
        elif isinstance(other, Variable):
            c = self._var >= other._var
        elif isinstance(other, Expression):
            c = self._var >= other._expr

        return Constraint.from_constraint(c)

    def __add__(self, other: int | float | Variable | Term | Expression) -> Expression:
        if isinstance(other, (int, float)):
            e = self._var + other
        elif isinstance(other, Variable):
            e = self._var + other._var
        elif isinstance(other, Term):
            e = self._var + other._term
        elif isinstance(other, Expression):
            e = self._var + other._expr
        else:
            raise TypeError(f"unsupported operand type(s) for -: {type(other)}")

        return Expression.from_expression(e)

    def __radd__(self, other: int | float | Variable | Term | Expression) -> Expression:
        return self + other

    def __sub__(self, other: int | float | Variable | Term | Expression) -> Expression:
        if isinstance(other, (int, float)):
            e = self._var - other
        elif isinstance(other, Variable):
            e = self._var - other._var
        elif isinstance(other, Term):
            e = self._var - other._term
        elif isinstance(other, Expression):
            e = self._var - other._expr
        else:
            raise TypeError(f"unsupported operand type(s) for -: {type(other)}")

        return Expression.from_expression(e)

    def __rsub__(self, other: int | float | Variable | Term | Expression) -> Expression:
        if isinstance(other, (int, float)):
            e = other - self._var
        elif isinstance(other, Variable):
            e = other._var - self._var
        elif isinstance(other, Term):
            e = other._term - self._var
        elif isinstance(other, Expression):
            e = other._expr - self._var
        else:
            raise TypeError(f"unsupported operand type(s) for -: {type(other)}")

        return Expression.from_expression(e)

    def __mul__(self, other: int) -> Term:
        term = self._var * other
        return Term.from_term(term)

    def __truediv__(self, other: int) -> Term:
        term = self._var / other
        return Term.from_term(term)

    def __deepcopy__(self, memo) -> Variable:
        id_ = id(self._var)
        if id_ in memo:
            return memo[id_]
        v = Variable(self._name)
        memo[id_] = v
        return v

    def __str__(self) -> str:
        return f"{self._var} [{hex(id(self._var))}]"


class Term:
    def __init__(self, variable: Variable, coefficient: float):
        self._var = variable
        self._coefficient = coefficient
        self._term = variable._var * coefficient

    @staticmethod
    def from_term(term: kiwi.Term) -> Term:
        return Term(Variable.from_variable(term.variable()), term.coefficient())

    def value(self) -> float:
        return self._term.value()

    def __eq__(self, other: int | float | Variable | Expression) -> Constraint:
        if isinstance(other, (int, float)):
            c = self._term == other
        elif isinstance(other, Variable):
            c = self._term == other._var
        elif isinstance(other, Expression):
            c = self._term == other._expr

        return Constraint.from_constraint(c)

    def __le__(self, other: int | float | Variable | Expression) -> Constraint:
        if isinstance(other, (int, float)):
            c = self._term <= other
        elif isinstance(other, Variable):
            c = self._term <= other._var
        elif isinstance(other, Expression):
            c = self._term <= other._expr

        return Constraint.from_constraint(c)

    def __ge__(self, other: int | float | Variable | Expression) -> Constraint:
        if isinstance(other, (int, float)):
            c = self._term >= other
        elif isinstance(other, Variable):
            c = self._term >= other._var
        elif isinstance(other, Expression):
            c = self._term >= other._expr

        return Constraint.from_constraint(c)

    def __add__(self, other: int | float | Variable | Term | Expression) -> Expression:
        if isinstance(other, (int, float)):
            e = self._term + other
        elif isinstance(other, Variable):
            e = self._term + other._var
        elif isinstance(other, Term):
            e = self._term + other._term
        elif isinstance(other, Expression):
            e = self._term + other._expr
        else:
            raise TypeError(f"unsupported operand type(s) for -: {type(other)}")

        return Expression.from_expression(e)

    def __radd__(self, other: int | float | Variable | Term | Expression) -> Expression:
        return self + other

    def __sub__(self, other: int | float | Variable | Term | Expression) -> Expression:
        if isinstance(other, (int, float)):
            e = self._term - other
        elif isinstance(other, Variable):
            e = self._term - other._var
        elif isinstance(other, Term):
            e = self._term - other._term
        elif isinstance(other, Expression):
            e = self._term - other._expr
        else:
            raise TypeError(f"unsupported operand type(s) for -: {type(other)}")

        return Expression.from_expression(e)

    def __rsub__(self, other: int | float | Variable | Term | Expression) -> Expression:
        if isinstance(other, (int, float)):
            e = other - self._term
        elif isinstance(other, Variable):
            e = other._var - self._term
        elif isinstance(other, Term):
            e = other._term - self._term
        elif isinstance(other, Expression):
            e = other._expr - self._term
        else:
            raise TypeError(f"unsupported operand type(s) for -: {type(other)}")

        return Expression.from_expression(e)

    def __mul__(self, other: int) -> Term:
        term = self._term * other
        return Term.from_term(term)

    def __truediv__(self, other: int) -> Term:
        term = self._term / other
        return Term.from_term(term)

    def __deepcopy__(self, memo) -> Term:
        id_ = id(self._term)
        if id_ in memo:
            return memo[id_]
        t = Term(deepcopy(self._var, memo), self._coefficient)
        memo[id_] = t
        return t

    def __str__(self) -> str:
        return f"{self._term} [{hex(id(self._term))}]"


class Expression:
    def __init__(self, terms: tuple[Term], constant: float):
        self._terms = terms
        self._constant = constant
        self._expr = kiwi.Expression(tuple(t._term for t in terms), constant)

    def value(self) -> float:
        return self._expr.value()

    @staticmethod
    def from_expression(e: kiwi.Expression) -> Expression:
        return Expression(tuple(Term.from_term(t) for t in e.terms()), e.constant())

    def variables(self) -> list[Variable]:
        variables = []
        for t in self._terms:
            variables.append(t._var)

        return variables

    def __eq__(self, other: int | float | Variable | Expression) -> Constraint:
        if isinstance(other, (int, float)):
            c = self._expr == other
        elif isinstance(other, Variable):
            c = self._expr == other._var
        elif isinstance(other, Expression):
            c = self._expr == other._expr

        return Constraint.from_constraint(c)

    def __le__(self, other: int | float | Variable | Expression) -> Constraint:
        if isinstance(other, (int, float)):
            c = self._expr <= other
        elif isinstance(other, Variable):
            c = self._expr <= other._var
        elif isinstance(other, Expression):
            c = self._expr <= other._expr

        return Constraint.from_constraint(c)

    def __ge__(self, other: int | float | Variable | Expression) -> Constraint:
        if isinstance(other, (int, float)):
            c = self._expr >= other
        elif isinstance(other, Variable):
            c = self._expr >= other._var
        elif isinstance(other, Expression):
            c = self._expr >= other._expr

        return Constraint.from_constraint(c)

    def __add__(self, other: int | float | Variable | Term | Expression) -> Expression:
        if isinstance(other, (int, float)):
            e = self._expr + other
        elif isinstance(other, Variable):
            e = self._expr + other._var
        elif isinstance(other, Term):
            e = self._expr + other._term
        elif isinstance(other, Expression):
            e = self._expr + other._expr
        else:
            raise TypeError(f"unsupported operand type(s) for -: {type(other)}")

        return Expression.from_expression(e)

    def __radd__(self, other: int | float | Variable | Term | Expression) -> Expression:
        return self + other

    def __sub__(self, other: int | float | Variable | Term | Expression) -> Expression:
        if isinstance(other, (int, float)):
            e = self._expr - other
        elif isinstance(other, Variable):
            e = self._expr - other._var
        elif isinstance(other, Term):
            e = self._expr - other._term
        elif isinstance(other, Expression):
            e = self._expr - other._expr
        else:
            raise TypeError(f"unsupported operand type(s) for -: {type(other)}")

        return Expression.from_expression(e)

    def __rsub__(self, other: int | float | Variable | Term | Expression) -> Expression:
        if isinstance(other, (int, float)):
            e = other - self._expr
        elif isinstance(other, Variable):
            e = other._var - self._expr
        elif isinstance(other, Term):
            e = other._term - self._expr
        elif isinstance(other, Expression):
            e = other._expr - self._expr
        else:
            raise TypeError(f"unsupported operand type(s) for -: {type(other)}")

        return Expression.from_expression(e)

    def __mul__(self, other: int) -> Expression:
        e = self._expr * other
        return Expression.from_expression(e)

    def __truediv__(self, other: int) -> Expression:
        e = self._expr / other
        return Expression.from_expression(e)

    def __deepcopy__(self, memo):
        id_ = id(self._expr)
        if id_ in memo:
            return memo[id_]
        e = Expression(deepcopy(self._terms, memo), self._constant)
        memo[id_] = e
        return e

    def __str__(self) -> str:
        return f"{self._expr} [{hex(id(self._expr))}]"


class Constraint:
    def __init__(self, e: Expression, op: Literal["==", "<=", ">="], strength: float):
        self._expr = e
        self._constraint = kiwi.Constraint(e._expr, op, strength)

    @staticmethod
    def from_constraint(c: kiwi.Constraint) -> Constraint:
        e = Expression.from_expression(c.expression())
        return Constraint(e, c.op(), c.strength())

    # def __eq__(self, other: Constraint) -> bool:
    #     return self._constraint == other._constraint

    # def __hash__(self) -> int:
    #     return hash(self._constraint)

    def __deepcopy__(self, memo) -> Constraint:
        id_ = id(self._constraint)
        if id_ in memo:
            return memo[id_]
        expr = deepcopy(self._expr, memo)
        c = Constraint(
            expr,
            self._constraint.op(),
            self._constraint.strength(),
        )
        memo[id_] = c
        return c

    def __str__(self) -> str:
        return f"{self._constraint} [{hex(id(self._constraint))}]"


class Solver:
    def __init__(self):
        self._solver = kiwi.Solver()
        self._constraints = set()

    def _find(self, v: str) -> tuple[Optional[Variable], set[Constraint]]:
        res = set()
        res_strs = set()
        var = None
        for c in self._constraints:
            for term in c._expr._terms:
                if term._var._name == v:
                    var = term._var

                    # Skip duplicate constraints
                    if str(c) in res_strs:
                        continue

                    res_strs.add(str(c))
                    res.add(c)

        return var, res

    def add(self, c: Constraint) -> None:
        self._constraints.add(c)
        self._solver.addConstraint(c._constraint)

    def remove(self, c: Constraint) -> None:
        self._constraints.remove(c)
        self._solver.removeConstraint(c._constraint)

    def hasConstraint(self, c: Constraint) -> bool:
        return self._solver.hasConstraint(c._constraint)

    def update(self) -> None:
        self._solver.updateVariables()

    def dumps(self) -> str:
        res = "\n".join(map(str, self.variables()))

        for c in self._constraints:
            res += f"{c}\n"

        return res

    def variables(self) -> list[Variable]:
        res = []
        for c in self._constraints:
            for t in c._expr._terms:
                res.append(t._var)

        return res

    def analyze(
        self, e: UnsatisfiableConstraint
    ) -> list[tuple[Variable, set[Constraint]]]:
        variables = []

        constraint = e.args[0]

        for term in constraint.expression().terms():
            var = term.variable().name()
            variables.append(self._find(var))

        return variables

    def __deepcopy__(self, memo):
        constraints = deepcopy(self._constraints, memo)
        solver = Solver()
        for c in constraints:
            solver.add(c)

        return solver
