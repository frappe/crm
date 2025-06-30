<template>
  <div class="flex flex-col h-full overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <ViewBreadcrumbs routeName="Dashboard" />
      </template>
    </LayoutHeader>

    <div class="p-5 w-full overflow-y-scroll">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <NumberChart
          v-for="(config, index) in numberCards"
          :key="index"
          class="border rounded-md"
          :config="config"
        />
      </div>
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4">
        <div class="border rounded-md min-h-80">
          <AxisChart :config="trendConfig" />
        </div>
        <div class="border rounded-md min-h-80">
          <AxisChart :config="forecastedRevenueConfig" />
        </div>
        <div class="border rounded-md min-h-80">
          <AxisChart :config="funnelConversionConfig" />
        </div>
        <div class="border rounded-md">
          <AxisChart :config="dealsBySalespersonConfig" />
        </div>
        <div class="border rounded-md">
          <AxisChart :config="territoriesBreakdownConfig" />
        </div>
        <div class="border rounded-md">
          <AxisChart :config="lostDealReasonsConfig" />
        </div>
        <div class="border rounded-md">
          <DonutChart :config="dealsByStage" />
        </div>
        <div class="border rounded-md">
          <DonutChart :config="leadsBySource" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import { AxisChart, DonutChart, NumberChart, usePageMeta } from 'frappe-ui'

const numberCards = [
  {
    title: 'Total Leads',
    value: 1234,
    delta: 15,
    deltaSuffix: '%',
  },
  {
    title: 'Total Deals',
    value: 567,
    delta: 8,
    deltaSuffix: '%',
  },
  {
    title: 'Won Deals',
    value: 234,
    delta: 12,
    deltaSuffix: '%',
  },
  {
    title: 'Avg Deal Value',
    value: 45,
    prefix: '$',
    suffix: 'K',
    delta: 5.2,
    deltaSuffix: '%',
  },
  {
    title: 'Avg Time to Close',
    value: 32,
    suffix: ' days',
    delta: -3,
    deltaSuffix: ' days',
    negativeIsBetter: true,
  },
]

const trendConfig = {
  data: [
    { date: new Date('2024-05-01'), leads: 45, deals: 23, won_deals: 12 },
    { date: new Date('2024-05-02'), leads: 52, deals: 28, won_deals: 15 },
    { date: new Date('2024-05-03'), leads: 38, deals: 19, won_deals: 8 },
    { date: new Date('2024-05-04'), leads: 61, deals: 32, won_deals: 18 },
    { date: new Date('2024-05-05'), leads: 47, deals: 25, won_deals: 14 },
    { date: new Date('2024-05-06'), leads: 55, deals: 29, won_deals: 16 },
    { date: new Date('2024-05-07'), leads: 43, deals: 22, won_deals: 11 },
    { date: new Date('2024-05-08'), leads: 58, deals: 31, won_deals: 17 },
    { date: new Date('2024-05-09'), leads: 49, deals: 26, won_deals: 13 },
    { date: new Date('2024-05-10'), leads: 62, deals: 33, won_deals: 19 },
    { date: new Date('2024-05-11'), leads: 44, deals: 21, won_deals: 10 },
    { date: new Date('2024-05-12'), leads: 51, deals: 27, won_deals: 15 },
    { date: new Date('2024-05-13'), leads: 56, deals: 30, won_deals: 16 },
    { date: new Date('2024-05-14'), leads: 48, deals: 24, won_deals: 12 },
    { date: new Date('2024-05-15'), leads: 59, deals: 32, won_deals: 18 },
    { date: new Date('2024-05-16'), leads: 53, deals: 28, won_deals: 14 },
    { date: new Date('2024-05-17'), leads: 46, deals: 23, won_deals: 11 },
  ],
  title: 'Sales Trend',
  subtitle: 'Daily performance of leads, deals, and wins',
  xAxis: {
    title: 'Date',
    key: 'date',
    type: 'time' as const,
    timeGrain: 'day' as const,
  },
  yAxis: {
    title: 'Count',
  },
  series: [
    { name: 'leads', type: 'line' as const, showDataPoints: true },
    { name: 'deals', type: 'line' as const, showDataPoints: true },
    { name: 'won_deals', type: 'line' as const, showDataPoints: true },
  ],
}

const funnelConversionConfig = {
  data: [
    { stage: 'Leads', count: 1234 },
    { stage: 'Qualified', count: 567 },
    { stage: 'Quotation', count: 345 },
    { stage: 'Ready to Close', count: 234 },
    { stage: 'Won', count: 156 },
  ],
  title: 'Funnel Conversion',
  subtitle: 'Lead to deal conversion pipeline',
  xAxis: {
    title: 'Stage',
    key: 'stage',
    type: 'category' as const,
  },
  yAxis: {
    title: 'Count',
  },
  swapXY: true,
  series: [
    {
      name: 'count',
      type: 'bar' as const,
      echartOptions: {
        colorBy: 'data',
      },
    },
  ],
}

