<template>
  <div class="flex sm:mx-5 mx-3 mb-3 overflow-hidden">
    <Draggable
      :list="columns.data"
      item-key="column"
      class="flex gap-2 overflow-x-auto"
    >
      <template #item="{ element: column }">
        <div class="flex flex-col gap-2 overflow-hidden min-w-[268px]">
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
  </div>
</template>
<script setup>
import { createResource } from 'frappe-ui'
import Draggable from 'vuedraggable'

const props = defineProps({
  doctype: { type: String, required: true },
  filters: { type: Object, required: true },
  column_field: { type: String, required: true },
  columns: { type: Object, required: true },
  rows: { type: Array, required: true },
})

function getParams() {
  return {
    doctype: props.doctype,
    filters: props.filters,
    order_by: 'modified',
    column_field: props.column_field,
    columns: props.columns,
    rows: props.rows,
  }
}

const columns = createResource({
  url: 'crm.api.doc.get_kanban_data',
  params: getParams(),
  cache: ['Kanban', props.doctype],
  auto: true,
  onSuccess(data) {
    data
  },
})
</script>
