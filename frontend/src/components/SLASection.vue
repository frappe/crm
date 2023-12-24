<template>
  <div class="flex flex-col gap-1.5 border-b px-6 py-3">
    <div
      v-for="s in slaSection"
      :key="s.label"
      class="flex items-center gap-2 text-base leading-5"
    >
      <div class="w-[106px] text-sm text-gray-600">{{ s.label }}</div>
      <div class="grid min-h-[28px] items-center">
        <Tooltip
          v-if="s.tooltipText"
          :text="s.tooltipText"
          class="ml-2 cursor-pointer"
        >
          <Badge
            v-if="s.type == 'Badge'"
            class="-ml-1"
            :label="s.value"
            variant="subtle"
            :theme="s.color"
          />
          <div v-else>{{ s.value }}</div>
        </Tooltip>
        <Dropdown
          class="form-control"
          v-if="s.type == 'Select'"
          :options="s.options"
        >
          <template #default="{ open }">
            <Button :label="s.value">
              <template #suffix>
                <FeatherIcon
                  :name="open ? 'chevron-up' : 'chevron-down'"
                  class="h-4"
                />
              </template>
            </Button>
          </template>
        </Dropdown>
      </div>
    </div>
  </div>
</template>
<script setup>
import { Dropdown, Badge, Tooltip, FeatherIcon } from 'frappe-ui'
import { timeAgo, dateFormat, formatTime, dateTooltipFormat } from '@/utils'
import { statusesStore } from '@/stores/statuses'
import { computed, defineModel } from 'vue'

const data = defineModel()
const emit = defineEmits(['updateField'])

const { communicationStatuses } = statusesStore()

let slaSection = computed(() => {
  let sections = []
  if (data.value.first_responded_on) {
    sections.push({
      label: 'Fulfilled In',
      type: 'Duration',
      value: formatTime(data.value.first_response_time),
      tooltipText: dateFormat(data.value.first_responded_on, dateTooltipFormat),
    })
  }

  let status = data.value.sla_status
  let tooltipText = status
  let color =
    data.value.sla_status == 'Failed'
      ? 'red'
      : data.value.sla_status == 'Fulfilled'
      ? 'green'
      : 'orange'

  if (status == 'First Response Due') {
    status = timeAgo(data.value.response_by)
    tooltipText = dateFormat(data.value.response_by, dateTooltipFormat)
    if (new Date(data.value.response_by) < new Date()) {
      color = 'red'
    }
  }

  sections.push(
    ...[
      {
        label: 'SLA',
        type: 'Badge',
        value: status,
        tooltipText: tooltipText,
        color: color,
      },
      {
        label: 'Status',
        value: data.value.communication_status,
        type: 'Select',
        options: communicationStatuses.data?.map((status) => ({
          label: status.name,
          value: status.name,
          onClick: () =>
            emit('updateField', 'communication_status', status.name),
        })),
      },
    ]
  )
  return sections
})
</script>

<style scoped>
:deep(.form-control button) {
  border-color: transparent;
  background: white;
}
</style>