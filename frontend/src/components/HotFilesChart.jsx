import { useEffect, useRef } from 'react'
import * as d3 from 'd3'

export default function HotFilesChart({ data }) {
  const chartRef = useRef(null)

  useEffect(() => {
    if (!data || data.length === 0 || !chartRef.current) return

    const topData = data.slice(0, 12)
    const width = chartRef.current.clientWidth
    const height = 330
    const margin = { top: 16, right: 16, bottom: 80, left: 55 }

    d3.select(chartRef.current).selectAll('*').remove()

    const svg = d3
      .select(chartRef.current)
      .append('svg')
      .attr('width', width)
      .attr('height', height)

    const x = d3
      .scaleBand()
      .domain(topData.map((d) => d.file))
      .range([margin.left, width - margin.right])
      .padding(0.2)

    const y = d3
      .scaleLinear()
      .domain([0, d3.max(topData, (d) => d.changes) || 0])
      .nice()
      .range([height - margin.bottom, margin.top])

    svg
      .append('g')
      .attr('transform', `translate(0,${height - margin.bottom})`)
      .call(d3.axisBottom(x).tickFormat((name) => name.split('/').slice(-2).join('/')))
      .selectAll('text')
      .style('fill', '#cbd5e1')
      .attr('transform', 'rotate(-28)')
      .style('text-anchor', 'end')

    svg
      .append('g')
      .attr('transform', `translate(${margin.left},0)`)
      .call(d3.axisLeft(y).ticks(6))
      .selectAll('text')
      .style('fill', '#cbd5e1')

    svg
      .append('g')
      .selectAll('rect')
      .data(topData)
      .join('rect')
      .attr('x', (d) => x(d.file))
      .attr('y', (d) => y(d.changes))
      .attr('width', x.bandwidth())
      .attr('height', (d) => y(0) - y(d.changes))
      .attr('fill', '#00d4ff')
      .attr('rx', 6)

    svg
      .append('g')
      .selectAll('text')
      .data(topData)
      .join('text')
      .attr('x', (d) => (x(d.file) || 0) + x.bandwidth() / 2)
      .attr('y', (d) => y(d.changes) - 6)
      .attr('text-anchor', 'middle')
      .style('fill', '#e2e8f0')
      .style('font-size', '11px')
      .text((d) => d.changes)
  }, [data])

  return (
    <section className="card p-5">
      <h2 className="panel-title">Hot Files Chart</h2>
      {(!data || data.length === 0) && <p className="text-sm text-slate-300">No git history found.</p>}
      <div ref={chartRef} className="w-full" />
    </section>
  )
}
