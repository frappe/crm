<template>
  <ListView
    :class="$attrs.class"
    :columns="columns"
    :rows="rows"
    :options="{
      getRowRoute: (row) => ({ name: 'Lead', params: { leadId: row.name } }),
      selectable: true,
      showTooltip: false,
      resizeColumn: false,
    }"
    row-key="name"
  >
    <ListHeader class="mx-3 sm:mx-5">
      <ListHeaderItem
        v-for="column in columns"
        :key="column.key"
        :item="column"
      />
    </ListHeader>
    <ListRows
      v-slot="{ column, item }"
      class="mx-3 sm:mx-5"
      :rows="rows"
      doctype="CRM Lead"
    >
      <ListRowItem :item="item" :align="column.align" class="overflow-hidden">
        <template #prefix>
          <div v-if="column.key === 'lead_name'">
            <Avatar
              v-if="item.label"
              class="flex items-center"
              :image="item.image"
              :label="item.image_label"
              size="sm"
            />
          </div>
          <div v-else-if="column.key === 'status'">
            <IndicatorIcon :class="item.color" />
          </div>
        </template>
        <template #default="{ label }">
          <div v-if="column.key === 'modified'" class="truncate text-base">
            <Tooltip :text="item.label">
              <div>{{ item.timeAgo }}</div>
            </Tooltip>
          </div>
          <div
            v-else-if="column.key === '_assign'"
            class="flex items-center truncate"
          >
            <MultipleAvatar :avatars="item" size="xs" />
          </div>
          <div v-else-if="label" class="truncate text-base">
            {{ label }}
          </div>
        </template>
      </ListRowItem>
    </ListRows>
    <ListSelectBanner>
      <template #actions="{ selections, unselectAll }">
        <Button
          :label="__('Remove from Segment')"
          variant="ghost"
          @click="emit('removeLeads', selections, unselectAll)"
        />
      </template>
    </ListSelectBanner>
  </ListView>
  <ListFooter
    v-if="pageLengthCount"
    v-model="pageLengthCount"
    class="border-t px-3 py-2 sm:px-5"
    :options="{ rowCount: options.rowCount, totalCount: options.totalCount }"
    @loadMore="emit('loadMore')"
  />
</template>
<script setup>
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import ListRows from '@/components/ListViews/ListRows.vue'
import {
  Avatar,
  ListView,
  ListHeader,
  ListHeaderItem,
  ListSelectBanner,
  ListRowItem,
  ListFooter,
  Tooltip,
} from 'frappe-ui'
import { watch } from 'vue'

defineProps({
  rows: { type: Array, required: true },
  columns: { type: Array, required: true },
  options: {
    type: Object,
    default: () => ({ totalCount: 0, rowCount: 0 }),
  },
})

const emit = defineEmits(['loadMore', 'updatePageCount', 'removeLeads'])

const pageLengthCount = defineModel({ type: Number })

watch(pageLengthCount, (val, old_value) => {
  if (val === old_value) return
  emit('updatePageCount', val)
})
</script>
