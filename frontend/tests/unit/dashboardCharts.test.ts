import { describe, expect, it } from 'vitest'
import {
  getAxisChartKind,
  toAxisChartProps,
  toDonutChartProps,
  toNumberCardProps,
} from '@/utils/dashboardCharts'

// Shapes below mirror what crm/api/dashboard.py resolvers return.
const salesTrend = {
  data: [{ date: '2026-09-01', leads: 2, deals: 1, won_deals: 0 }],
  title: 'Sales trend',
  subtitle: 'Daily performance of leads, deals, and wins',
  xAxis: { title: 'Date', key: 'date', type: 'time', timeGrain: 'day' },
  yAxis: { title: 'Count' },
  series: [
    { name: 'leads', type: 'line', showDataPoints: true },
    { name: 'deals', type: 'line', showDataPoints: true },
    { name: 'won_deals', type: 'line', showDataPoints: true },
  ],
}

const dealsByTerritory = {
  data: [{ territory: 'APAC', deals: 4, value: 500000 }],
  title: 'Deals by territory',
  xAxis: { title: 'Territory', key: 'territory', type: 'category' },
  yAxis: { title: 'Number of deals' },
  y2Axis: { title: 'Deal value ($)' },
  series: [
    { name: 'deals', type: 'bar' },
    { name: 'value', type: 'line', showDataPoints: true, axis: 'y2' },
  ],
}

const funnelConversion = {
  data: [
    { stage: 'Leads', count: 19 },
    { stage: 'Won', count: 9 },
  ],
  title: 'Funnel conversion',
  xAxis: { title: 'Stage', key: 'stage', type: 'category' },
  yAxis: { title: 'Count' },
  swapXY: true,
  series: [{ name: 'count', type: 'bar', echartOptions: { colorBy: 'data' } }],
}

describe('getAxisChartKind', () => {
  it('uses a line chart when every series is a line', () => {
    expect(getAxisChartKind(salesTrend)).toBe('line')
  })

  it('uses an area chart when every series is an area', () => {
    expect(getAxisChartKind({ series: [{ name: 'a', type: 'area' }] })).toBe(
      'area',
    )
  })

  it('uses a bar chart for bars and for bar-and-line combos', () => {
    expect(getAxisChartKind(funnelConversion)).toBe('bar')
    expect(getAxisChartKind(dealsByTerritory)).toBe('bar')
  })
})

describe('toAxisChartProps', () => {
  it('maps a multi-line time chart', () => {
    const props = toAxisChartProps(salesTrend)
    expect(props.x).toBe('date')
    expect(props.y).toEqual(['leads', 'deals', 'won_deals'])
    expect(props.y2).toBeUndefined()
    expect(props.xAxis).toMatchObject({ type: 'time', timeGrain: 'day' })
    expect(props.yAxis.title).toBe('Count')
    expect(props.seriesConfig.leads).toMatchObject({
      type: 'line',
      showDataPoints: true,
    })
    expect(props).not.toHaveProperty('horizontal')
  })

  it('puts y2 series on the second axis of a bar-and-line combo', () => {
    const props = toAxisChartProps(dealsByTerritory)
    expect(props.y).toEqual(['deals'])
    expect(props.y2).toEqual(['value'])
    expect(props.y2Axis.title).toBe('Deal value ($)')
    expect(props.seriesConfig.value.type).toBe('line')
  })

  it('turns swapXY into a horizontal bar chart and keeps series echartOptions', () => {
    const props = toAxisChartProps(funnelConversion)
    expect(props.horizontal).toBe(true)
    expect(props.seriesConfig.count.echartOptions).toEqual({ colorBy: 'data' })
  })

  it('maps axis bounds, series colors and dashed lines', () => {
    const props = toAxisChartProps({
      xAxis: { key: 'x' },
      yAxis: { yMin: 0, yMax: 10 },
      colors: ['#111', '#222'],
      series: [
        { name: 'a', type: 'line', lineType: 'dashed' },
        { name: 'b', type: 'line', color: '#333' },
      ],
    })
    expect(props.yAxis).toMatchObject({ min: 0, max: 10 })
    expect(props.seriesConfig.a).toMatchObject({ color: '#111', dashed: true })
    expect(props.seriesConfig.b).toMatchObject({ color: '#333' })
    expect(props.seriesConfig.b.dashed).toBeUndefined()
  })

  it('handles a config with no data or series', () => {
    const props = toAxisChartProps({})
    expect(props.data).toEqual([])
    expect(props.y).toEqual([])
  })
})

describe('toDonutChartProps', () => {
  it('maps category and value columns', () => {
    const props = toDonutChartProps({
      data: [{ source: 'Web Form', count: 7 }],
      title: 'Leads by source',
      categoryColumn: 'source',
      valueColumn: 'count',
    })
    expect(props).toMatchObject({
      title: 'Leads by source',
      category: 'source',
      value: 'count',
    })
    expect(props.data).toHaveLength(1)
  })
})

describe('toNumberCardProps', () => {
  it('passes number props through and drops the tooltip', () => {
    const props = toNumberCardProps({
      title: 'Avg. time to close a lead',
      tooltip: 'Average time taken',
      value: 18.18,
      suffix: ' days',
      delta: -5.7,
      deltaSuffix: ' days',
      negativeIsBetter: true,
    })
    expect(props).not.toHaveProperty('tooltip')
    expect(props).toMatchObject({
      value: 18.18,
      suffix: ' days',
      delta: -5.7,
      negativeIsBetter: true,
    })
  })
})
