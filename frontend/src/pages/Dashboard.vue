<template>
  <div class="flex flex-col h-full overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <ViewBreadcrumbs routeName="Dashboard" />
      </template>
    </LayoutHeader>

    <div class="p-5 pb-3 flex items-center gap-4">
      <Dropdown
        v-if="!showDatePicker"
        :options="options"
        class="form-control"
        v-model="preset"
        :placeholder="__('Select Range')"
        :button="{
          label: __(preset),
          class:
            '!w-full justify-start [&>span]:mr-auto [&>svg]:text-ink-gray-5 ',
          variant: 'outline',
          iconRight: 'chevron-down',
          iconLeft: 'calendar',
        }"
      >
        <template #prefix>
          <LucideCalendar class="size-4 text-ink-gray-5 mr-2" />
        </template>
      </Dropdown>
      <DateRangePicker
        v-else
        class="!w-48"
        ref="datePickerRef"
        :value="filters.period"
        variant="outline"
        :placeholder="__('Period')"
        @change="
          (v) =>
            updateFilter('period', v, () => {
              showDatePicker = false
              if (!v) {
                filters.period = getLastXDays()
                preset = 'Last 30 Days'
              } else {
                preset = formatter(v)
              }
            })
        "
        :formatter="formatRange"
      >
        <template #prefix>
          <LucideCalendar class="size-4 text-ink-gray-5 mr-2" />
        </template>
      </DateRangePicker>
      <Link
        v-if="isAdmin() || isManager()"
        class="form-control w-48"
        variant="outline"
        :value="filters.user && getUser(filters.user).full_name"
        doctype="User"
        :filters="{ name: ['in', users.data.crmUsers?.map((u) => u.name)] }"
        @change="(v) => updateFilter('user', v)"
        :placeholder="__('Sales User')"
        :hideMe="true"
      >
        <template #prefix>
          <UserAvatar
            v-if="filters.user"
            class="mr-2"
            :user="filters.user"
            size="sm"
          />
        </template>
        <template #item-prefix="{ option }">
          <UserAvatar class="mr-2" :user="option.value" size="sm" />
        </template>
        <template #item-label="{ option }">
          <Tooltip :text="option.value">
            <div class="cursor-pointer">
              {{ getUser(option.value).full_name }}
            </div>
          </Tooltip>
        </template>
      </Link>
    </div>

    <div class="p-5 pt-2 w-full overflow-y-scroll">
      <div class="transition-all animate-fade-in duration-300">
        <div
          v-if="!numberCards.loading"
          class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4"
        >
          <Tooltip
            v-for="(config, index) in numberCards.data"
            :text="config.tooltip"
          >
            <NumberChart
              :key="index"
              class="border rounded-md"
              :config="config"
            />
          </Tooltip>
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
  </div>
</template>

<script setup lang="ts">
import UserAvatar from '@/components/UserAvatar.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Link from '@/components/Controls/Link.vue'
import { usersStore } from '@/stores/users'
import { getLastXDays, formatter, formatRange } from '@/utils/dashboard'
import {
  AxisChart,
  DonutChart,
  NumberChart,
  usePageMeta,
  createResource,
  DateRangePicker,
  Dropdown,
  Tooltip,
} from 'frappe-ui'
import { ref, reactive, computed } from 'vue'

const { users, getUser, isManager, isAdmin } = usersStore()

const showDatePicker = ref(false)
const datePickerRef = ref(null)
const preset = ref('Last 30 Days')

const filters = reactive({
  period: getLastXDays(),
  user: null,
})

const fromDate = computed(() => {
  if (!filters.period) return null
  return filters.period.split(',')[0]
})

const toDate = computed(() => {
  if (!filters.period) return null
  return filters.period.split(',')[1]
})

function updateFilter(key: string, value: any, callback?: () => void) {
  filters[key] = value
  callback?.()
  reload()
}

function reload() {
  numberCards.reload()
  salesTrend.reload()
  funnelConversion.reload()
  dealsBySalesperson.reload()
  dealsByTerritory.reload()
  lostDealReasons.reload()
  forecastedRevenue.reload()
  dealsByStage.reload()
  leadsBySource.reload()
}

const options = computed(() => [
  {
    group: 'Presets',
    hideLabel: true,
    items: [
      {
        label: 'Last 7 Days',
        onClick: () => {
          preset.value = 'Last 7 Days'
          filters.period = getLastXDays(7)
          reload()
        },
      },
      {
        label: 'Last 30 Days',
        onClick: () => {
          preset.value = 'Last 30 Days'
          filters.period = getLastXDays(30)
          reload()
        },
      },
      {
        label: 'Last 60 Days',
        onClick: () => {
          preset.value = 'Last 60 Days'
          filters.period = getLastXDays(60)
          reload()
        },
      },
      {
        label: 'Last 90 Days',
        onClick: () => {
          preset.value = 'Last 90 Days'
          filters.period = getLastXDays(90)
          reload()
        },
      },
    ],
  },
  {
    label: 'Custom Range',
    onClick: () => {
      showDatePicker.value = true
      setTimeout(() => datePickerRef.value?.open(), 0)
      preset.value = 'Custom Range'
      filters.period = null // Reset period to allow custom date selection
    },
  },
])

