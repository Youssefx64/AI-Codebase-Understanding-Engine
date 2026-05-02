"""Unit tests for the Python AST parser."""

import pytest

from domain.models import SupportedLanguage
from parsers.python_parser import PythonParser

SIMPLE_PYTHON = """
import os
from pathlib import Path

class Greeter:
    \"\"\"Greets people.\"\"\"

    def __init__(self, name: str) -> None:
        self.name = name

    def greet(self) -> str:
        return f"Hello, {self.name}!"

def add(a: int, b: int) -> int:
    return a + b
"""

COMPLEX_PYTHON = """
def complex_function(x, y, z):
    if x > 0:
        if y > 0:
            while z > 0:
                z -= 1
                if z == 5:
                    break
            for i in range(10):
                pass
        else:
            try:
                result = x / y
            except ZeroDivisionError:
                result = 0
    return result
"""


@pytest.fixture
def parser() -> PythonParser:
    return PythonParser()


class TestPythonParser:
    def test_supports_py_extension(self, parser: PythonParser) -> None:
        assert parser.supports(".py")
        assert parser.supports("python")
        assert not parser.supports(".js")

    def test_parses_classes(self, parser: PythonParser) -> None:
        analysis = parser.parse_file("test.py", SIMPLE_PYTHON)
        assert len(analysis.classes) == 1
        cls = analysis.classes[0]
        assert cls.name == "Greeter"
        assert cls.docstring == "Greets people."
        assert len(cls.methods) == 2

    def test_parses_functions(self, parser: PythonParser) -> None:
        analysis = parser.parse_file("test.py", SIMPLE_PYTHON)
        func_names = [f.name for f in analysis.functions]
        assert "add" in func_names

    def test_parses_imports(self, parser: PythonParser) -> None:
        analysis = parser.parse_file("test.py", SIMPLE_PYTHON)
        import_modules = [i.module for i in analysis.imports]
        assert "os" in import_modules
        assert "pathlib" in import_modules

    def test_return_types(self, parser: PythonParser) -> None:
        analysis = parser.parse_file("test.py", SIMPLE_PYTHON)
        add_func = next(f for f in analysis.functions if f.name == "add")
        assert add_func.return_type == "int"

    def test_language_is_python(self, parser: PythonParser) -> None:
        analysis = parser.parse_file("test.py", SIMPLE_PYTHON)
        assert analysis.language == SupportedLanguage.PYTHON

    def test_cyclomatic_complexity(self, parser: PythonParser) -> None:
        analysis = parser.parse_file("complex.py", COMPLEX_PYTHON)
        assert len(analysis.functions) == 1
        func = analysis.functions[0]
        assert func.name == "complex_function"
        assert func.complexity > 1  # Should be high due to many branches

    def test_lines_of_code(self, parser: PythonParser) -> None:
        analysis = parser.parse_file("test.py", SIMPLE_PYTHON)
        assert analysis.lines_of_code > 0

    def test_graceful_failure_on_syntax_error(self, parser: PythonParser) -> None:
        bad_code = "def broken(:\n    pass"
        analysis = parser.parse_file("broken.py", bad_code)
        # Should not raise; returns minimal analysis
        assert analysis.file_path == "broken.py"
        assert analysis.language == SupportedLanguage.PYTHON

    def test_async_function_detection(self, parser: PythonParser) -> None:
        code = "async def fetch(url: str) -> bytes:\n    return b''"
        analysis = parser.parse_file("async_test.py", code)
        assert len(analysis.functions) == 1
        assert analysis.functions[0].is_async is True
