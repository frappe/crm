<template>
  <Draggable
    :list="kanban?.data"
    item-key="column"
    class="flex sm:mx-5 mx-3 pb-3 overflow-x-auto gap-2"
  >
    <template #item="{ element: column }">
      <div class="flex flex-col gap-2 min-w-[268px]">
        <div>{{ column.column }}</div>
        <Draggable
          :list="column.data"
          group="fields"
          item-key="name"
          class="flex flex-col gap-2 overflow-y-auto h-full"
        >
          <template #item="{ element: fields }">
            <div class="p-3 rounded border bg-white">
              <div v-for="value in fields">
                <div>{{ value }}</div>
              </div>
            </div>
          </template>
        </Draggable>
      </div>
    </template>
  </Draggable>
</template>
<script setup>
import Draggable from 'vuedraggable'

const kanban = defineModel()
</script>
