"""Dependency graph construction service.

Builds a directed graph from parsed file analyses:
- File nodes
- Class nodes (contained within files)
- Function nodes (contained within classes or files)
- Import edges (file A imports module B)
- Call edges (function A calls function B)
- Inheritance edges (class A extends class B)
- Contains edges (file contains class / class contains method)
"""

from typing import Dict, List, Optional

from core.logging import get_logger
from domain.models import (
    DependencyGraph,
    FileAnalysis,
    GraphEdge,
    GraphNode,
)
from infrastructure.graph.graph_db import get_graph_store

logger = get_logger(__name__)


class GraphService:
    """Builds and persists the codebase dependency graph."""

    def __init__(self) -> None:
        self._store = get_graph_store()

    async def build_and_save(
        self, repo_id: str, file_analyses: List[FileAnalysis]
    ) -> DependencyGraph:
        """
        Build the complete dependency graph from file analyses and persist it.
        """
        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []

        # Index: module_name or file_path → node_id
        file_id_map: Dict[str, str] = {}
        func_id_map: Dict[str, str] = {}
        class_id_map: Dict[str, str] = {}

        # ── Pass 1: create all nodes ─────────────────────────────────────────
        for analysis in file_analyses:
            file_node_id = f"file::{analysis.file_path}"
            file_id_map[analysis.file_path] = file_node_id

            nodes.append(
                GraphNode(
                    node_id=file_node_id,
                    node_type="file",
                    name=analysis.file_path,
                    file_path=analysis.file_path,
                    metadata={
                        "language": analysis.language.value,
                        "loc": analysis.lines_of_code,
                        "complexity": analysis.complexity_score,
                    },
                )
            )

            for cls in analysis.classes:
                cls_id = f"class::{analysis.file_path}::{cls.name}"
                class_id_map[f"{analysis.file_path}::{cls.name}"] = cls_id
                nodes.append(
                    GraphNode(
                        node_id=cls_id,
                        node_type="class",
                        name=cls.name,
                        file_path=analysis.file_path,
                        metadata={"bases": cls.bases},
                    )
                )
                # file contains class
                edges.append(
                    GraphEdge(source_id=file_node_id, target_id=cls_id, edge_type="contains")
                )
                for method in cls.methods:
                    m_id = f"method::{analysis.file_path}::{cls.name}::{method.name}"
                    func_id_map[f"{analysis.file_path}::{cls.name}::{method.name}"] = m_id
                    nodes.append(
                        GraphNode(
                            node_id=m_id,
                            node_type="function",
                            name=f"{cls.name}.{method.name}",
                            file_path=analysis.file_path,
                            metadata={
                                "is_async": method.is_async,
                                "complexity": method.complexity,
                            },
                        )
                    )
                    edges.append(
                        GraphEdge(source_id=cls_id, target_id=m_id, edge_type="contains")
                    )

            for func in analysis.functions:
                f_id = f"func::{analysis.file_path}::{func.name}"
                func_id_map[f"{analysis.file_path}::{func.name}"] = f_id
                nodes.append(
                    GraphNode(
                        node_id=f_id,
                        node_type="function",
                        name=func.name,
                        file_path=analysis.file_path,
                        metadata={
                            "is_async": func.is_async,
                            "complexity": func.complexity,
                        },
                    )
                )
                edges.append(
                    GraphEdge(source_id=file_node_id, target_id=f_id, edge_type="contains")
                )

        # ── Pass 2: import edges ─────────────────────────────────────────────
        for analysis in file_analyses:
            src_id = file_id_map[analysis.file_path]
            for imp in analysis.imports:
                # Try to resolve the import to a known file
                target_id = self._resolve_import(imp.module, file_id_map)
                if target_id:
                    edges.append(
                        GraphEdge(
                            source_id=src_id,
                            target_id=target_id,
                            edge_type="imports",
                            metadata={"module": imp.module},
                        )
                    )

        # ── Pass 3: inheritance edges ────────────────────────────────────────
        for analysis in file_analyses:
            for cls in analysis.classes:
                cls_id = class_id_map.get(f"{analysis.file_path}::{cls.name}")
                if not cls_id:
                    continue
                for base in cls.bases:
                    # Find base class node in any file
                    for key, nid in class_id_map.items():
                        if key.endswith(f"::{base}"):
                            edges.append(
                                GraphEdge(
                                    source_id=cls_id,
                                    target_id=nid,
                                    edge_type="inherits",
                                )
                            )
                            break

        graph = DependencyGraph(repo_id=repo_id, nodes=nodes, edges=edges)
        await self._store.save_graph(graph)

        logger.info(
            "Dependency graph built",
            repo_id=repo_id,
            nodes=len(nodes),
            edges=len(edges),
        )
        return graph

    async def get_graph(self, repo_id: str) -> Optional[DependencyGraph]:
        """Retrieve the stored dependency graph for a repository."""
        return await self._store.get_graph(repo_id)

    def _resolve_import(
        self, module: str, file_id_map: Dict[str, str]
    ) -> Optional[str]:
        """Try to map a module name to a known file node id."""
        # Try direct match and common path variants
        candidates = [
            module.replace(".", "/") + ".py",
            module.replace(".", "/") + "/__init__.py",
            module + ".py",
        ]
        for candidate in candidates:
            if candidate in file_id_map:
                return file_id_map[candidate]
        return None
