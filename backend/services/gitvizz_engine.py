from __future__ import annotations

from pathlib import Path
from typing import Any


class GitVizzEngine:
    """Adapter for GitVizz GraphGenerator with stable output normalization."""

    def __init__(self) -> None:
        self._graph_generator_cls = None
        try:
            from gitvizz import GraphGenerator

            self._graph_generator_cls = GraphGenerator
        except Exception:
            self._graph_generator_cls = None

    @property
    def available(self) -> bool:
        return self._graph_generator_cls is not None

    def generate(self, repo_path: Path, files: list[Path]) -> dict[str, Any]:
        if not self._graph_generator_cls:
            raise RuntimeError("GitVizz GraphGenerator is not available")

        files_data: list[dict[str, str]] = []
        for file_path in files:
            try:
                rel_path = str(file_path.relative_to(repo_path)).replace("\\", "/")
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            files_data.append({"path": rel_path, "content": content})

        generator = self._graph_generator_cls(files=files_data)
        raw_graph = generator.generate()
        return self._normalize(raw_graph)

    def _normalize(self, raw_graph: Any) -> dict[str, Any]:
        if not isinstance(raw_graph, dict):
            return {"nodes": [], "edges": [], "metadata": {"engine": "gitvizz"}}

        graph_block = raw_graph.get("graph") if isinstance(raw_graph.get("graph"), dict) else {}
        raw_nodes = raw_graph.get("nodes") or graph_block.get("nodes") or []
        raw_edges = raw_graph.get("edges") or graph_block.get("edges") or []

        nodes: list[dict[str, Any]] = []
        for item in raw_nodes:
            if not isinstance(item, dict):
                continue
            node_id = (
                item.get("id")
                or item.get("path")
                or item.get("file")
                or item.get("name")
                or item.get("label")
            )
            if not node_id:
                continue
            node_path = str(node_id).replace("\\", "/")
            nodes.append(
                {
                    "id": node_path,
                    "label": item.get("label") or Path(node_path).name,
                    "group": item.get("type") or Path(node_path).suffix.replace(".", "") or "other",
                    "metadata": {
                        "language": item.get("language"),
                        "size": item.get("size"),
                    },
                }
            )

        edges: list[dict[str, Any]] = []
        for item in raw_edges:
            if not isinstance(item, dict):
                continue
            source = item.get("source") or item.get("from") or item.get("src")
            target = item.get("target") or item.get("to") or item.get("dst")
            if not source or not target:
                continue
            edges.append(
                {
                    "source": str(source).replace("\\", "/"),
                    "target": str(target).replace("\\", "/"),
                }
            )

        metadata = {
            "engine": "gitvizz",
            "raw_keys": sorted(raw_graph.keys()),
            "node_count": len(nodes),
            "edge_count": len(edges),
        }
        return {"nodes": nodes, "edges": edges, "metadata": metadata}
