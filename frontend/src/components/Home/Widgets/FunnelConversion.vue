<template>
  <HomeWidget
    :title="__('Sales funnel')"
    :subtitle="__('Leads and deals created in the period, by how far they got')"
    :resource="resource"
    :emptyText="__('No leads or deals in this period.')"
    emptyIcon="lucide-filter"
  >
    <template #tabs>
      <PeriodPicker
        :period="config?.period"
        @change="(period) => emit('update:config', { ...config, period })"
      />
    </template>
    <template #default="{ rows }">
      <div class="mx-2 flex min-h-0 flex-1">
        <FunnelChart :data="stages(rows)" category="stage" value="count" />
      </div>
    </template>
  </HomeWidget>
</template>
<script setup>
import HomeWidget from '@/components/Home/HomeWidget.vue'
import PeriodPicker from '@/components/Home/PeriodPicker.vue'
import { useHomeWidget } from '@/composables/homeWidget'
import { FunnelChart } from 'frappe-ui/charts'

const props = defineProps({ config: { type: Object, default: null } })

const emit = defineEmits(['update:config'])

const resource = useHomeWidget('funnel_conversion', () => props.config || {})

function stages(rows) {
  return rows.map((row) => ({ ...row, stage: __(row.stage) }))
}
</script>
