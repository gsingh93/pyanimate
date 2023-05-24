from pyanimate.shape import Shape
from pyanimate.solver import Variable


def rand() -> int:
    ...

s1 = Shape("foo")  # E: Argument of type "Literal['foo']" cannot be assigned to parameter "args" of type "T@Shape" in function "__new__"

## Addition

s1 = Shape(1, 2)  # T: Shape[int]
s2 = Shape(3, 4)  # T: Shape[int]
s3 = s1 + s2  # T: Shape[int]

s1 = Shape(1.0, 2.0)  # T: Shape[float]
s2 = Shape(3.0, 4.0)  # T: Shape[float]
s3 = s1 + s2  # T: Shape[float]

s1 = Shape(1.0, 2)  # T: Shape[int | float]
s2 = Shape(3, 4.0)  # T: Shape[int | float]
s3 = s1 + s2  # T: Shape[int | float]

s1 = Shape(1.0, 2)  # T: Shape[int | float]
s2 = Shape(3, 4)  # T: Shape[int]
s3 = s1 + s2  # T: Shape[int | float]
s3 = s2 + s1  # T: Shape[int | float]

s1 = Shape(1, 2)  # T: Shape[int]
s3 = s1.add(2)  # T: Shape[int]

s1 = Shape(1, 2)  # T: Shape[int]
s3 = s1.add(2.0)  # T: Shape[int]

l1 = rand()
s1 = Shape(1, 2)
s3 = l1 + s1  # E: Operator "+" not supported for types "int" and "Shape[int]"
s3 = s1 + l1  # E: Operator "+" not supported for types "Shape[int]" and "int"

s1 = Shape(Variable('x'), 1)
s2 = Shape(1, 2)
s3 = s1 + s2
s3 = s2 + s1

s1 = Shape(Variable('x'), 1)
s2 = Shape(1, Variable('y'))
s3 = s1 + s2

s1 = Shape(Variable('x'), Variable('y'))
s2 = Shape(1, 2)
s3 = s1 + s2
s3 = s2 + s1

s1 = Shape(Variable('x'), Variable('y'))
s2 = Shape(Variable('a'), Variable('b'))
s3 = s1 + s2
s3 = s2 + s1

s1.add(2)
s1.add(2.0)
s1.add(s2)  # E: Argument of type "Shape[Variable]" cannot be assigned to parameter "other" of type "int | float" in function "add"

## Multiplication

s1 = Shape(1, 2)  # T: Shape[int]
s2 = Shape(3, 4)  # T: Shape[int]
s3 = s1 * s2  # T: Shape[int]

s1 = Shape(1.0, 2.0)  # T: Shape[float]
s2 = Shape(3.0, 4.0)  # T: Shape[float]
s3 = s1 * s2  # T: Shape[float]

s1 = Shape(1.0, 2)  # T: Shape[int | float]
s2 = Shape(3, 4.0)  # T: Shape[int | float]
s3 = s1 * s2  # T: Shape[int | float]

s1 = Shape(1.0, 2)  # T: Shape[int | float]
s2 = Shape(3, 4)  # T: Shape[int]
s3 = s1 * s2  # T: Shape[int | float]
s3 = s2 * s1  # T: Shape[int | float]

s1 = Shape(1, 2)  # T: Shape[int]
s3 = s1.mul(2)  # T: Shape[int]

s1 = Shape(1, 2)  # T: Shape[int]
s3 = s1.mul(2.0)  # T: Shape[int]

l1 = rand()
s1 = Shape(1, 2)
s3 = l1 * s1  # E: Operator "*" not supported for types "int" and "Shape[int]"
s3 = s1 * l1  # E: Operator "*" not supported for types "Shape[int]" and "int"

s1 = Shape(Variable('x'), 1)
s2 = Shape(1, 2)
s3 = s1 * s2
s3 = s2 * s1

s1 = Shape(Variable('x'), 1)
s2 = Shape(1, Variable('y'))
s3 = s1 * s2  # E: Operator "*" not supported for types "Shape[Variable | int]" and "Shape[Variable | int]"

s1 = Shape(Variable('x'), 1.0)
s2 = Shape(1.0, Variable('y'))
s3 = s1 * s2  # E: Operator "*" not supported for types "Shape[Variable | float]" and "Shape[float | Variable]"

s1 = Shape(Variable('x'), Variable('y'))
s2 = Shape(1, 2)
s3 = s1 * s2
s3 = s2 * s1

s1 = Shape(Variable('x'), Variable('y'))
s2 = Shape(Variable('a'), Variable('b'))
s3 = s1 * s2  # E: Operator "*" not supported for types "Shape[Variable]" and "Shape[Variable]"
s3 = s2 * s1  # E: Operator "*" not supported for types "Shape[Variable]" and "Shape[Variable]"

s1.mul(2)
s1.mul(2.0)
s1.mul(s2)  # E: Argument of type "Shape[Variable]" cannot be assigned to parameter "other" of type "int | float" in function "mul"
