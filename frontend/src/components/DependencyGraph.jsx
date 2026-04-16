import { useEffect, useRef } from 'react'
import * as d3 from 'd3'

export default function DependencyGraph({ graph, title = 'Dependency Graph', subtitle = '', weightKey = null }) {
  const graphRef = useRef(null)

  useEffect(() => {
    if (!graphRef.current || !graph || !graph.nodes || graph.nodes.length === 0) return

    const container = graphRef.current
    const width = container.clientWidth
    const height = 420

    d3.select(container).selectAll('*').remove()

    const nodes = graph.nodes.slice(0, 150).map((d) => ({ ...d }))
    const nodeSet = new Set(nodes.map((n) => n.id))
    const links = (graph.edges || []).filter((e) => nodeSet.has(e.source) && nodeSet.has(e.target)).slice(0, 260)

    const svg = d3
      .select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .style('background', '#070d1b')
      .style('border-radius', '12px')

    const viewport = svg.append('g')
    svg.call(
      d3
        .zoom()
        .scaleExtent([0.3, 4])
        .on('zoom', (event) => {
          viewport.attr('transform', event.transform)
        })
    )

    const color = d3.scaleOrdinal(d3.schemeTableau10)

    const simulation = d3
      .forceSimulation(nodes)
      .force('link', d3.forceLink(links).id((d) => d.id).distance(44))
      .force('charge', d3.forceManyBody().strength(-110))
      .force('center', d3.forceCenter(width / 2, height / 2))

    const link = viewport
      .append('g')
      .attr('stroke', '#475569')
      .attr('stroke-opacity', 0.55)
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke-width', (d) => {
        if (!weightKey || !d[weightKey]) return 1.2
        return Math.min(5, 1 + Number(d[weightKey]) * 0.4)
      })

    const node = viewport
      .append('g')
      .selectAll('circle')
      .data(nodes)
      .join('circle')
      .attr('r', (d) => 5 + Math.min(d.out_degree || 0, 5))
      .attr('fill', (d) => color(d.group || 'other'))
      .call(
        d3
          .drag()
          .on('start', (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart()
            d.fx = d.x
            d.fy = d.y
          })
          .on('drag', (event, d) => {
            d.fx = event.x
            d.fy = event.y
          })
          .on('end', (event, d) => {
            if (!event.active) simulation.alphaTarget(0)
            d.fx = null
            d.fy = null
          })
      )

    node.append('title').text((d) => d.id)

    const labels = viewport
      .append('g')
      .selectAll('text')
      .data(nodes)
      .join('text')
      .text((d) => d.label)
      .style('font-size', '10px')
      .style('fill', '#e2e8f0')
      .style('pointer-events', 'none')

    const getNodeId = (value) => (typeof value === 'string' ? value : value.id)
    const updateHighlight = (focusId) => {
      if (!focusId) {
        node.attr('opacity', 1)
        labels.attr('opacity', 1)
        link.attr('stroke', '#475569').attr('stroke-opacity', 0.55)
        return
      }

      const neighbors = new Set([focusId])
      links.forEach((edge) => {
        const source = getNodeId(edge.source)
        const target = getNodeId(edge.target)
        if (source === focusId) neighbors.add(target)
        if (target === focusId) neighbors.add(source)
      })

      node.attr('opacity', (d) => (neighbors.has(d.id) ? 1 : 0.16))
      labels.attr('opacity', (d) => (neighbors.has(d.id) ? 1 : 0.1))
      link
        .attr('stroke', (d) => {
          const source = getNodeId(d.source)
          const target = getNodeId(d.target)
          return source === focusId || target === focusId ? '#22d3ee' : '#334155'
        })
        .attr('stroke-opacity', (d) => {
          const source = getNodeId(d.source)
          const target = getNodeId(d.target)
          return source === focusId || target === focusId ? 0.95 : 0.2
        })
    }

    let selectedNodeId = null
    node.on('click', (_, d) => {
      selectedNodeId = selectedNodeId === d.id ? null : d.id
      updateHighlight(selectedNodeId)
    })

    simulation.on('tick', () => {
      link
        .attr('x1', (d) => d.source.x)
        .attr('y1', (d) => d.source.y)
        .attr('x2', (d) => d.target.x)
        .attr('y2', (d) => d.target.y)

      node.attr('cx', (d) => d.x).attr('cy', (d) => d.y)

      labels.attr('x', (d) => d.x + 7).attr('y', (d) => d.y + 3)
    })

    return () => simulation.stop()
  }, [graph])

  return (
    <section className="card p-5">
      <h2 className="panel-title">{title}</h2>
      <p className="mb-2 text-xs text-slate-400">
        {subtitle || 'Drag nodes to inspect local clusters. Click a node to highlight its connections.'}
      </p>
      {graph?.stats && (
        <div className="mb-3 flex flex-wrap gap-2 text-xs text-slate-300">
          <span className="rounded border border-slate-600 px-2 py-1">Nodes: {graph.stats.node_count}</span>
          <span className="rounded border border-slate-600 px-2 py-1">Edges: {graph.stats.edge_count}</span>
          <span className="rounded border border-slate-600 px-2 py-1">Density: {graph.stats.density}</span>
          {graph.stats.engine && (
            <span className="rounded border border-slate-600 px-2 py-1">Engine: {graph.stats.engine}</span>
          )}
        </div>
      )}
      {(!graph || !graph.nodes || graph.nodes.length === 0) && (
        <p className="text-sm text-slate-300">No import dependency data available.</p>
      )}
      <div ref={graphRef} className="w-full" />
    </section>
  )
}
