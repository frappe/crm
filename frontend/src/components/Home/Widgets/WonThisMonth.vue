<template>
  <NumberCard
    :title="__('Won')"
    :loading="!resource.data"
    :value="data.value ?? null"
    :prefix="data.currency"
    :format="formatCompactNumber"
    :delta="data.delta"
    deltaSuffix="%"
    :deltaFormat="formatPercentChange"
    :sparkline="{ data: data.sparkline || [] }"
  >
    <template #caption>
      <PeriodPicker
        :period="config?.period"
        @change="(period) => emit('update:config', { ...config, period })"
      />
    </template>
  </NumberCard>
</template>
<script setup>
import PeriodPicker from '@/components/Home/PeriodPicker.vue'
import { useHomeWidget } from '@/composables/homeWidget'
import { formatPercentChange } from '@/utils/home'
import { formatCompactNumber } from '@/utils/numberFormat'
import { NumberCard } from 'frappe-ui/charts'
import { computed } from 'vue'

const props = defineProps({ config: { type: Object, default: null } })

const emit = defineEmits(['update:config'])

const resource = useHomeWidget('won_this_month', () => props.config || {})
const data = computed(() => resource.data || {})
</script>
