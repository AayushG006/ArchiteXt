# ArchiteXt v2

ArchiteXt v2 is a full-stack GitHub repository intelligence system.

It accepts a GitHub URL, clones and analyzes the codebase, then returns:
- Structured project documentation
- Hot files chart data from git history
- Hot folders commit activity
- Interactive file structure tree data
- Dependency graph data (GitVizz-powered)
- Co-change graph data
- File type distribution
- Commit activity timeline
- Risk panel insights

## Stack

### Backend
- FastAPI
- GitPython
- networkx
- GitVizz core library (external GitHub integration)
- gitingest (external open-source GitHub analyzer)

### Frontend
- React (Vite)
- TailwindCSS
- D3.js

## Project Structure

- `backend/`
- `frontend/`

## Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Backend runs at: `http://127.0.0.1:8000`

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: `http://127.0.0.1:5173`

## API

### `POST /analyze`

Request:

```json
{
  "repo_url": "https://github.com/owner/repository"
}
```

Response:

```json
{
  "documentation": {
    "overview": "...",
    "tech_stack": ["..."],
    "architecture": "...",
    "architecture_summary_from_graph": "...",
    "components": [{ "name": "...", "description": "..." }],
    "improvements": ["..."],
    "key_insights": ["..."],
    "critical_files": [{ "file": "...", "score": 0.7, "reasons": ["..."] }]
  },
  "hot_files": [{ "file": "path/to/file", "changes": 12 }],
  "hot_folders": [{ "folder": "src/components", "changes": 30 }],
  "file_tree": {
    "name": "repo",
    "type": "directory",
    "file_count": 123,
    "size_bytes": 123456,
    "depth": 0,
    "children": []
  },
  "dependency_graph": {
    "nodes": [{ "id": "...", "label": "...", "group": "..." }],
    "edges": [{ "source": "...", "target": "..." }],
    "stats": { "node_count": 0, "edge_count": 0, "density": 0.0, "engine": "gitvizz" }
  },
  "co_change_graph": {
    "nodes": [{ "id": "...", "label": "...", "co_change_degree": 0 }],
    "edges": [{ "source": "...", "target": "...", "weight": 3 }],
    "stats": { "node_count": 0, "edge_count": 0, "density": 0.0 }
  },
  "file_types": {
    "total_files": 0,
    "by_type": [{ "type": "Python", "count": 0, "percentage": 0.0 }]
  },
  "timeline": {
    "points": [{ "date": "2026-01", "commits": 12 }],
    "total_commits": 200
  },
  "risks": [{ "file": "...", "risk_score": 0.71, "reasons": ["High commit churn"] }]
}
```

## External Open-Source Integration

ArchiteXt v2 integrates `gitingest` from GitHub:
- Repo: `https://github.com/coderamp-labs/gitingest`
- Usage: Python package integration inside backend documentation generation service

ArchiteXt v2 integrates `GitVizz` core library from GitHub:
- Repo: `https://github.com/adithya-s-k/GitVizz`
- Usage: GraphGenerator integration for dependency graph generation and repo visualization intelligence

## Notes

- Supports public GitHub repositories.
- Dependency graph is limited to top 100 files for interactive performance.
- Backend includes in-memory analysis caching for repeated repository requests.
- Co-change graph is computed from commit history and highlights hidden file coupling.
