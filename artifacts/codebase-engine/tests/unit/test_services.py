"""Unit tests for service layer components."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from domain.models import (
    AnalysisStatus,
    FileAnalysis,
    FunctionInfo,
    IssueSeverity,
    IssueType,
    Repository,
    SupportedLanguage,
)
from services.bug_detection_service import BugDetectionService


def _make_function(
    name: str = "my_func",
    start_line: int = 1,
    end_line: int = 10,
    complexity: int = 1,
    return_type: str | None = None,
) -> FunctionInfo:
    return FunctionInfo(
        name=name,
        file_path="test.py",
        start_line=start_line,
        end_line=end_line,
        complexity=complexity,
        return_type=return_type,
    )


def _make_analysis(functions=None, classes=None) -> FileAnalysis:
    return FileAnalysis(
        file_path="test.py",
        language=SupportedLanguage.PYTHON,
        lines_of_code=100,
        functions=functions or [],
        classes=classes or [],
    )


class TestBugDetectionService:
    @pytest.fixture
    def service(self) -> BugDetectionService:
        return BugDetectionService()

    def test_long_function_detected(self, service: BugDetectionService) -> None:
        func = _make_function(start_line=1, end_line=100, complexity=2)
        analysis = _make_analysis(functions=[func])
        issues = service.detect_static_issues("repo-1", [analysis])
        long_func_issues = [i for i in issues if i.issue_type == IssueType.LONG_FUNCTION]
        assert len(long_func_issues) == 1
        assert long_func_issues[0].severity == IssueSeverity.MEDIUM

    def test_complex_function_detected(self, service: BugDetectionService) -> None:
        func = _make_function(complexity=15)
        analysis = _make_analysis(functions=[func])
        issues = service.detect_static_issues("repo-1", [analysis])
        complex_issues = [i for i in issues if i.issue_type == IssueType.COMPLEX_FUNCTION]
        assert len(complex_issues) == 1

    def test_missing_return_type_detected(self, service: BugDetectionService) -> None:
        func = _make_function(name="public_method", return_type=None)
        analysis = _make_analysis(functions=[func])
        issues = service.detect_static_issues("repo-1", [analysis])
        hint_issues = [i for i in issues if i.issue_type == IssueType.MISSING_TYPE_HINT]
        assert len(hint_issues) == 1

    def test_private_function_skipped_for_type_hint(self, service: BugDetectionService) -> None:
        func = _make_function(name="_private_method", return_type=None)
        analysis = _make_analysis(functions=[func])
        issues = service.detect_static_issues("repo-1", [analysis])
        hint_issues = [i for i in issues if i.issue_type == IssueType.MISSING_TYPE_HINT]
        assert len(hint_issues) == 0

    def test_no_issues_on_clean_code(self, service: BugDetectionService) -> None:
        func = _make_function(
            name="clean_func", start_line=1, end_line=20, complexity=2, return_type="str"
        )
        analysis = _make_analysis(functions=[func])
        issues = service.detect_static_issues("repo-1", [analysis])
        assert len(issues) == 0

    def test_circular_import_detection(self, service: BugDetectionService) -> None:
        from domain.models import ImportInfo

        # a imports b, b imports a
        a = FileAnalysis(
            file_path="a.py",
            language=SupportedLanguage.PYTHON,
            lines_of_code=5,
            imports=[ImportInfo(module="b", is_from_import=False, line=1)],
        )
        b = FileAnalysis(
            file_path="b.py",
            language=SupportedLanguage.PYTHON,
            lines_of_code=5,
            imports=[ImportInfo(module="a", is_from_import=False, line=1)],
        )
        issues = service.detect_static_issues("repo-1", [a, b])
        circular = [i for i in issues if i.issue_type == IssueType.CIRCULAR_IMPORT]
        assert len(circular) >= 1


class TestRepository:
    def test_mark_status_transitions(self) -> None:
        repo = Repository(github_url="https://github.com/test/test")
        assert repo.status == AnalysisStatus.PENDING

        repo.mark_status(AnalysisStatus.CLONING)
        assert repo.status == AnalysisStatus.CLONING

        repo.mark_status(AnalysisStatus.COMPLETE)
        assert repo.status == AnalysisStatus.COMPLETE
        assert repo.completed_at is not None

    def test_mark_status_with_error(self) -> None:
        repo = Repository(github_url="https://github.com/test/test")
        repo.mark_status(AnalysisStatus.FAILED, error="Clone failed")
        assert repo.status == AnalysisStatus.FAILED
        assert repo.error_message == "Clone failed"
