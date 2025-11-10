<template>
  <div class="flex flex-col gap-1.5 border-b sm:px-6 py-3 px-4">
    <div
      v-for="s in slaSection"
      :key="s.label"
      class="flex items-center gap-2 text-base leading-5"
    >
      <div class="sm:w-[106px] w-36 text-sm text-ink-gray-5">
        {{ __(s.label) }}
      </div>
      <div class="grid min-h-[28px] items-center">
        <Tooltip v-if="s.tooltipText" :text="__(s.tooltipText)">
          <div class="ml-2 cursor-pointer">
            <Badge
              v-if="s.type == 'Badge'"
              class="-ml-1"
              :label="s.value"
              variant="subtle"
              :theme="s.color"
            />
            <div v-else>{{ s.value }}</div>
          </div>
        </Tooltip>
        <Dropdown v-if="s.type == 'Select'" :options="s.options">
          <template #default="{ open }">
            <Button
              class="form-control bg-surface-white hover:bg-surface-white"
              :label="s.value"
              :iconRight="open ? 'chevron-up' : 'chevron-down'"
            />
          </template>
        </Dropdown>
      </div>
    </div>
  </div>
</template>
<script setup>
import { Dropdown, Tooltip } from 'frappe-ui'
import { timeAgo, formatDate, formatTime } from '@/utils'
import { statusesStore } from '@/stores/statuses'
import { capture } from '@/telemetry'
import { computed } from 'vue'

const data = defineModel()
const emit = defineEmits(['updateField'])

const { communicationStatuses } = statusesStore()

let slaSection = computed(() => {
  let sections = []
  let status = data.value.sla_status
  let tooltipText = status
  let color =
    data.value.sla_status == 'Failed'
      ? 'red'
      : data.value.sla_status == 'Fulfilled'
        ? 'green'
        : 'orange'

  if (status == 'First Response Due' || status == 'Rolling Response Due') {
    status = timeAgo(data.value.response_by)
    if (status == 'just now') {
      status = 'In less than a minute'
    }
    tooltipText = formatDate(data.value.response_by)
    if (new Date(data.value.response_by) < new Date()) {
      color = 'red'
      if (status == __('In less than a minute')) {
        status = 'less than a minute ago'
      }
    }
  } else if (['Fulfilled', 'Failed'].includes(status)) {
    status = __(status) + ' in ' + formatTime(data.value.last_response_time)
    tooltipText = formatDate(data.value.last_responded_on)
  }

  let responseType = 'First Response'

  if (
    Boolean(data.value.first_responded_on) &&
    Boolean(data.value.last_responded_on) &&
    (data.value.sla_status != 'Fulfilled' ||
      data.value.first_responded_on != data.value.last_responded_on)
  ) {
    responseType = 'Rolling Response'
  }

  sections.push(
    ...[
      {
        label: responseType,
        type: 'Badge',
        value: __(status),
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
          onClick: () => {
            capture('sla_status_change')
            emit('updateField', 'communication_status', status.name)
          },
        })),
      },
    ],
  )
  return sections
})
</script>

<style scoped>
:deep(.form-control button) {
  border-color: transparent;
  background: transparent;
}
</style>
