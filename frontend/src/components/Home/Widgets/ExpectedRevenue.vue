<template>
  <HomeEmptyState
    v-if="resource.data && !data.forecasting"
    compact
    class="rounded-4 border border-outline-gray-1 bg-surface-elevation-2 px-4 py-3"
    icon="lucide-trending-up"
  >
    {{ beforeCta }}
    <button
      v-if="isAdmin()"
      type="button"
      class="text-ink-gray-8 underline underline-offset-2 hover:text-ink-gray-9"
      @click="openForecastingSettings"
    >
      {{ __('Turn on forecasting') }}
    </button>
    <template v-else>{{ __('Turn on forecasting') }}</template>
    {{ afterCta }}
  </HomeEmptyState>
  <NumberCard
    v-else
    :title="__('Expected revenue')"
    :loading="!resource.data"
    :value="data.value ?? null"
    :prefix="data.currency"
    :format="formatCompactNumber"
    :delta="delta"
    deltaSuffix="%"
    :deltaFormat="formatPercentChange"
    :sparkline="{ data: data.value ? data.sparkline : [] }"
  >
    <template #title-suffix>
      <Tooltip
        :text="
          __(
            'Expected deal value of open deals × the win probability of their stage.',
          )
        "
      >
        <span class="lucide-info size-[0.9em] text-ink-gray-5" />
      </Tooltip>
    </template>
    <template #caption>
      <PeriodPicker
        :period="config?.period"
        :labels="comparisonLabels"
        @change="(period) => emit('update:config', { ...config, period })"
      />
    </template>
  </NumberCard>
</template>
<script setup>
import HomeEmptyState from '@/components/Home/HomeEmptyState.vue'
import PeriodPicker from '@/components/Home/PeriodPicker.vue'
import { useHomeWidget } from '@/composables/homeWidget'
import { activeSettingsPage, showSettings } from '@/composables/settings'
import { usersStore } from '@/stores/users'
import { formatPercentChange } from '@/utils/home'
import { formatCompactNumber } from '@/utils/numberFormat'
import { Tooltip } from 'frappe-ui'
import { NumberCard } from 'frappe-ui/charts'
import { computed } from 'vue'

const props = defineProps({ config: { type: Object, default: null } })

const emit = defineEmits(['update:config'])

const { isAdmin } = usersStore()

// The value is today's pipeline; the period only sets the window the change covers.
const comparisonLabels = {
  last_week: __('in the last week'),
  last_month: __('in the last month'),
  last_3_months: __('in the last 3 months'),
}

const resource = useHomeWidget('expected_revenue', () => props.config || {})
const data = computed(() => resource.data || {})

// A pipeline that grew from nothing has no percent change; show it as the top of the scale.
const delta = computed(() => {
  const { delta, value, sparkline } = data.value
  if (delta != null) return delta
  return sparkline?.[0] === 0 && value > 0 ? Infinity : null
})

const [beforeCta, afterCta] = __('{0} to see expected revenue.', []).split(
  '{0}',
)

function openForecastingSettings() {
  activeSettingsPage.value = 'Dashboard'
  showSettings.value = true
}
</script>
