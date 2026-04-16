import { useEffect, useRef } from 'react'
import * as d3 from 'd3'

export default function ActivityTimeline({ timeline }) {
  const chartRef = useRef(null)

  useEffect(() => {
    const points = timeline?.points || []
    if (!chartRef.current || points.length === 0) return

    const data = points.map((point) => ({ ...point, parsedDate: d3.timeParse('%Y-%m')(point.date) }))
    const width = chartRef.current.clientWidth
    const height = 300
    const margin = { top: 16, right: 16, bottom: 44, left: 54 }

    d3.select(chartRef.current).selectAll('*').remove()

    const svg = d3.select(chartRef.current).append('svg').attr('width', width).attr('height', height)

    const x = d3
      .scaleTime()
      .domain(d3.extent(data, (d) => d.parsedDate))
      .range([margin.left, width - margin.right])

    const y = d3
      .scaleLinear()
      .domain([0, d3.max(data, (d) => d.commits) || 0])
      .nice()
      .range([height - margin.bottom, margin.top])

    svg
      .append('g')
      .attr('transform', `translate(0,${height - margin.bottom})`)
      .call(d3.axisBottom(x).ticks(6).tickFormat(d3.timeFormat('%b %y')))
      .selectAll('text')
      .style('fill', '#cbd5e1')

    svg
      .append('g')
      .attr('transform', `translate(${margin.left},0)`)
      .call(d3.axisLeft(y).ticks(5))
      .selectAll('text')
      .style('fill', '#cbd5e1')

    const line = d3
      .line()
      .x((d) => x(d.parsedDate))
      .y((d) => y(d.commits))
      .curve(d3.curveMonotoneX)

    svg
      .append('path')
      .datum(data)
      .attr('fill', 'none')
      .attr('stroke', '#fb923c')
      .attr('stroke-width', 2.4)
      .attr('d', line)

    svg
      .append('g')
      .selectAll('circle')
      .data(data)
      .join('circle')
      .attr('cx', (d) => x(d.parsedDate))
      .attr('cy', (d) => y(d.commits))
      .attr('r', 3.5)
      .attr('fill', '#f97316')
  }, [timeline])

  return (
    <section className="card p-5">
      <h2 className="panel-title">Activity Timeline</h2>
      {timeline?.total_commits ? (
        <p className="mb-2 text-xs text-slate-400">Total commits sampled: {timeline.total_commits}</p>
      ) : (
        <p className="mb-2 text-xs text-slate-400">No commit timeline data available.</p>
      )}
      <div ref={chartRef} className="w-full" />
    </section>
  )
}
