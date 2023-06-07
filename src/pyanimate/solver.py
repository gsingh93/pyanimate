from __future__ import annotations

from copy import deepcopy
from typing import Literal, TypeAlias, Union

import kiwisolver as kiwi
from kiwisolver import UnsatisfiableConstraint

from . import get_logger

logger = get_logger(__name__)


SolverType: TypeAlias = Union[int, float, "Variable", "Term", "Expression"]


class Variable:
    def __init__(self, name: str = ""):
        self._name = name
        self._var = kiwi.Variable(name)

    @staticmethod
    def from_variable(variable: kiwi.Variable) -> Variable:
        v = Variable.__new__(Variable)
        v._name = variable.name()
        v._var = variable
        return v

    def name(self) -> str:
        return self._name

    def value(self) -> float:
        return self._var.value()

    def __neg__(self) -> Term:
        term = -self._var
        return Term.from_term(term)

    def __eq__(self, other: SolverType) -> Constraint:
        if isinstance(other, (int, float)):
            c = self._var == other
        elif isinstance(other, Variable):
            c = self._var == other._var
        elif isinstance(other, Term):
            c = self._var == other._term
        elif isinstance(other, Expression):
            c = self._var == other._expr

        return Constraint.from_constraint(c)

    def __hash__(self) -> int:
        return id(self._var)

    def __le__(self, other: SolverType) -> Constraint:
        if isinstance(other, (int, float)):
            c = self._var <= other
        elif isinstance(other, Variable):
            c = self._var <= other._var
        elif isinstance(other, Term):
            c = self._var <= other._term
        elif isinstance(other, Expression):
            c = self._var <= other._expr

        return Constraint.from_constraint(c)

    def __ge__(self, other: SolverType) -> Constraint:
        if isinstance(other, (int, float)):
            c = self._var >= other
        elif isinstance(other, Variable):
            c = self._var >= other._var
        elif isinstance(other, Term):
            c = self._var >= other._term
        elif isinstance(other, Expression):
            c = self._var >= other._expr

        return Constraint.from_constraint(c)

    def __add__(self, other: SolverType) -> Expression:
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

    def __radd__(self, other: SolverType) -> Expression:
        return self + other

    def __sub__(self, other: SolverType) -> Expression:
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

    def __rsub__(self, other: SolverType) -> Expression:
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

    def __mul__(self, other: int | float) -> Term:
        term = self._var * other
        return Term.from_term(term)

    def __rmul__(self, other: int | float) -> Term:
        return self * other

    def __truediv__(self, other: int | float) -> Term:
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
        return f"{self._var}"

    def __repr__(self) -> str:
        return f"{self} [{hex(id(self._var))}]"


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

    def __neg__(self) -> Term:
        term = -self._term
        return Term.from_term(term)

    def __eq__(self, other: SolverType) -> Constraint:
        if isinstance(other, (int, float)):
            c = self._term == other
        elif isinstance(other, Variable):
            c = self._term == other._var
        elif isinstance(other, Term):
            c = self._term == other._term
        elif isinstance(other, Expression):
            c = self._term == other._expr

        return Constraint.from_constraint(c)

    def __le__(self, other: SolverType) -> Constraint:
        if isinstance(other, (int, float)):
            c = self._term <= other
        elif isinstance(other, Variable):
            c = self._term <= other._var
        elif isinstance(other, Term):
            c = self._term <= other._term
        elif isinstance(other, Expression):
            c = self._term <= other._expr

        return Constraint.from_constraint(c)

    def __ge__(self, other: SolverType) -> Constraint:
        if isinstance(other, (int, float)):
            c = self._term >= other
        elif isinstance(other, Variable):
            c = self._term >= other._var
        elif isinstance(other, Term):
            c = self._term >= other._term
        elif isinstance(other, Expression):
            c = self._term >= other._expr

        return Constraint.from_constraint(c)

    def __add__(self, other: SolverType) -> Expression:
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

    def __radd__(self, other: SolverType) -> Expression:
        return self + other

    def __sub__(self, other: SolverType) -> Expression:
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

    def __rsub__(self, other: SolverType) -> Expression:
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

    def __mul__(self, other: int | float) -> Term:
        term = self._term * other
        return Term.from_term(term)

    def __rmul__(self, other: int | float) -> Term:
        return self * other

    def __truediv__(self, other: int | float) -> Term:
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
        return f"{self._term}"

    def __repr__(self) -> str:
        return f"{self} [{hex(id(self._term))}]"


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

    def __neg__(self) -> Expression:
        expr = -self._expr
        return Expression.from_expression(expr)

    def __eq__(self, other: SolverType) -> Constraint:
        if isinstance(other, (int, float)):
            c = self._expr == other
        elif isinstance(other, Variable):
            c = self._expr == other._var
        elif isinstance(other, Term):
            c = self._expr == other._term
        elif isinstance(other, Expression):
            c = self._expr == other._expr

        return Constraint.from_constraint(c)

    def __le__(self, other: SolverType) -> Constraint:
        if isinstance(other, (int, float)):
            c = self._expr <= other
        elif isinstance(other, Variable):
            c = self._expr <= other._var
        elif isinstance(other, Term):
            c = self._expr <= other._term
        elif isinstance(other, Expression):
            c = self._expr <= other._expr

        return Constraint.from_constraint(c)

    def __ge__(self, other: SolverType) -> Constraint:
        if isinstance(other, (int, float)):
            c = self._expr >= other
        elif isinstance(other, Variable):
            c = self._expr >= other._var
        elif isinstance(other, Term):
            c = self._expr >= other._term
        elif isinstance(other, Expression):
            c = self._expr >= other._expr

        return Constraint.from_constraint(c)

    def __add__(self, other: SolverType) -> Expression:
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

    def __radd__(self, other: SolverType) -> Expression:
        return self + other

    def __sub__(self, other: SolverType) -> Expression:
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

    def __rsub__(self, other: SolverType) -> Expression:
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

    def __mul__(self, other: int | float) -> Expression:
        e = self._expr * other
        return Expression.from_expression(e)

    def __rmul__(self, other: int | float) -> Expression:
        return self * other

    def __truediv__(self, other: int | float) -> Expression:
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
        return f"{self._expr}"

    def __repr__(self) -> str:
        return f"{self} [{hex(id(self._expr))}]"


