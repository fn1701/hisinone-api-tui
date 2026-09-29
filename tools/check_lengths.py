#!/usr/bin/env python3
"""Enforce the size limits of the style guide (see CLAUDE.md).

- a file has at most MAX_FILE_LINES lines (all lines)
- a function/method has at most MAX_CODE_LINES code lines: the body without
  signature, docstring, comment-only lines and blank lines

Usage: check_lengths.py FILE...   (exit code 1 if a limit is exceeded)
"""

import ast
import sys
from pathlib import Path

MAX_FILE_LINES = 150
MAX_CODE_LINES = 20

FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef


class LengthChecker:
    """Checks one source file and collects human readable violations."""

    def __init__(self, path: Path):
        self.path = path
        self.lines = path.read_text(encoding="utf-8").splitlines()
        self.violations: list[str] = []

    def check(self) -> list[str]:
        if len(self.lines) > MAX_FILE_LINES:
            self.violations.append(f"{self.path}: {len(self.lines)} lines (max {MAX_FILE_LINES})")
        tree = ast.parse("\n".join(self.lines), filename=str(self.path))
        for node in ast.walk(tree):
            if isinstance(node, FunctionNode):
                self._check_function(node)
        return self.violations

    def _check_function(self, node: FunctionNode) -> None:
        count = len(self._code_lines(node))
        if count > MAX_CODE_LINES:
            self.violations.append(
                f"{self.path}:{node.lineno}: {node.name}() has {count} code lines "
                f"(max {MAX_CODE_LINES})"
            )

    def _code_lines(self, node: FunctionNode) -> set[int]:
        """Line numbers of the body that contain code (nested functions count
        towards their parent too, they are part of its body)."""
        body = node.body
        if _is_docstring(body[0]):
            body = body[1:]
        numbers: set[int] = set()
        for statement in body:
            numbers.update(range(statement.lineno, statement.end_lineno + 1))
        return {n for n in numbers if self._is_code(self.lines[n - 1])}

    @staticmethod
    def _is_code(line: str) -> bool:
        stripped = line.strip()
        return bool(stripped) and not stripped.startswith("#")


def _is_docstring(statement: ast.stmt) -> bool:
    return (
        isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Constant)
        and isinstance(statement.value.value, str)
    )


def main(paths: list[str]) -> int:
    violations = [v for p in paths for v in LengthChecker(Path(p)).check()]
    for violation in violations:
        print(violation)
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
