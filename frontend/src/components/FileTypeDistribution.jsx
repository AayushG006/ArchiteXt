import { useEffect, useRef } from 'react'
import * as d3 from 'd3'

export default function FileTypeDistribution({ data }) {
  const chartRef = useRef(null)

  useEffect(() => {
    const series = data?.by_type || []
    if (!chartRef.current || series.length === 0) return

    const width = chartRef.current.clientWidth
    const height = 320
    const radius = Math.min(width, height) / 2 - 24

    d3.select(chartRef.current).selectAll('*').remove()

    const svg = d3
      .select(chartRef.current)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .append('g')
      .attr('transform', `translate(${width / 2},${height / 2})`)

    const color = d3.scaleOrdinal().domain(series.map((d) => d.type)).range(d3.schemeSet2)

    const pie = d3.pie().value((d) => d.count).sort(null)
    const arcs = pie(series)

    const arc = d3.arc().innerRadius(radius * 0.5).outerRadius(radius)

    svg
      .selectAll('path')
      .data(arcs)
      .join('path')
      .attr('d', arc)
      .attr('fill', (d) => color(d.data.type))
      .attr('stroke', '#0f172a')
      .attr('stroke-width', 2)

    svg
      .selectAll('text')
      .data(arcs)
      .join('text')
      .attr('transform', (d) => `translate(${arc.centroid(d)})`)
      .attr('text-anchor', 'middle')
      .style('font-size', '10px')
      .style('fill', '#f8fafc')
      .text((d) => `${d.data.type} ${d.data.percentage}%`)
  }, [data])

  return (
    <section className="card p-5">
      <h2 className="panel-title">File Type Distribution</h2>
      {data?.total_files ? (
        <p className="mb-2 text-xs text-slate-400">Total files: {data.total_files}</p>
      ) : (
        <p className="mb-2 text-xs text-slate-400">No file type data available.</p>
      )}
      <div ref={chartRef} className="w-full" />
    </section>
  )
}
