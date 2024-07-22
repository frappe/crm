<template>
  <div class="mx-3 mt-2 h-full overflow-y-auto sm:mx-5" v-if="showGroupedRows">
    <div v-for="group in reactivieRows" :key="group.group">
      <ListGroupHeader :group="group">
        <div
          class="my-2 flex items-center gap-2 text-base font-medium text-gray-800"
        >
          <div>{{ __(group.label) }} -</div>
          <div class="flex items-center gap-1">
            <component v-if="group.icon" :is="group.icon" />
            <div v-if="group.group == ' '" class="text-gray-500">
              {{ __('Empty') }}
            </div>
            <div v-else>{{ group.group }}</div>
          </div>
        </div>
      </ListGroupHeader>
      <ListGroupRows :group="group" id="list-rows">
        <ListRow
          v-for="row in group.rows"
          :key="row.name"
          v-slot="{ idx, column, item }"
          :row="row"
        >
          <slot v-bind="{ idx, column, item, row }" />
        </ListRow>
      </ListGroupRows>
    </div>
  </div>
  <ListRows class="mx-3 sm:mx-5" v-else id="list-rows">
    <ListRow
      v-for="row in reactivieRows"
      :key="row.name"
      v-slot="{ idx, column, item }"
      :row="row"
    >
      <slot v-bind="{ idx, column, item, row }" />
    </ListRow>
  </ListRows>
</template>

<script setup>
import { ListRows, ListRow, ListGroupHeader, ListGroupRows } from 'frappe-ui'

import { ref, computed, watch } from 'vue'

const props = defineProps({
  rows: {
    type: Array,
    required: true,
  },
})

const reactivieRows = ref(props.rows)

watch(
  () => props.rows,
  (val) => (reactivieRows.value = val)
)

let showGroupedRows = computed(() => {
  return props.rows.every(
    (row) => row.group && row.rows && Array.isArray(row.rows)
  )
})
</script>
