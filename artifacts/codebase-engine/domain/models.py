"""Domain models (entities) for the codebase understanding engine."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl


class AnalysisStatus(str, Enum):
    """Lifecycle states for a repository analysis job."""

    PENDING = "pending"
    CLONING = "cloning"
    PARSING = "parsing"
    EMBEDDING = "embedding"
    ANALYZING = "analyzing"
    COMPLETE = "complete"
    FAILED = "failed"


class SupportedLanguage(str, Enum):
    """Programming languages the engine can parse."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"
    UNKNOWN = "unknown"


class IssueSeverity(str, Enum):
    """Severity levels for detected code issues."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueType(str, Enum):
    """Category of a detected code issue."""

    UNUSED_VARIABLE = "unused_variable"
    CIRCULAR_IMPORT = "circular_import"
    MISSING_TYPE_HINT = "missing_type_hint"
    LONG_FUNCTION = "long_function"
    COMPLEX_FUNCTION = "complex_function"
    POTENTIAL_BUG = "potential_bug"
    SECURITY_VULNERABILITY = "security_vulnerability"
    CODE_SMELL = "code_smell"


# ─── Value objects ─────────────────────────────────────────────────────────────


class CodeChunk(BaseModel):
    """A slice of source code ready for embedding."""

    chunk_id: str = Field(default_factory=lambda: str(uuid4()))
    repo_id: str
    file_path: str
    start_line: int
    end_line: int
    content: str
    language: SupportedLanguage = SupportedLanguage.UNKNOWN
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FunctionInfo(BaseModel):
    """Metadata extracted from a function/method definition."""

    name: str
    file_path: str
    start_line: int
    end_line: int
    docstring: Optional[str] = None
    arguments: List[str] = Field(default_factory=list)
    return_type: Optional[str] = None
    calls: List[str] = Field(default_factory=list)
    decorators: List[str] = Field(default_factory=list)
    is_async: bool = False
    complexity: int = 1


class ClassInfo(BaseModel):
    """Metadata extracted from a class definition."""

    name: str
    file_path: str
    start_line: int
    end_line: int
    docstring: Optional[str] = None
    bases: List[str] = Field(default_factory=list)
    methods: List[FunctionInfo] = Field(default_factory=list)
    attributes: List[str] = Field(default_factory=list)


class ImportInfo(BaseModel):
    """A single import statement extracted from a file."""

    module: str
    names: List[str] = Field(default_factory=list)
    is_from_import: bool = False
    line: int = 0
    alias: Optional[str] = None


class FileAnalysis(BaseModel):
    """Full parsed representation of a single source file."""

    file_path: str
    language: SupportedLanguage
    lines_of_code: int
    functions: List[FunctionInfo] = Field(default_factory=list)
    classes: List[ClassInfo] = Field(default_factory=list)
    imports: List[ImportInfo] = Field(default_factory=list)
    summary: Optional[str] = None
    complexity_score: float = 0.0


class CodeIssue(BaseModel):
    """A static or semantic issue detected in the codebase."""

    issue_id: str = Field(default_factory=lambda: str(uuid4()))
    repo_id: str
    file_path: str
    line: Optional[int] = None
    issue_type: IssueType
    severity: IssueSeverity
    message: str
    suggestion: Optional[str] = None
    context: Optional[str] = None


class RefactorSuggestion(BaseModel):
    """A suggestion for improving code structure or quality."""

    suggestion_id: str = Field(default_factory=lambda: str(uuid4()))
    repo_id: str
    file_path: str
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    title: str
    description: str
    pattern: Optional[str] = None
    original_code: Optional[str] = None
    suggested_code: Optional[str] = None
    effort: str = "medium"  # low / medium / high


class GraphNode(BaseModel):
    """A node in the dependency graph."""

    node_id: str
    node_type: str  # file / class / function / module
    name: str
    file_path: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """A directed edge between two graph nodes."""

    source_id: str
    target_id: str
    edge_type: str  # imports / calls / inherits / contains
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DependencyGraph(BaseModel):
    """Full dependency graph for a repository."""

    repo_id: str
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ─── Aggregate roots ──────────────────────────────────────────────────────────


class Repository(BaseModel):
    """Top-level aggregate representing an analysed GitHub repository."""

    repo_id: str = Field(default_factory=lambda: str(uuid4()))
    github_url: str
    owner: str = ""
    name: str = ""
    branch: str = "main"
    status: AnalysisStatus = AnalysisStatus.PENDING
    languages: List[SupportedLanguage] = Field(default_factory=list)
    file_count: int = 0
    total_lines: int = 0
    architecture_summary: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    def mark_status(self, status: AnalysisStatus, error: Optional[str] = None) -> None:
        """Transition to a new lifecycle status."""
        self.status = status
        self.updated_at = datetime.utcnow()
        if error:
            self.error_message = error
        if status == AnalysisStatus.COMPLETE:
            self.completed_at = datetime.utcnow()


# ─── Request / Response DTOs ──────────────────────────────────────────────────


class AnalyzeRepoRequest(BaseModel):
    """Payload for POST /analyze-repo."""

    github_url: str = Field(..., description="Full GitHub repository URL")
    branch: str = Field(default="main", description="Branch to analyse")
    force_reanalysis: bool = Field(
        default=False, description="Re-run even if analysis already exists"
    )


class AskQuestionRequest(BaseModel):
    """Payload for POST /ask."""

    repo_id: str = Field(..., description="Repository ID to query against")
    question: str = Field(..., description="Natural language question about the code")
    max_chunks: int = Field(default=5, ge=1, le=20)


class AnalyzeRepoResponse(BaseModel):
    """Response for POST /analyze-repo."""

    repo_id: str
    status: AnalysisStatus
    message: str


class RepoSummaryResponse(BaseModel):
    """Response for GET /repo-summary/{id}."""

    repo_id: str
    github_url: str
    status: AnalysisStatus
    languages: List[str]
    file_count: int
    total_lines: int
    architecture_summary: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]


class AskResponse(BaseModel):
    """Response for POST /ask."""

    repo_id: str
    question: str
    answer: str
    source_chunks: List[Dict[str, Any]] = Field(default_factory=list)
