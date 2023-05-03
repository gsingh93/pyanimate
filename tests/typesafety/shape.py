from pyanimate.shape import Shape

s1 = Shape(1, 2)  # T: Shape[int, int]
s2 = Shape(3, 4)  # T: Shape[int, int]
s3 = s1 + s2  # T: Shape[int, int]

s1 = Shape(1, 2)  # T: Shape[int, int]
s2 = Shape(3, 4, 5)  # T: Shape[int, int, int]
s3 = s1 + s2  # E: Operator "+" not supported for types "Shape[int, int]" and "Shape[int, int, int]"
s4 = s2 + s1  # E: Operator "+" not supported for types "Shape[int, int, int]" and "Shape[int, int]"

s1 = Shape(1, 2)  # T: Shape[int, int]
s2 = (3, 4)  # T: tuple[int, int]
s3 = s1 + s2  # E: Operator "+" not supported for types "Shape[int, int]" and "tuple[Literal[3], Literal[4]]"
s3 = s2 + s1  # T: tuple[int, int]

s1 = Shape(1, 2)  # T: Shape[int, int]
s2 = 3  # T: int
s3 = s1 + s2  # E: Operator "+" not supported for types "Shape[int, int]" and "Literal[3]"
