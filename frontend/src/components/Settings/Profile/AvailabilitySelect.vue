<template>
  <Select
    :model-value="availability.myStatus"
    :options="options"
    :placeholder="__('Set status')"
    @update:model-value="availability.setMyStatus"
  >
    <template #item-prefix="{ item }">
      <AvailabilityDot :status="item.value" />
    </template>
  </Select>
</template>

<script setup lang="ts">
import AvailabilityDot from '@/components/AvailabilityDot.vue'
import { availabilityStore } from '@/stores/availability'
import { Select } from 'frappe-ui'
import { computed } from 'vue'

const availability = availabilityStore()

const options = computed(() =>
  availability.enabledStatuses.map((status) => ({
    label: __(status.name),
    value: status.name,
  })),
)
</script>
