export default function DocumentationPanel({ documentation }) {
  if (!documentation) return null

  return (
    <section className="card p-5 lg:col-span-2">
      <h2 className="panel-title">Documentation</h2>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-slate-700/70 bg-slate-950/70 p-4">
          <h3 className="mb-2 text-sm font-semibold uppercase tracking-wider text-cyan-300">Overview</h3>
          <p className="whitespace-pre-wrap text-sm text-slate-200">{documentation.overview}</p>
        </div>

        <div className="rounded-lg border border-slate-700/70 bg-slate-950/70 p-4">
          <h3 className="mb-2 text-sm font-semibold uppercase tracking-wider text-cyan-300">Architecture</h3>
          <p className="text-sm text-slate-200">{documentation.architecture}</p>
          {documentation.architecture_summary_from_graph && (
            <p className="mt-2 text-xs text-slate-300">{documentation.architecture_summary_from_graph}</p>
          )}
        </div>

        <div className="rounded-lg border border-slate-700/70 bg-slate-950/70 p-4">
          <h3 className="mb-2 text-sm font-semibold uppercase tracking-wider text-cyan-300">Tech Stack</h3>
          <div className="flex flex-wrap gap-2">
            {(documentation.tech_stack || []).map((tech) => (
              <span
                key={tech}
                className="rounded-full border border-cyan-400/40 bg-cyan-900/30 px-3 py-1 text-xs text-cyan-100"
              >
                {tech}
              </span>
            ))}
          </div>
        </div>

        <div className="rounded-lg border border-slate-700/70 bg-slate-950/70 p-4">
          <h3 className="mb-2 text-sm font-semibold uppercase tracking-wider text-cyan-300">Components</h3>
          <ul className="space-y-2 text-sm text-slate-200">
            {(documentation.components || []).slice(0, 12).map((comp, idx) => (
              <li key={`${comp.name}-${idx}`}>
                <span className="font-semibold text-slate-100">{comp.name}:</span> {comp.description}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="mt-4 rounded-lg border border-slate-700/70 bg-slate-950/70 p-4">
        <h3 className="mb-2 text-sm font-semibold uppercase tracking-wider text-cyan-300">Improvements</h3>
        <ul className="list-disc space-y-1 pl-5 text-sm text-slate-200">
          {(documentation.improvements || []).map((item, idx) => (
            <li key={idx}>{item}</li>
          ))}
        </ul>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-slate-700/70 bg-slate-950/70 p-4">
          <h3 className="mb-2 text-sm font-semibold uppercase tracking-wider text-cyan-300">Key Insights</h3>
          <ul className="list-disc space-y-1 pl-5 text-sm text-slate-200">
            {(documentation.key_insights || []).map((item, idx) => (
              <li key={idx}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="rounded-lg border border-slate-700/70 bg-slate-950/70 p-4">
          <h3 className="mb-2 text-sm font-semibold uppercase tracking-wider text-cyan-300">Critical Files</h3>
          <ul className="space-y-2 text-sm text-slate-200">
            {(documentation.critical_files || []).slice(0, 8).map((item, idx) => (
              <li key={`${item.file}-${idx}`}>
                <span className="font-semibold text-slate-100">{item.file}</span>
                <span className="ml-2 text-xs text-red-200">score {item.score}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  )
}
