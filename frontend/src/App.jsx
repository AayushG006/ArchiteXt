import { useState } from 'react'
import { analyzeRepository } from './api/client'
import DocumentationPanel from './components/DocumentationPanel'
import HotFilesChart from './components/HotFilesChart'
import HotFoldersChart from './components/HotFoldersChart'
import FileTreePanel from './components/FileTreePanel'
import DependencyGraph from './components/DependencyGraph'
import FileTypeDistribution from './components/FileTypeDistribution'
import ActivityTimeline from './components/ActivityTimeline'
import RiskPanel from './components/RiskPanel'

const SAMPLE_REPO = 'https://github.com/fastapi/fastapi'

export default function App() {
  const [repoUrl, setRepoUrl] = useState(SAMPLE_REPO)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  const onAnalyze = async (event) => {
    event.preventDefault()
    setLoading(true)
    setError('')

    try {
      const data = await analyzeRepository(repoUrl)
      setResult(data)
    } catch (err) {
      setError(err.message || 'Analysis request failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen px-4 py-8 md:px-10">
      <div className="mx-auto max-w-7xl">
        <header className="mb-8 rounded-2xl border border-cyan-400/30 bg-slate-900/70 p-6 shadow-xl">
          <p className="title-text text-xs uppercase">ArchiteXt v2</p>
          <h1 className="mt-2 text-3xl font-bold text-white md:text-4xl">Codebase Intelligence Dashboard</h1>
          <p className="mt-2 max-w-2xl text-slate-300">
            Generate documentation and advanced repository visualizations from any public GitHub URL.
          </p>

          <form className="mt-5 flex flex-col gap-3 md:flex-row" onSubmit={onAnalyze}>
            <input
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              placeholder="https://github.com/owner/repository"
              className="w-full rounded-lg border border-slate-600 bg-slate-950/80 px-4 py-3 text-slate-100 outline-none focus:border-cyan-400"
            />
            <button
              type="submit"
              disabled={loading}
              className="rounded-lg bg-ember px-6 py-3 font-semibold text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {loading ? 'Analyzing...' : 'Analyze'}
            </button>
          </form>

          {error && (
            <div className="mt-3 rounded-lg border border-red-500/40 bg-red-950/30 px-4 py-2 text-sm text-red-300">
              {error}
            </div>
          )}
        </header>

        {result && (
          <div className="space-y-6">
            <DocumentationPanel documentation={result.documentation} />

            <DependencyGraph
              graph={result.dependency_graph}
              title="Dependency Graph"
              subtitle="GitVizz-powered structural graph with zoom, pan, and node highlighting."
            />

            <DependencyGraph
              graph={result.co_change_graph}
              title="Co-Change Graph"
              subtitle="Files that frequently change together in commits reveal hidden coupling."
              weightKey="weight"
            />

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 xl:grid-cols-3">
              <HotFilesChart data={result.hot_files} />
              <HotFoldersChart data={result.hot_folders} />
              <FileTypeDistribution data={result.file_types} />
              <ActivityTimeline timeline={result.timeline} />
              <FileTreePanel tree={result.file_tree} />
              <RiskPanel risks={result.risks} />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
