export default function RiskPanel({ risks }) {
  const items = risks || []

  return (
    <section className="card p-5">
      <h2 className="panel-title">Risk Panel</h2>
      {items.length === 0 && <p className="text-sm text-slate-300">No high risk files identified.</p>}

      <div className="space-y-2">
        {items.map((risk) => (
          <div key={risk.file} className="rounded-lg border border-red-800/40 bg-red-950/20 p-3">
            <div className="flex items-center justify-between gap-2">
              <p className="truncate text-sm font-semibold text-slate-100">{risk.file}</p>
              <span className="rounded border border-red-400/40 px-2 py-0.5 text-xs text-red-200">
                score {risk.risk_score}
              </span>
            </div>
            <p className="mt-1 text-xs text-slate-300">
              changes {risk.changes} | dependency degree {risk.dependency_degree}
            </p>
            <p className="mt-1 text-xs text-red-200">{(risk.reasons || []).join(', ')}</p>
          </div>
        ))}
      </div>
    </section>
  )
}