const numberCards = createResource({
  url: 'crm.api.dashboard.get_number_card_data',
  cache: ['Analytics', 'NumberCards'],
  makeParams() {
    return {
      from_date: fromDate.value,
      to_date: toDate.value,
      user: filters.user,
    }
  },
  auto: true,
})

const salesTrend = createResource({
  url: 'crm.api.dashboard.get_sales_trend_data',
  cache: ['Analytics', 'SalesTrend'],
  makeParams() {
    return {
      from_date: fromDate.value,
      to_date: toDate.value,
      user: filters.user,
    }
  },
  auto: true,
  transform(data = []) {
    return {
      data: data,
      title: __('Sales Trend'),
      subtitle: __('Daily performance of leads, deals, and wins'),
      xAxis: {
        title: __('Date'),
        key: 'date',
        type: 'time' as const,
        timeGrain: 'day' as const,
      },
      yAxis: {
        title: __('Count'),
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
  makeParams() {
    return {
      from_date: fromDate.value,
      to_date: toDate.value,
      user: filters.user,
    }
  },
  auto: true,
  transform(data = []) {
    return {
      data: data,
      title: __('Funnel Conversion'),
      subtitle: __('Lead to deal conversion pipeline'),
      xAxis: {
        title: __('Stage'),
        key: 'stage',
        type: 'category' as const,
      },
      yAxis: {
        title: __('Count'),
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
  makeParams() {
    return {
      from_date: fromDate.value,
      to_date: toDate.value,
      user: filters.user,
    }
  },
  auto: true,
  transform(r = { data: [], currency_symbol: '$' }) {
    return {
      data: r.data || [],
      title: __('Deals by Salesperson'),
      subtitle: __('Number of deals and total value per salesperson'),
      xAxis: {
        title: __('Salesperson'),
        key: 'salesperson',
        type: 'category' as const,
      },
      yAxis: {
        title: __('Number of Deals'),
      },
      y2Axis: {
        title: __('Deal Value') + ` (${r.currency_symbol})`,
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
  makeParams() {
    return {
      from_date: fromDate.value,
      to_date: toDate.value,
      user: filters.user,
    }
  },
  auto: true,
  transform(r = { data: [], currency_symbol: '$' }) {
    return {
      data: r.data || [],
      title: __('Deals by Territory'),
      subtitle: __('Geographic distribution of deals and revenue'),
      xAxis: {
        title: __('Territory'),
        key: 'territory',
        type: 'category' as const,
      },
      yAxis: {
        title: __('Number of Deals'),
      },
      y2Axis: {
        title: __('Deal Value') + ` (${r.currency_symbol})`,
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
  makeParams() {
    return {
      from_date: fromDate.value,
      to_date: toDate.value,
      user: filters.user,
    }
  },
  auto: true,
  transform(data = []) {
    return {
      data: data,
      title: __('Lost Deal Reasons'),
      subtitle: __('Common reasons for losing deals'),
      xAxis: {
        title: __('Reason'),
        key: 'reason',
        type: 'category' as const,
      },
      yAxis: {
        title: __('Count'),
      },
      swapXY: true,
      series: [{ name: 'count', type: 'bar' as const }],
    }
  },
})

const forecastedRevenue = createResource({
  url: 'crm.api.dashboard.get_forecasted_revenue',
  cache: ['Analytics', 'ForecastedRevenue'],
  makeParams() {
    return { user: filters.user }
  },
  auto: true,
  transform(r = { data: [], currency_symbol: '$' }) {
    return {
      data: r.data || [],
      title: __('Revenue Forecast'),
      subtitle: __('Projected vs actual revenue based on deal probability'),
      xAxis: {
        title: __('Month'),
        key: 'month',
        type: 'time' as const,
        timeGrain: 'month' as const,
      },
      yAxis: {
        title: __('Revenue') + ` (${r.currency_symbol})`,
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
  makeParams() {
    return {
      from_date: fromDate.value,
      to_date: toDate.value,
      user: filters.user,
    }
  },
  auto: true,
  transform(data = []) {
    return {
      data: data,
      title: __('Deals by Stage'),
      subtitle: __('Current pipeline distribution'),
      categoryColumn: 'stage',
      valueColumn: 'count',
    }
  },
})

const leadsBySource = createResource({
  url: 'crm.api.dashboard.get_leads_by_source',
  cache: ['Analytics', 'LeadsBySource'],
  makeParams() {
    return {
      from_date: fromDate.value,
      to_date: toDate.value,
      user: filters.user,
    }
  },
  auto: true,
  transform(data = []) {
    return {
      data: data,
      title: __('Leads by Source'),
      subtitle: __('Lead generation channel analysis'),
      categoryColumn: 'source',
      valueColumn: 'count',
    }
  },
})

usePageMeta(() => {
  return { title: __('CRM Dashboard') }
})
</script>
