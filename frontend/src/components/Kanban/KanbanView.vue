<template>
  <Draggable
    v-if="columns"
    :list="columns"
    item-key="column"
    class="flex sm:mx-2.5 mx-2 pb-3.5 overflow-x-auto"
  >
    <template #item="{ element: column }">
      <div
        class="flex flex-col gap-2.5 min-w-[268px] hover:bg-gray-100 rounded-lg p-2.5 transition-all duration-300 ease-in-out"
      >
        <div class="flex gap-2 items-center justify-between">
          <div class="flex gap-2 items-center text-base py-1.5">
            <IndicatorIcon :class="colorClasses(column.column.color)" />
            <div>{{ column.column.name }}</div>
          </div>
          <div>
            <Button icon="plus" variant="ghost" />
          </div>
        </div>
        <Draggable
          :list="column.data"
          group="fields"
          item-key="name"
          class="flex flex-col gap-3.5 overflow-y-auto h-full"
        >
          <template #item="{ element: fields }">
            <div
              class="pt-3 px-3.5 pb-2.5 rounded-lg border bg-white text-base flex flex-col gap-2"
            >
              <div v-for="value in fields" :key="value">
                <div class="truncate">{{ value }}</div>
              </div>
            </div>
          </template>
        </Draggable>
      </div>
    </template>
  </Draggable>
</template>
<script setup>
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import Draggable from 'vuedraggable'
import { computed } from 'vue'

const kanban = defineModel()

const columns = computed(() => {
  if (!kanban.value?.data?.data || kanban.value.data.view_type != 'kanban')
    return []
  let _columns = kanban.value.data.data

  let has_color = _columns.some((column) => column.column?.color)
  if (!has_color) {
    _columns.forEach((column, i) => {
      column.column['color'] = colors[i % colors.length]
    })
  }
  return _columns
})

function colorClasses(color) {
  let textColor = `!text-${color}-600`
  if (color == 'black') {
    textColor = '!text-gray-900'
  } else if (['gray', 'green'].includes(color)) {
    textColor = `!text-${color}-700`
  }
  return [textColor]
}

const colors = [
  'gray',
  'blue',
  'green',
  'red',
  'pink',
  'orange',
  'amber',
  'yellow',
  'cyan',
  'teal',
  'violet',
  'purple',
  'black',
]
</script>
