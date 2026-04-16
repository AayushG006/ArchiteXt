from __future__ import annotations

import itertools
import re
import shutil
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import networkx as nx
from git import Repo

from .doc_generator import ExternalDocumentationGenerator
from .gitvizz_engine import GitVizzEngine


SKIP_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "venv",
    ".venv",
    "__pycache__",
    ".next",
    "target",
    ".idea",
    ".vscode",
}

SUPPORTED_IMPORT_FILES = {".py", ".js", ".jsx", ".ts", ".tsx"}


class RepositoryAnalyzer:
    def __init__(self) -> None:
        self.doc_generator = ExternalDocumentationGenerator()
        self.gitvizz_engine = GitVizzEngine()
        self.cache_ttl_seconds = 20 * 60
        self._cache: dict[str, dict[str, Any]] = {}

    def analyze_from_url(self, repo_url: str) -> dict[str, Any]:
        now_ts = datetime.utcnow().timestamp()
        cached = self._cache.get(repo_url)
        if cached and now_ts - cached["timestamp"] <= self.cache_ttl_seconds:
            result = dict(cached["value"])
            result["analysis_meta"] = {
                **result.get("analysis_meta", {}),
                "cache": "hit",
                "cached_at": cached.get("cached_at"),
            }
            return result

        temp_dir = tempfile.mkdtemp(prefix="architectx-")
        repo_path = Path(temp_dir) / "repo"

        try:
            Repo.clone_from(repo_url, repo_path)
            result = self.analyze_local_repo(repo_path, repo_url=repo_url)
            self._cache[repo_url] = {
                "timestamp": now_ts,
                "cached_at": datetime.utcnow().isoformat() + "Z",
                "value": result,
            }
            return result
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def analyze_local_repo(self, repo_path: Path, repo_url: str | None = None) -> dict[str, Any]:
        repo = Repo(repo_path)
        hot_files, hot_folders, file_commit_counter = self._build_hot_insights(repo)
        file_tree = self._build_file_tree(repo_path)
        dependency_graph = self._build_dependency_graph(repo_path, file_commit_counter)
        co_change_graph = self._build_co_change_graph(repo, file_commit_counter)
        file_types = self._build_file_type_distribution(repo_path)
        timeline = self._build_activity_timeline(repo)
        risks = self._build_risk_panel(hot_files, dependency_graph)

        doc_context = {
            "hot_files": hot_files,
            "hot_folders": hot_folders,
            "dependency_graph": dependency_graph,
            "co_change_graph": co_change_graph,
            "file_types": file_types,
            "timeline": timeline,
            "risks": risks,
        }
        documentation = self.doc_generator.generate(str(repo_path), context=doc_context)

        return {
            "documentation": documentation,
            "hot_files": hot_files,
            "hot_folders": hot_folders,
            "file_tree": file_tree,
            "dependency_graph": dependency_graph,
            "co_change_graph": co_change_graph,
            "file_types": file_types,
            "timeline": timeline,
            "risks": risks,
            "analysis_meta": {
                "cache": "miss",
                "graph_engine": dependency_graph.get("stats", {}).get("engine", "unknown"),
                "repo_url": repo_url,
            },
        }

    def _build_hot_insights(self, repo: Repo) -> tuple[list[dict[str, Any]], list[dict[str, Any]], Counter[str]]:
        file_counter: Counter[str] = Counter()
        folder_counter: Counter[str] = Counter()

        for commit in repo.iter_commits(max_count=600):
            for changed_file in commit.stats.files.keys():
                if changed_file and not changed_file.startswith(".git/"):
                    normalized = self._normalize_path(changed_file)
                    file_counter[normalized] += 1
                    folder = str(Path(normalized).parent).replace("\\", "/")
                    folder_counter[folder if folder and folder != "." else "/"] += 1

        hot_files = [
            {"file": file_name, "changes": changes}
            for file_name, changes in file_counter.most_common(20)
        ]
        hot_folders = [
            {"folder": folder_name, "changes": changes}
            for folder_name, changes in folder_counter.most_common(15)
        ]
        return hot_files, hot_folders, file_counter

    def _build_file_tree(self, repo_path: Path) -> dict[str, Any]:
        def build_node(path: Path, depth: int = 0) -> dict[str, Any]:
            if path.is_file():
                try:
                    size_bytes = path.stat().st_size
                except Exception:
                    size_bytes = 0
                return {
                    "name": path.name,
                    "path": self._normalize_path(str(path.relative_to(repo_path))),
                    "type": "file",
                    "size_bytes": size_bytes,
                    "file_count": 1,
                    "depth": depth,
                }

            children: list[dict[str, Any]] = []
            file_count = 0
            total_size = 0

            for child in sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
                if child.name in SKIP_DIRS:
                    continue
                child_node = build_node(child, depth + 1)
                children.append(child_node)
                file_count += child_node.get("file_count", 0)
                total_size += child_node.get("size_bytes", 0)
                if len(children) >= 250:
                    break

            return {
                "name": path.name,
                "path": self._normalize_path(str(path.relative_to(repo_path))) if path != repo_path else "repo",
                "type": "directory",
                "children": children,
                "size_bytes": total_size,
                "file_count": file_count,
                "depth": depth,
            }

        return build_node(repo_path)

    def _build_dependency_graph(
        self,
        repo_path: Path,
        file_commit_counter: Counter[str],
    ) -> dict[str, Any]:
        source_files: list[Path] = []
        for file_path in repo_path.rglob("*"):
            if not file_path.is_file():
                continue
            if any(skip in file_path.parts for skip in SKIP_DIRS):
                continue
            if file_path.suffix.lower() not in SUPPORTED_IMPORT_FILES:
                continue
            source_files.append(file_path)

        try:
            if self.gitvizz_engine.available:
                raw_graph = self.gitvizz_engine.generate(repo_path, source_files)
                limited = self._limit_graph(raw_graph, file_commit_counter, max_nodes=100, engine="gitvizz")
                if limited["nodes"]:
                    return limited
        except Exception:
            pass

        fallback = self._fallback_dependency_graph(repo_path, source_files)
        return self._limit_graph(fallback, file_commit_counter, max_nodes=100, engine="fallback")

    def _fallback_dependency_graph(self, repo_path: Path, all_files: list[Path]) -> dict[str, Any]:
        graph = nx.DiGraph()
        rel_file_map = {
            self._normalize_path(str(path.relative_to(repo_path))): path
            for path in all_files
        }
        module_index = self._build_module_index(repo_path, all_files)

        for rel_path in rel_file_map.keys():
            graph.add_node(rel_path)

        for rel_path, abs_path in rel_file_map.items():
            imports = self._extract_imports(abs_path)
            for imp in imports:
                target = self._resolve_import_target(imp, abs_path, repo_path, module_index)
                if target and target in rel_file_map:
                    graph.add_edge(rel_path, target)

        return {
            "nodes": [{"id": node, "label": Path(node).name, "group": Path(node).suffix.replace(".", "") or "other"} for node in graph.nodes],
            "edges": [{"source": u, "target": v} for u, v in graph.edges],
            "metadata": {"engine": "fallback"},
        }

    def _limit_graph(
        self,
        graph_data: dict[str, Any],
        file_commit_counter: Counter[str],
        max_nodes: int,
        engine: str,
    ) -> dict[str, Any]:
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])
        if not nodes:
            return {"nodes": [], "edges": [], "stats": {"node_count": 0, "edge_count": 0, "density": 0.0, "engine": engine}}

        degree_counter: Counter[str] = Counter()
        for edge in edges:
            source = self._normalize_path(str(edge.get("source", "")))
            target = self._normalize_path(str(edge.get("target", "")))
            if not source or not target:
                continue
            degree_counter[source] += 1
            degree_counter[target] += 1

        scored = sorted(
            nodes,
            key=lambda node: (
                degree_counter.get(self._normalize_path(str(node.get("id", ""))), 0) * 2
                + file_commit_counter.get(self._normalize_path(str(node.get("id", ""))), 0)
            ),
            reverse=True,
        )
        selected_ids = {
            self._normalize_path(str(item.get("id", "")))
            for item in scored[:max_nodes]
            if item.get("id")
        }

        filtered_edges = []
        for edge in edges:
            source = self._normalize_path(str(edge.get("source", "")))
            target = self._normalize_path(str(edge.get("target", "")))
            if source in selected_ids and target in selected_ids:
                filtered_edges.append({"source": source, "target": target})

        graph = nx.DiGraph()
        for node in scored:
            node_id = self._normalize_path(str(node.get("id", "")))
            if node_id in selected_ids:
                graph.add_node(node_id, label=node.get("label") or Path(node_id).name, group=node.get("group") or "other")
        graph.add_edges_from((edge["source"], edge["target"]) for edge in filtered_edges)

        enriched_nodes = [
            {
                "id": node,
                "label": graph.nodes[node].get("label") or Path(node).name,
                "group": graph.nodes[node].get("group") or "other",
                "in_degree": graph.in_degree(node),
                "out_degree": graph.out_degree(node),
            }
            for node in graph.nodes
        ]

        return {
            "nodes": enriched_nodes,
            "edges": filtered_edges,
            "stats": {
                "node_count": graph.number_of_nodes(),
                "edge_count": graph.number_of_edges(),
                "density": round(nx.density(graph), 6) if graph.number_of_nodes() > 1 else 0.0,
                "engine": engine,
            },
        }

    def _build_co_change_graph(
        self,
        repo: Repo,
        file_commit_counter: Counter[str],
    ) -> dict[str, Any]:
        pair_counter: Counter[tuple[str, str]] = Counter()
        node_counter: Counter[str] = Counter()

        for commit in repo.iter_commits(max_count=800):
            files = {
                self._normalize_path(file)
                for file in commit.stats.files.keys()
                if file and not file.startswith(".git/")
            }
            files = {f for f in files if Path(f).suffix.lower() in SUPPORTED_IMPORT_FILES}
            if len(files) < 2:
                continue

            file_list = sorted(files)[:25]
            for file_name in file_list:
                node_counter[file_name] += 1
            for source, target in itertools.combinations(file_list, 2):
                pair_counter[(source, target)] += 1

        top_pairs = [pair for pair in pair_counter.items() if pair[1] >= 2]
        if not top_pairs:
            top_pairs = pair_counter.most_common(220)
        else:
            top_pairs = sorted(top_pairs, key=lambda item: item[1], reverse=True)[:220]

        graph = nx.Graph()
        for (source, target), weight in top_pairs:
            graph.add_edge(source, target, weight=weight)

        # Keep graph readable by prioritizing nodes with high co-change and churn activity.
        ranked_nodes = sorted(
            graph.nodes,
            key=lambda node: node_counter.get(node, 0) * 2 + file_commit_counter.get(node, 0),
            reverse=True,
        )[:100]
        selected = set(ranked_nodes)

        reduced = nx.Graph()
        for source, target, data in graph.edges(data=True):
            if source in selected and target in selected:
                reduced.add_edge(source, target, weight=int(data.get("weight", 1)))

        nodes = [
            {
                "id": node,
                "label": Path(node).name,
                "group": Path(node).suffix.replace(".", "") or "other",
                "co_change_degree": reduced.degree(node),
                "commit_frequency": file_commit_counter.get(node, 0),
            }
            for node in reduced.nodes
        ]
        edges = [
            {"source": source, "target": target, "weight": int(data.get("weight", 1))}
            for source, target, data in reduced.edges(data=True)
        ]

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "node_count": reduced.number_of_nodes(),
                "edge_count": reduced.number_of_edges(),
                "density": round(nx.density(reduced), 6) if reduced.number_of_nodes() > 1 else 0.0,
            },
        }

    def _build_file_type_distribution(self, repo_path: Path) -> dict[str, Any]:
        type_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".jsx": "JavaScript",
            ".ts": "TypeScript",
            ".tsx": "TypeScript",
            ".md": "Markdown",
            ".rst": "Markdown",
            ".json": "JSON",
            ".yml": "YAML",
            ".yaml": "YAML",
        }
        counts: Counter[str] = Counter()

        for file_path in repo_path.rglob("*"):
            if not file_path.is_file() or any(skip in file_path.parts for skip in SKIP_DIRS):
                continue
            file_type = type_map.get(file_path.suffix.lower(), "Other")
            counts[file_type] += 1

        total = sum(counts.values())
        by_type = [
            {
                "type": file_type,
                "count": count,
                "percentage": round((count / total) * 100, 2) if total else 0.0,
            }
            for file_type, count in counts.most_common()
        ]
        return {"total_files": total, "by_type": by_type}

    def _build_activity_timeline(self, repo: Repo) -> dict[str, Any]:
        buckets: Counter[str] = Counter()
        total_commits = 0
        for commit in repo.iter_commits(max_count=800):
            dt = datetime.fromtimestamp(commit.committed_date)
            bucket = dt.strftime("%Y-%m")
            buckets[bucket] += 1
            total_commits += 1

        points = [{"date": month, "commits": count} for month, count in sorted(buckets.items())]
        return {"points": points, "total_commits": total_commits}

    def _build_risk_panel(
        self,
        hot_files: list[dict[str, Any]],
        dependency_graph: dict[str, Any],
    ) -> list[dict[str, Any]]:
        hot_map = {item.get("file", ""): int(item.get("changes", 0)) for item in hot_files}
        nodes = dependency_graph.get("nodes", [])

        max_churn = max(hot_map.values()) if hot_map else 1
        max_degree = 1
        degree_map: dict[str, int] = {}
        for node in nodes:
            degree = int(node.get("in_degree", 0)) + int(node.get("out_degree", 0))
            degree_map[str(node.get("id", ""))] = degree
            max_degree = max(max_degree, degree)

        candidates = set(hot_map.keys()) | set(degree_map.keys())
        risks: list[dict[str, Any]] = []
        for file_name in candidates:
            churn = hot_map.get(file_name, 0)
            degree = degree_map.get(file_name, 0)
            churn_score = churn / max_churn if max_churn else 0.0
            dep_score = degree / max_degree if max_degree else 0.0
            score = round(churn_score * 0.6 + dep_score * 0.4, 3)

            reasons: list[str] = []
            if churn_score >= 0.5:
                reasons.append("High commit churn")
            if dep_score >= 0.5:
                reasons.append("High dependency centrality")
            if not reasons and score >= 0.35:
                reasons.append("Moderate combined risk")
            if score < 0.35:
                continue

            risks.append(
                {
                    "file": file_name,
                    "risk_score": score,
                    "changes": churn,
                    "dependency_degree": degree,
                    "reasons": reasons,
                }
            )

        return sorted(risks, key=lambda item: item["risk_score"], reverse=True)[:15]

    def _build_module_index(self, repo_path: Path, files: list[Path]) -> dict[str, str]:
        module_map: dict[str, str] = {}
        for file in files:
            rel = self._normalize_path(str(file.relative_to(repo_path)))
            no_ext = str(file.relative_to(repo_path).with_suffix(""))
            dot_mod = no_ext.replace("/", ".").replace("\\", ".")
            module_map[dot_mod] = rel
            module_map[file.stem] = rel
        return module_map

    def _extract_imports(self, file_path: Path) -> list[str]:
        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return []

        imports: set[str] = set()

        if file_path.suffix.lower() == ".py":
            for line in text.splitlines():
                line = line.strip()
                if line.startswith("import "):
                    chunk = line.replace("import ", "", 1)
                    for token in chunk.split(","):
                        mod = token.strip().split(" as ")[0].strip()
                        if mod:
                            imports.add(mod)
                elif line.startswith("from ") and " import " in line:
                    mod = line.split(" import ")[0].replace("from ", "", 1).strip()
                    if mod:
                        imports.add(mod)
        else:
            patterns = [
                r"import\\s+.*?from\\s+['\"]([^'\"]+)['\"]",
                r"import\\s+['\"]([^'\"]+)['\"]",
                r"require\\(['\"]([^'\"]+)['\"]\\)",
            ]
            for pattern in patterns:
                for match in re.findall(pattern, text):
                    imports.add(match.strip())

        return list(imports)

    def _resolve_import_target(
        self,
        module_name: str,
        source_file: Path,
        repo_path: Path,
        module_index: dict[str, str],
    ) -> str | None:
        cleaned = module_name.strip()
        if not cleaned or cleaned.startswith("@"):
            return None

        if cleaned in module_index:
            return module_index[cleaned]

        if cleaned.startswith("."):
            source_dir = source_file.parent
            candidate = (source_dir / cleaned).resolve()
            for suffix in [".py", ".js", ".jsx", ".ts", ".tsx"]:
                file_candidate = Path(str(candidate) + suffix)
                if file_candidate.exists() and repo_path in file_candidate.parents:
                    return self._normalize_path(str(file_candidate.relative_to(repo_path)))

                index_candidate = candidate / f"index{suffix}"
                if index_candidate.exists() and repo_path in index_candidate.parents:
                    return self._normalize_path(str(index_candidate.relative_to(repo_path)))

        # Try package/module path mapping for imports like a.b.c
        if cleaned in module_index:
            return module_index[cleaned]
        if cleaned.split(".")[0] in module_index:
            return module_index[cleaned.split(".")[0]]

        return None

    def _normalize_path(self, value: str) -> str:
        return value.replace("\\", "/").strip()
