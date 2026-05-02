"""Graph database adapter.

Provides a NetworkX in-memory implementation by default, with a Neo4j
implementation available when NEO4J_URI is configured. Both satisfy the
IGraphStore interface so services remain decoupled from the storage engine.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import networkx as nx

from core.config import get_settings
from core.exceptions import GraphDBError
from core.logging import get_logger
from domain.interfaces import IGraphStore
from domain.models import DependencyGraph, GraphEdge, GraphNode

logger = get_logger(__name__)

_GRAPH_PERSIST_DIR = Path("./data/graphs")


class NetworkXGraphStore(IGraphStore):
    """
    In-process graph store backed by NetworkX directed graphs.

    Graphs are serialised to JSON on disk so they survive restarts.
    This is the default implementation used in development and when
    NEO4J_URI is not configured.
    """

    def __init__(self) -> None:
        _GRAPH_PERSIST_DIR.mkdir(parents=True, exist_ok=True)

    def _path(self, repo_id: str) -> Path:
        return _GRAPH_PERSIST_DIR / f"{repo_id}.json"

    async def save_graph(self, graph: DependencyGraph) -> None:
        try:
            G = nx.DiGraph()
            for node in graph.nodes:
                G.add_node(node.node_id, **node.model_dump())
            for edge in graph.edges:
                G.add_edge(edge.source_id, edge.target_id, **edge.model_dump())

            data = nx.node_link_data(G)
            self._path(graph.repo_id).write_text(json.dumps(data, default=str))
            logger.debug(
                "Graph saved",
                repo_id=graph.repo_id,
                nodes=len(graph.nodes),
                edges=len(graph.edges),
            )
        except Exception as exc:
            raise GraphDBError(str(exc)) from exc

    async def get_graph(self, repo_id: str) -> Optional[DependencyGraph]:
        path = self._path(repo_id)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            G = nx.node_link_graph(data, directed=True)

            nodes = [GraphNode(**G.nodes[n]) for n in G.nodes]
            edges = [
                GraphEdge(**G.edges[u, v]) for u, v in G.edges
            ]
            return DependencyGraph(repo_id=repo_id, nodes=nodes, edges=edges)
        except Exception as exc:
            logger.error("Failed to load graph", repo_id=repo_id, error=str(exc))
            raise GraphDBError(str(exc)) from exc

    async def delete_graph(self, repo_id: str) -> None:
        path = self._path(repo_id)
        if path.exists():
            path.unlink()


class Neo4jGraphStore(IGraphStore):
    """
    Neo4j-backed graph store.

    Activated automatically when NEO4J_URI is set in the environment.
    Requires: pip install neo4j
    """

    def __init__(self) -> None:
        try:
            from neo4j import AsyncGraphDatabase  # type: ignore

            settings = get_settings()
            self._driver = AsyncGraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_username, settings.neo4j_password),
            )
            logger.info("Neo4j driver initialised", uri=settings.neo4j_uri)
        except ImportError:
            raise GraphDBError(
                "neo4j package not installed. Run: pip install neo4j"
            )

    async def save_graph(self, graph: DependencyGraph) -> None:
        async with self._driver.session() as session:
            # Clear existing data for this repo
            await session.run(
                "MATCH (n {repo_id: $repo_id}) DETACH DELETE n",
                repo_id=graph.repo_id,
            )
            # Create nodes
            for node in graph.nodes:
                await session.run(
                    """
                    CREATE (n:CodeNode {
                        node_id: $node_id, repo_id: $repo_id,
                        node_type: $node_type, name: $name,
                        file_path: $file_path
                    })
                    """,
                    node_id=node.node_id,
                    repo_id=graph.repo_id,
                    node_type=node.node_type,
                    name=node.name,
                    file_path=node.file_path or "",
                )
            # Create edges
            for edge in graph.edges:
                await session.run(
                    """
                    MATCH (a:CodeNode {node_id: $source}),
                          (b:CodeNode {node_id: $target})
                    CREATE (a)-[r:DEPENDS_ON {edge_type: $edge_type}]->(b)
                    """,
                    source=edge.source_id,
                    target=edge.target_id,
                    edge_type=edge.edge_type,
                )

    async def get_graph(self, repo_id: str) -> Optional[DependencyGraph]:
        async with self._driver.session() as session:
            node_result = await session.run(
                "MATCH (n {repo_id: $repo_id}) RETURN n", repo_id=repo_id
            )
            edge_result = await session.run(
                """
                MATCH (a {repo_id: $repo_id})-[r]->(b {repo_id: $repo_id})
                RETURN a.node_id, b.node_id, r.edge_type
                """,
                repo_id=repo_id,
            )
            nodes = [
                GraphNode(
                    node_id=record["n"]["node_id"],
                    node_type=record["n"]["node_type"],
                    name=record["n"]["name"],
                    file_path=record["n"].get("file_path"),
                )
                async for record in node_result
            ]
            edges = [
                GraphEdge(
                    source_id=record[0],
                    target_id=record[1],
                    edge_type=record[2],
                )
                async for record in edge_result
            ]
            return DependencyGraph(repo_id=repo_id, nodes=nodes, edges=edges) if nodes else None

    async def delete_graph(self, repo_id: str) -> None:
        async with self._driver.session() as session:
            await session.run(
                "MATCH (n {repo_id: $repo_id}) DETACH DELETE n",
                repo_id=repo_id,
            )


def get_graph_store() -> IGraphStore:
    """Factory: return Neo4j store if configured, else NetworkX."""
    settings = get_settings()
    if settings.neo4j_uri:
        try:
            return Neo4jGraphStore()
        except Exception as exc:
            logger.warning("Neo4j unavailable, falling back to NetworkX", error=str(exc))
    return NetworkXGraphStore()
