"""GET /dependency-graph/{id} — Retrieve the dependency graph for a repository."""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query

from core.logging import get_logger
from infrastructure.cache.redis_cache import get_cache
from services.graph_service import GraphService

router = APIRouter(prefix="/dependency-graph", tags=["Graph"])
logger = get_logger(__name__)

_CACHE_TTL = 600  # 10 minutes


@router.get(
    "/{repo_id}",
    response_model=Dict[str, Any],
    summary="Get the dependency graph for a repository",
    description=(
        "Returns a node-link JSON representation of the codebase dependency graph "
        "(files, classes, functions, and their relationships). "
        "Use the `node_type` filter to narrow results."
    ),
)
async def get_dependency_graph(
    repo_id: str,
    node_type: str | None = Query(
        default=None,
        description="Filter nodes by type: file | class | function",
    ),
    max_nodes: int = Query(default=500, ge=1, le=5000),
) -> Dict[str, Any]:
    cache = await get_cache()
    cache_key = f"graph:{repo_id}:{node_type}:{max_nodes}"

    cached = await cache.get(cache_key)
    if cached:
        return cached

    service = GraphService()
    graph = await service.get_graph(repo_id)

    if not graph:
        raise HTTPException(
            status_code=404,
            detail=f"No dependency graph found for repository '{repo_id}'. "
                   "Ensure analysis has completed successfully.",
        )

    # Apply optional filters
    nodes = graph.nodes
    if node_type:
        nodes = [n for n in nodes if n.node_type == node_type]
    nodes = nodes[:max_nodes]

    node_ids = {n.node_id for n in nodes}
    edges = [
        e for e in graph.edges
        if e.source_id in node_ids and e.target_id in node_ids
    ]

    result: Dict[str, Any] = {
        "repo_id": repo_id,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": [n.model_dump() for n in nodes],
        "edges": [e.model_dump() for e in edges],
    }

    await cache.set(cache_key, result, ttl=_CACHE_TTL)
    return result