class Constraint:
    def __init__(self, e: Expression, op: Literal["==", "<=", ">="], strength: float):
        self._expr = e
        self._constraint = kiwi.Constraint(e._expr, op, strength)

    @staticmethod
    def from_constraint(c: kiwi.Constraint) -> Constraint:
        e = Expression.from_expression(c.expression())
        return Constraint(e, c.op(), c.strength())

    def __or__(
        self,
        other: float
        | Literal["weak"]
        | Literal["medium"]
        | Literal["strong"]
        | Literal["required"],
    ) -> Constraint:
        return Constraint.from_constraint(self._constraint | other)

    def __ror__(
        self,
        other: float
        | Literal["weak"]
        | Literal["medium"]
        | Literal["strong"]
        | Literal["required"],
    ) -> Constraint:
        return Constraint.from_constraint(self._constraint | other)

    # def __eq__(self, other: Constraint) -> bool:
    #     return self._constraint == other._constraint

    # def __hash__(self) -> int:
    #     return hash(self._constraint)

    def variables(self) -> set[Variable]:
        res = set()
        for t in self._expr._terms:
            res.add(t._var)

        return res

    def dump(self) -> str:
        res = " + ".join([f"({t}) [{t.value()}]" for t in self._expr._terms])
        res += f" {self._constraint.op()} {-1*self._expr._constant}"
        res += f" | strength = {self._constraint.strength()}"
        # TODO: Remove type ignore when this is fixed: https://github.com/nucleic/kiwi/issues/165
        if self._constraint.violated():  # type: ignore
            res += " (VIOLATED)"

        return res

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
        self._constraints: set[Constraint] = set()

    def _find(self, v: str | Variable) -> tuple[Variable | None, set[Constraint]]:
        if isinstance(v, Variable):
            v = v.name()

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

    def reset(self) -> None:
        self._solver = kiwi.Solver()
        self._constraints.clear()

    def add(self, c: Constraint) -> None:
        logger.verbose("Adding constraint %s", c)
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
        self.update()

        res = ""
        for v in self.variables():
            res += f"{v.name()} = {v.value()}\n"
            res += self.dump_var_constraints(v)
            res += "\n\n"

        return res

    def dump_var_constraints(self, v: Variable) -> str:
        _, constraints = self._find(v.name())
        return "\n".join([c.dump() for c in constraints])

    def variables(self) -> set[Variable]:
        res = set()
        for c in self._constraints:
            res |= c.variables()

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
