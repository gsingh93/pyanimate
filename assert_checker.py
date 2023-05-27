import pdb

import astroid
from pylint.checkers import BaseChecker
from pylint.interfaces import IAstroidChecker
from pylint.lint import PyLinter


class AssertChecker(BaseChecker):
    __implements__ = IAstroidChecker

    name = "assert-checker"
    msgs = {
        "E9999": (
            "Assertion on variable with type Constraint",
            "assert-on-constraint",
            "Assertions on variables of type Constraint are usually a bug",
        ),
    }

    def visit_compare(self, node: astroid.Compare):
        found_assert = False
        p = node.parent
        while p is not None:
            if isinstance(p, astroid.Assert):
                found_assert = True
                break
            p = p.parent

        if not found_assert:
            return

        if node.ops[0][0] in ["<=", ">=", "=="]:
            try:
                context = next(node.left.infer())
                if context.name in ["Expression", "Variable"]:
                    self.add_message("assert-on-constraint", node=node)
                    return
            except astroid.exceptions.InferenceError:
                pass

            right = node.ops[0][1]
            try:
                context = next(right.infer())
                if context.name in ["Expression", "Variable"]:
                    self.add_message("assert-on-constraint", node=node)
                    return
            except astroid.exceptions.InferenceError:
                pass


def register(linter: PyLinter):
    linter.register_checker(AssertChecker(linter))
