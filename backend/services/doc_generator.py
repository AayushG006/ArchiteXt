from __future__ import annotations

import re
from pathlib import Path
from typing import Any


class ExternalDocumentationGenerator:
    """Uses gitingest (open-source GitHub repo analyzer) to generate structured docs."""

    def __init__(self) -> None:
        self._ingest = None
        try:
            from gitingest import ingest

            self._ingest = ingest
        except Exception:
            self._ingest = None

    def generate(self, repo_path: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = context or {}
        summary = ""
        tree = ""
        content = ""

        if self._ingest:
            try:
                summary, tree, content = self._ingest(repo_path)
            except Exception:
                summary, tree, content = "", "", ""

        if not summary:
            summary = self._fallback_overview(repo_path)
        if not tree:
            tree = self._fallback_tree(repo_path)
        if not content:
            content = ""

        architecture = self._derive_architecture(tree, repo_path, context)
        key_insights = self._build_key_insights(context)
        critical_files = self._extract_critical_files(context)

        return {
            "overview": summary.strip() or "Repository analyzed successfully.",
            "tech_stack": self._extract_tech_stack(repo_path, content),
            "architecture": architecture,
            "architecture_summary_from_graph": self._graph_architecture_summary(context),
            "components": self._derive_components(repo_path),
            "improvements": self._suggest_improvements(repo_path),
            "key_insights": key_insights,
            "critical_files": critical_files,
        }

    def _fallback_overview(self, repo_path: str) -> str:
        path = Path(repo_path)
        readme = next(path.glob("README*"), None)
        if readme and readme.is_file():
            try:
                text = readme.read_text(encoding="utf-8", errors="ignore")
                excerpt = text[:1500].strip()
                if excerpt:
                    return excerpt
            except Exception:
                pass
        return f"Auto-generated overview for repository: {path.name}."

    def _fallback_tree(self, repo_path: str) -> str:
        root = Path(repo_path)
        lines: list[str] = []
        for item in sorted(root.rglob("*")):
            if ".git" in item.parts:
                continue
            rel = item.relative_to(root)
            depth = len(rel.parts) - 1
            prefix = "  " * max(depth, 0)
            name = rel.parts[-1]
            if item.is_dir():
                lines.append(f"{prefix}{name}/")
            else:
                lines.append(f"{prefix}{name}")
            if len(lines) >= 400:
                break
        return "\n".join(lines)

    def _extract_tech_stack(self, repo_path: str, content: str) -> list[str]:
        path = Path(repo_path)
        detected: set[str] = set()

        checks = {
            "Python": ["requirements.txt", "pyproject.toml", "setup.py"],
            "JavaScript": ["package.json"],
            "TypeScript": ["tsconfig.json"],
            "React": ["react"],
            "FastAPI": ["fastapi"],
            "Django": ["django"],
            "Flask": ["flask"],
            "TailwindCSS": ["tailwind"],
            "Docker": ["Dockerfile", "docker-compose.yml", "compose.yml"],
        }

        file_names = {p.name.lower() for p in path.glob("**/*") if p.is_file()}
        lower_content = content.lower()

        for tech, needles in checks.items():
            for needle in needles:
                needle_lower = needle.lower()
                if needle_lower in file_names or needle_lower in lower_content:
                    detected.add(tech)
                    break

        if not detected:
            detected.update(self._stack_from_extensions(path))

        return sorted(detected)

    def _stack_from_extensions(self, repo_path: Path) -> set[str]:
        ext_counts: dict[str, int] = {}
        for file in repo_path.rglob("*"):
            if not file.is_file() or ".git" in file.parts:
                continue
            ext = file.suffix.lower()
            ext_counts[ext] = ext_counts.get(ext, 0) + 1

        stack: set[str] = set()
        if ext_counts.get(".py", 0) > 0:
            stack.add("Python")
        if ext_counts.get(".js", 0) + ext_counts.get(".jsx", 0) > 0:
            stack.add("JavaScript")
        if ext_counts.get(".ts", 0) + ext_counts.get(".tsx", 0) > 0:
            stack.add("TypeScript")
        if ext_counts.get(".java", 0) > 0:
            stack.add("Java")
        if ext_counts.get(".go", 0) > 0:
            stack.add("Go")
        if ext_counts.get(".rs", 0) > 0:
            stack.add("Rust")
        return stack

    def _derive_architecture(self, tree: str, repo_path: str, context: dict[str, Any]) -> str:
        root = Path(repo_path)
        top_level = [p.name for p in root.iterdir() if p.is_dir() and p.name != ".git"]
        architecture = []
        if top_level:
            architecture.append("Top-level modules: " + ", ".join(sorted(top_level)[:15]))
        if tree:
            architecture.append("Repository structure was extracted using gitingest.")
        dep_stats = context.get("dependency_graph", {}).get("stats", {})
        if dep_stats:
            architecture.append(
                f"Dependency graph contains {dep_stats.get('node_count', 0)} files and {dep_stats.get('edge_count', 0)} edges."
            )
        architecture.append(
            "Architecture summary combines folder boundaries, entry files, and import relationships."
        )
        return " ".join(architecture)

    def _graph_architecture_summary(self, context: dict[str, Any]) -> str:
        dep_graph = context.get("dependency_graph", {})
        nodes = dep_graph.get("nodes", [])
        edges = dep_graph.get("edges", [])
        if not nodes:
            return "Dependency graph was unavailable for this repository."

        top_nodes = sorted(
            nodes,
            key=lambda n: (n.get("in_degree", 0) + n.get("out_degree", 0)),
            reverse=True,
        )[:5]
        anchors = ", ".join(n.get("id", "unknown") for n in top_nodes if n.get("id"))
        return (
            f"Graph-driven architecture indicates {len(nodes)} connected files and {len(edges)} dependency links. "
            f"Most connected files include: {anchors}."
        )

    def _extract_critical_files(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        risks = context.get("risks", [])
        critical: list[dict[str, Any]] = []
        for risk in risks[:8]:
            critical.append(
                {
                    "file": risk.get("file", "unknown"),
                    "score": risk.get("risk_score", 0),
                    "reasons": risk.get("reasons", []),
                }
            )
        return critical

    def _build_key_insights(self, context: dict[str, Any]) -> list[str]:
        hot_files = context.get("hot_files", [])
        hot_folders = context.get("hot_folders", [])
        timeline = context.get("timeline", {})
        dep_stats = context.get("dependency_graph", {}).get("stats", {})

        insights: list[str] = []
        if hot_files:
            insights.append(
                f"Most frequently changed file: {hot_files[0].get('file', 'unknown')} ({hot_files[0].get('changes', 0)} commits)."
            )
        if hot_folders:
            insights.append(
                f"Most active folder: {hot_folders[0].get('folder', 'unknown')} ({hot_folders[0].get('changes', 0)} commits)."
            )
        if timeline.get("points"):
            insights.append(f"Commit timeline includes {len(timeline.get('points', []))} time buckets.")
        if dep_stats:
            insights.append(
                f"Dependency map density is {dep_stats.get('density', 0.0)} across {dep_stats.get('node_count', 0)} files."
            )

        if not insights:
            insights.append("No advanced repository insights were generated for this run.")
        return insights

    def _derive_components(self, repo_path: str) -> list[dict[str, str]]:
        root = Path(repo_path)
        components: list[dict[str, str]] = []

        for directory in sorted(root.iterdir()):
            if not directory.is_dir() or directory.name.startswith("."):
                continue
            if directory.name in {"node_modules", "dist", "build", "venv", "__pycache__"}:
                continue

            file_count = 0
            for _ in directory.rglob("*"):
                file_count += 1
                if file_count > 5000:
                    break

            components.append(
                {
                    "name": directory.name,
                    "description": f"Directory '{directory.name}' containing ~{file_count} items.",
                }
            )
            if len(components) >= 20:
                break

        if not components:
            components.append(
                {
                    "name": "root",
                    "description": "Core repository files live at root level.",
                }
            )

        return components

    def _suggest_improvements(self, repo_path: str) -> list[str]:
        root = Path(repo_path)
        suggestions: list[str] = []

        has_tests = any("test" in p.name.lower() for p in root.rglob("*") if p.is_file())
        if not has_tests:
            suggestions.append("Add automated tests to improve reliability and regression safety.")

        has_ci = any(
            ".github" in p.parts and "workflows" in p.parts for p in root.rglob("*")
        )
        if not has_ci:
            suggestions.append("Set up CI pipelines for linting, testing, and build validation.")

        readme = next(root.glob("README*"), None)
        if not readme:
            suggestions.append("Create a comprehensive README with setup and architecture details.")

        if not any(root.glob("LICENSE*")):
            suggestions.append("Add a license file to clarify usage rights.")

        if not suggestions:
            suggestions.append("Current repository quality indicators are healthy; focus on incremental refactoring.")

        return suggestions
