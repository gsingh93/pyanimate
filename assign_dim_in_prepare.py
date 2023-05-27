import pdb

import astroid
from pylint.checkers import BaseChecker
from pylint.interfaces import IAstroidChecker
from pylint.lint import PyLinter


class AssertChecker(BaseChecker):
    __implements__ = IAstroidChecker

    name = "assign-dim-in-prepare"
    msgs = {
        "E9998": (
            "Assignment to width or height in prepare() or prepare_impl()",
            "assign-dim-in-prepare",
            "Assignment to width or height in prepare() or prepare_impl() will have no effect",
        ),
    }

    def visit_assign(self, node: astroid.Assign):
        target = node.targets[0]
        if isinstance(target, astroid.AssignAttr):
            if target.attrname in ["width", "height"]:
                scope = node.scope()
                if isinstance(scope, astroid.FunctionDef):
                    if scope.name in ["prepare", "prepare_impl"]:
                        self.add_message("assign-dim-in-prepare", node=node)


def register(linter: PyLinter):
    linter.register_checker(AssertChecker(linter))
