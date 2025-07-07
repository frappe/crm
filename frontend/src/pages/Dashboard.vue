<template>
  <div class="flex flex-col h-full overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <ViewBreadcrumbs routeName="Dashboard" />
      </template>
    </LayoutHeader>

    <div class="p-5 w-full overflow-y-scroll">
      <div
        v-if="!numberCards.loading"
        class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4"
      >
        <NumberChart
          v-for="(config, index) in numberCards.data"
          :key="index"
          class="border rounded-md"
          :config="config"
        />
      </div>
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4">
        <div v-if="salesTrend.data" class="border rounded-md min-h-80">
          <AxisChart :config="salesTrend.data" />
        </div>
        <div v-if="forecastedRevenue.data" class="border rounded-md min-h-80">
          <AxisChart :config="forecastedRevenue.data" />
        </div>
        <div v-if="funnelConversion.data" class="border rounded-md min-h-80">
          <AxisChart :config="funnelConversion.data" />
        </div>
        <div v-if="lostDealReasons.data" class="border rounded-md">
          <AxisChart :config="lostDealReasons.data" />
        </div>
        <div v-if="dealsByTerritory.data" class="border rounded-md">
          <AxisChart :config="dealsByTerritory.data" />
        </div>
        <div v-if="dealsBySalesperson.data" class="border rounded-md">
          <AxisChart :config="dealsBySalesperson.data" />
        </div>
        <div v-if="dealsByStage.data" class="border rounded-md">
          <DonutChart :config="dealsByStage.data" />
        </div>
        <div v-if="leadsBySource.data" class="border rounded-md">
          <DonutChart :config="leadsBySource.data" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import {
  AxisChart,
  DonutChart,
  NumberChart,
  usePageMeta,
  createResource,
} from 'frappe-ui'

const numberCards = createResource({
  url: 'crm.api.dashboard.get_number_card_data',
  cache: ['Analytics', 'NumberCards'],
  auto: true,
})

const salesTrend = createResource({
  url: 'crm.api.dashboard.get_sales_trend_data',
  cache: ['Analytics', 'SalesTrend'],
  auto: true,
  transform(data = []) {
    return {
      data: data,
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
  },
})

const funnelConversion = createResource({
  url: 'crm.api.dashboard.get_funnel_conversion_data',
  cache: ['Analytics', 'FunnelConversion'],
  auto: true,
  transform(data = []) {
    return {
      data: data,
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
  },
})

const dealsBySalesperson = createResource({
  url: 'crm.api.dashboard.get_deals_by_salesperson',
  cache: ['Analytics', 'DealsBySalesperson'],
  auto: true,
  transform(data = []) {
    return {
      data: data,
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
  },
})

const dealsByTerritory = createResource({
  url: 'crm.api.dashboard.get_deals_by_territory',
  cache: ['Analytics', 'DealsByTerritory'],
  auto: true,
  transform(data = []) {
    return {
      data: data,
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
  },
})

const lostDealReasons = createResource({
  url: 'crm.api.dashboard.get_lost_deal_reasons',
  cache: ['Analytics', 'LostDealReasons'],
  auto: true,
  transform(data = []) {
    return {
      data: data,
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
      swapXY: true,
      series: [{ name: 'count', type: 'bar' as const }],
    }
  },
})

const forecastedRevenue = createResource({
  url: 'crm.api.dashboard.get_forecasted_revenue',
  cache: ['Analytics', 'ForecastedRevenue'],
  auto: true,
  transform(data = []) {
    return {
      data: data,
      title: 'Revenue Forecast',
      subtitle: 'Projected vs actual revenue based on deal probability',
      xAxis: {
        key: 'month',
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
  },
})

const dealsByStage = createResource({
  url: 'crm.api.dashboard.get_deals_by_stage',
  cache: ['Analytics', 'DealsByStage'],
  auto: true,
  transform(data = []) {
    return {
      data: data,
      title: 'Deals by Stage',
      subtitle: 'Current pipeline distribution',
      categoryColumn: 'stage',
      valueColumn: 'count',
    }
  },
})

const leadsBySource = createResource({
  url: 'crm.api.dashboard.get_leads_by_source',
  cache: ['Analytics', 'LeadsBySource'],
  auto: true,
  transform(data = []) {
    return {
      data: data,
      title: 'Leads by Source',
      subtitle: 'Lead generation channel analysis',
      categoryColumn: 'source',
      valueColumn: 'count',
    }
  },
})

usePageMeta(() => {
  return { title: 'CRM Dashboard' }
})
</script>
