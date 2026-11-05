<template>
  <Dropdown :options="options" align="end">
    <template #default>
      <Button
        variant="ghost"
        iconLeft="lucide-calendar-clock"
        :label="label"
        :class="
          selected
            ? '!bg-surface-gray-4 hover:bg-surface-gray-3'
            : '!text-ink-gray-5'
        "
      />
    </template>
  </Dropdown>
</template>
<script setup>
import { followUpPresets } from '@/utils/task'
import { Dropdown } from 'frappe-ui'
import { computed } from 'vue'

const presetKey = defineModel({ type: String, default: null })

const presets = followUpPresets()

const selected = computed(() =>
  presets.find((preset) => preset.key === presetKey.value),
)

const label = computed(() =>
  selected.value
    ? __('Follow up: {0}', [selected.value.label])
    : __('Follow up in…'),
)

const options = computed(() => {
  const groups = [
    {
      group: __('Follow up in'),
      hideLabel: true,
      options: presets.map((preset) => ({
        label: preset.label,
        onClick: () => (presetKey.value = preset.key),
      })),
    },
  ]
  if (selected.value) {
    groups.push({
      group: __('Clear'),
      hideLabel: true,
      options: [
        {
          label: __("Don't follow up"),
          onClick: () => (presetKey.value = null),
        },
      ],
    })
  }
  return groups
})
</script>
