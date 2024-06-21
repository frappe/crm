<template>
  <Draggable
    v-if="columns"
    :list="columns"
    item-key="column"
    @end="updateColumn"
    class="flex sm:mx-2.5 mx-2 pb-3.5 overflow-x-auto"
  >
    <template #item="{ element: column }">
      <div
        class="flex flex-col gap-2.5 min-w-[268px] hover:bg-gray-100 rounded-lg p-2.5 transition-all duration-300 ease-in-out"
      >
        <div class="flex gap-2 items-center justify-between">
          <div class="flex items-center text-base">
            <NestedPopover>
              <template #target>
                <Button variant="ghost" size="sm" class="hover:!bg-gray-100">
                  <IndicatorIcon
                    :class="colorClasses(column.column.color, true)"
                  />
                </Button>
              </template>
              <template #body="{ close }">
                <div
                  class="flex flex-col gap-3 px-3 py-2.5 rounded-lg border border-gray-100 bg-white shadow-xl"
                >
                  <div class="flex gap-1">
                    <Button
                      :class="colorClasses(color)"
                      variant="ghost"
                      v-for="color in colors"
                      :key="color"
                      @click="() => (column.column.color = color)"
                    >
                      <IndicatorIcon />
                    </Button>
                  </div>
                  <div class="flex flex-row-reverse">
                    <Button
                      variant="solid"
                      :label="__('Apply')"
                      @click="updateColumn"
                    />
                  </div>
                </div>
              </template>
            </NestedPopover>
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
import NestedPopover from '@/components/NestedPopover.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import Draggable from 'vuedraggable'
import { computed } from 'vue'

const emit = defineEmits(['update'])

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

function updateColumn() {
  let _columns = []
  columns.value.forEach((col) => {
    _columns.push(col.column)
  })

  emit('update', { columns: _columns })
}

function colorClasses(color, onlyIcon = false) {
  let textColor = `!text-${color}-600`
  if (color == 'black') {
    textColor = '!text-gray-900'
  } else if (['gray', 'green'].includes(color)) {
    textColor = `!text-${color}-700`
  }

  let bgColor = `!bg-${color}-100 hover:!bg-${color}-200 active:!bg-${color}-300`

  return [textColor, onlyIcon ? '' : bgColor]
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
