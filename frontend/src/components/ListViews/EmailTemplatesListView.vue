<template>
  <ListView
    :columns="columns"
    :rows="rows"
    :options="{
      onRowClick: (row) => emit('showEmailTemplate', row.name),
      selectable: options.selectable,
    }"
    row-key="name"
  >
    <ListHeader class="mx-5" />
    <ListRows id="list-rows">
      <ListRow
        class="mx-5"
        v-for="row in rows"
        :key="row.name"
        v-slot="{ column, item }"
        :row="row"
      >
        <ListRowItem :item="item">
          <!-- <template #prefix>

          </template> -->
          <div
            v-if="['modified', 'creation'].includes(column.key)"
            class="truncate text-base"
          >
            {{ item.timeAgo }}
          </div>
          <div v-else-if="column.key === 'status'" class="truncate text-base">
            <Badge
              :variant="'subtle'"
              :theme="item.color"
              size="md"
              :label="item.label"
            />
          </div>
          <div v-else-if="column.type === 'Check'">
            <FormControl
              type="checkbox"
              :modelValue="item"
              :disabled="true"
              class="text-gray-900"
            />
          </div>
        </ListRowItem>
      </ListRow>
    </ListRows>
    <ListSelectBanner>
      <template #actions="{ selections, unselectAll }">
        <Button
          theme="red"
          variant="subtle"
          label="Delete"
          @click="deleteEmailTemplate(selections, unselectAll)"
        />
      </template>
    </ListSelectBanner>
  </ListView>
  <ListFooter
    class="border-t px-5 py-2"
    v-model="pageLengthCount"
    :options="{
      rowCount: options.rowCount,
      totalCount: options.totalCount,
    }"
    @loadMore="emit('loadMore')"
  />
</template>
<script setup>
import { globalStore } from '@/stores/global'
import {
  ListView,
  ListHeader,
  ListRows,
  ListRow,
  ListSelectBanner,
  ListRowItem,
  ListFooter,
  call,
} from 'frappe-ui'
import { defineModel } from 'vue'

const props = defineProps({
  rows: {
    type: Array,
    required: true,
  },
  columns: {
    type: Array,
    required: true,
  },
  options: {
    type: Object,
    default: () => ({
      selectable: true,
      totalCount: 0,
      rowCount: 0,
    }),
  },
})

const emit = defineEmits(['loadMore', 'showEmailTemplate', 'reload'])

const pageLengthCount = defineModel()

const { $dialog } = globalStore()

function deleteEmailTemplate(selections, unselectAll) {
  let title = 'Delete email template'
  let message = 'Are you sure you want to delete this email template?'

  if (selections.size > 1) {
    title = 'Delete email templates'
    message = 'Are you sure you want to delete these email templates?'
  }

  $dialog({
    title: title,
    message: message,
    actions: [
      {
        label: 'Delete',
        theme: 'red',
        variant: 'solid',
        async onClick(close) {
          for (const selection of selections) {
            await call('frappe.client.delete', {
              doctype: 'Email Template',
              name: selection,
            })
          }
          close()
          unselectAll()
          emit('reload')
        },
      },
    ],
  })
}
</script>