const dealsBySalespersonConfig = {
  data: [
    { salesperson: 'John Smith', deals: 45, value: 2300000 },
    { salesperson: 'Sarah Johnson', deals: 38, value: 1950000 },
    { salesperson: 'Mike Chen', deals: 42, value: 2100000 },
    { salesperson: 'Emily Davis', deals: 35, value: 1750000 },
    { salesperson: 'Alex Wilson', deals: 40, value: 2000000 },
    { salesperson: 'Lisa Brown', deals: 33, value: 1650000 },
  ],
  title: 'Deals by Salesperson',
  subtitle: 'Number of deals and total value per salesperson',
  xAxis: {
    key: 'salesperson',
    type: 'category' as const,
    title: 'Salesperson',
  },
  yAxis: {
    title: 'Number of Deals',
  },
  y2Axis: {
    title: 'Deal Value ($)',
  },
  series: [
    { name: 'deals', type: 'bar' as const },
    {
      name: 'value',
      type: 'line' as const,
      showDataPoints: true,
      axis: 'y2' as const,
    },
  ],
}

const territoriesBreakdownConfig = {
  data: [
    { territory: 'North America', deals: 145, value: 7250000 },
    { territory: 'Europe', deals: 98, value: 4900000 },
    { territory: 'Asia Pacific', deals: 76, value: 3800000 },
    { territory: 'Latin America', deals: 45, value: 2250000 },
    { territory: 'Middle East', deals: 32, value: 1600000 },
  ],
  title: 'Deals by Territory',
  subtitle: 'Geographic distribution of deals and revenue',
  xAxis: {
    key: 'territory',
    type: 'category' as const,
    title: 'Territory',
  },
  yAxis: {
    title: 'Number of Deals',
  },
  y2Axis: {
    title: 'Deal Value ($)',
  },
  series: [
    { name: 'deals', type: 'bar' as const },
    {
      name: 'value',
      type: 'line' as const,
      showDataPoints: true,
      axis: 'y2' as const,
    },
  ],
}

const lostDealReasonsConfig = {
  data: [
    { reason: 'Price', count: 45 },
    { reason: 'Competition', count: 38 },
    { reason: 'Budget', count: 32 },
    { reason: 'Timing', count: 28 },
    { reason: 'Features', count: 25 },
    { reason: 'No Response', count: 22 },
    { reason: 'Other', count: 18 },
  ],
  title: 'Lost Deal Reasons',
  subtitle: 'Common reasons for losing deals',
  xAxis: {
    key: 'reason',
    type: 'category' as const,
    title: 'Reason',
  },
  yAxis: {
    title: 'Count',
  },
  series: [{ name: 'count', type: 'bar' as const }],
}

const forecastedRevenueConfig = {
  data: [
    { date: new Date('2024-06-01'), forecasted: 1200000, actual: 980000 },
    { date: new Date('2024-07-01'), forecasted: 1350000, actual: 1120000 },
    { date: new Date('2024-08-01'), forecasted: 1400000, actual: 1250000 },
    { date: new Date('2024-09-01'), forecasted: 1500000, actual: 1380000 },
    { date: new Date('2024-10-01'), forecasted: 1600000, actual: null },
    { date: new Date('2024-11-01'), forecasted: 1650000, actual: null },
    { date: new Date('2024-12-01'), forecasted: 1700000, actual: null },
  ],
  title: 'Revenue Forecast',
  subtitle: 'Projected vs actual revenue based on deal probability',
  xAxis: {
    key: 'date',
    type: 'time' as const,
    title: 'Month',
    timeGrain: 'month' as const,
  },
  yAxis: {
    title: 'Revenue ($)',
  },
  series: [
    { name: 'forecasted', type: 'line' as const, showDataPoints: true },
    { name: 'actual', type: 'line' as const, showDataPoints: true },
  ],
}

const dealsByStage = {
  data: [
    { stage: 'Qualification', count: 145 },
    { stage: 'Needs Analysis', count: 98 },
    { stage: 'Proposal', count: 76 },
    { stage: 'Negotiation', count: 45 },
    { stage: 'Closed Won', count: 234 },
    { stage: 'Closed Lost', count: 87 },
  ],
  title: 'Deals by Stage',
  subtitle: 'Current pipeline distribution',
  categoryColumn: 'stage',
  valueColumn: 'count',
}

const leadsBySource = {
  data: [
    { source: 'Website', count: 456 },
    { source: 'Referral', count: 298 },
    { source: 'Social Media', count: 187 },
    { source: 'Email Campaign', count: 156 },
    { source: 'Trade Show', count: 89 },
    { source: 'Cold Call', count: 48 },
  ],
  title: 'Leads by Source',
  subtitle: 'Lead generation channel analysis',
  categoryColumn: 'source',
  valueColumn: 'count',
}

usePageMeta(() => {
  return {
    title: 'CRM Dashboard',
  }
})
</script>
