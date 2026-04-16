import { useEffect, useRef } from 'react'
import * as d3 from 'd3'

export default function HotFoldersChart({ data }) {
  const chartRef = useRef(null)

  useEffect(() => {
    if (!chartRef.current || !data || data.length === 0) return

    const topData = data.slice(0, 10)
    const width = chartRef.current.clientWidth
    const height = 320
    const margin = { top: 12, right: 16, bottom: 20, left: 200 }

    d3.select(chartRef.current).selectAll('*').remove()
    const svg = d3.select(chartRef.current).append('svg').attr('width', width).attr('height', height)

    const y = d3
      .scaleBand()
      .domain(topData.map((d) => d.folder))
      .range([margin.top, height - margin.bottom])
      .padding(0.2)

    const x = d3
      .scaleLinear()
      .domain([0, d3.max(topData, (d) => d.changes) || 0])
      .nice()
      .range([margin.left, width - margin.right])

    svg
      .append('g')
      .attr('transform', `translate(0,${height - margin.bottom})`)
      .call(d3.axisBottom(x).ticks(6))
      .selectAll('text')
      .style('fill', '#cbd5e1')

    svg
      .append('g')
      .attr('transform', `translate(${margin.left},0)`)
      .call(d3.axisLeft(y).tickFormat((name) => (name.length > 34 ? `${name.slice(0, 34)}...` : name)))
      .selectAll('text')
      .style('fill', '#cbd5e1')

    svg
      .append('g')
      .selectAll('rect')
      .data(topData)
      .join('rect')
      .attr('x', margin.left)
      .attr('y', (d) => y(d.folder))
      .attr('width', (d) => x(d.changes) - margin.left)
      .attr('height', y.bandwidth())
      .attr('fill', '#22d3ee')
      .attr('rx', 6)

    svg
      .append('g')
      .selectAll('text')
      .data(topData)
      .join('text')
      .attr('x', (d) => x(d.changes) + 6)
      .attr('y', (d) => (y(d.folder) || 0) + y.bandwidth() / 2 + 4)
      .style('fill', '#e2e8f0')
      .style('font-size', '11px')
      .text((d) => d.changes)
  }, [data])

  return (
    <section className="card p-5">
      <h2 className="panel-title">Hot Folders</h2>
      {(!data || data.length === 0) && <p className="text-sm text-slate-300">No folder churn data available.</p>}
      <div ref={chartRef} className="w-full" />
    </section>
  )
}
