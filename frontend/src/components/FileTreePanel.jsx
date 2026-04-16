import { useState } from 'react'

function formatBytes(size) {
  if (!size) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let value = size
  let unit = 0
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024
    unit += 1
  }
  return `${value.toFixed(unit === 0 ? 0 : 1)} ${units[unit]}`
}

function TreeNode({ node, depth = 0 }) {
  const [open, setOpen] = useState(depth < 1)

  if (node.type === 'file') {
    return (
      <div className="ml-4 py-0.5 text-sm text-slate-300">
        <span className="text-slate-500">-</span> {node.name}
        {typeof node.size_bytes === 'number' && (
          <span className="ml-2 text-xs text-slate-500">{formatBytes(node.size_bytes)}</span>
        )}
      </div>
    )
  }

  return (
    <div className="ml-1">
      <button
        onClick={() => setOpen((prev) => !prev)}
        className="mt-1 flex items-center gap-2 text-left text-sm font-medium text-cyan-100 hover:text-cyan-300"
      >
        <span className="w-4 text-cyan-400">{open ? 'v' : '>'}</span>
        <span>{node.name}</span>
        <span className="text-xs text-slate-500">
          {node.file_count || 0} files | {formatBytes(node.size_bytes || 0)} | depth {node.depth ?? depth}
        </span>
      </button>

      {open && node.children && (
        <div className="ml-4 border-l border-slate-700/50 pl-2">
          {node.children.map((child, idx) => (
            <TreeNode node={child} depth={depth + 1} key={`${child.name}-${idx}`} />
          ))}
        </div>
      )}
    </div>
  )
}

export default function FileTreePanel({ tree }) {
  return (
    <section className="card max-h-[560px] overflow-auto p-5">
      <h2 className="panel-title">File Structure Tree</h2>
      {tree ? <TreeNode node={tree} /> : <p className="text-sm text-slate-300">No structure available.</p>}
    </section>
  )
}
