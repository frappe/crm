<template>
  <ListView
    :columns="columns"
    :rows="rows"
    :options="{
      getRowRoute: (row) => ({
        name: 'Call Log',
        params: { callLogId: row.name },
      }),
      selectable: options.selectable,
    }"
    row-key="name"
  >
    <ListHeader class="mx-5" />
    <ListRows>
      <ListRow
        class="mx-5"
        v-for="row in rows"
        :key="row.name"
        v-slot="{ column, item }"
        :row="row"
      >
        <ListRowItem :item="item">
          <template #prefix>
            <div v-if="['caller', 'receiver'].includes(column.key)">
              <Avatar
                v-if="item.label"
                class="flex items-center"
                :image="item.image"
                :label="item.label"
                size="sm"
              />
            </div>
            <div v-else-if="['type', 'duration'].includes(column.key)">
              <FeatherIcon :name="item.icon" class="h-3 w-3" />
            </div>
          </template>
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
    <ListSelectBanner />
  </ListView>
</template>
<script setup>
import {
  Avatar,
  ListView,
  ListHeader,
  ListRows,
  ListRow,
  ListSelectBanner,
  ListRowItem,
  FormControl,
  FeatherIcon,
  Badge,
} from 'frappe-ui'

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
    }),
  },
})
</script>
