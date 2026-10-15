<template>
  <ListView
    :columns="columns"
    :rows="rows"
    :options="{
      onRowClick: (row: { name: string }) => emit('openImport', row.name),
      selectable: options.selectable,
      showTooltip: options.showTooltip,
      resizeColumn: options.resizeColumn,
    }"
    row-key="name"
    v-bind="$attrs"
    @update:selections="
      (selections: Set<string>) => emit('selectionsChanged', selections)
    "
  >
    <ListHeader
      class="sm:mx-5 mx-3"
      @columnWidthUpdated="emit('columnWidthUpdated')"
    >
      <ListHeaderItem
        v-for="column in columns"
        :key="column.key"
        :item="column"
        @columnWidthUpdated="
          (e: ColumnWidthUpdate) => onColumnWidthUpdated(e, column)
        "
      >
        <Button
          v-if="column.key == '_liked_by'"
          variant="ghost"
          class="!h-4"
          @click="() => emit('applyLikeFilter')"
        >
          <HeartIcon
            class="h-4 w-4"
            :class="isLikeFilterApplied ? 'fill-red-500 text-red-500' : ''"
          />
        </Button>
      </ListHeaderItem>
    </ListHeader>
    <ListRows
      v-slot="{ idx, column, item, row }"
      class="mx-3 sm:mx-5"
      :rows="rows"
      doctype="Data Import"
    >
      <ListRowItem :item="item" :align="column.align" class="overflow-hidden">
        <template #default="{ label }">
          <div
            v-if="['modified', 'creation'].includes(column.key)"
            class="truncate text-base"
            @click="
              (event) =>
                emit('applyFilter', {
                  event,
                  idx,
                  column,
                  item,
                  firstColumn: columns[0],
                })
            "
          >
            <Tooltip :text="item.label">
              <div>{{ item.timeAgo }}</div>
            </Tooltip>
          </div>
          <div v-else-if="column.key === 'status'" class="truncate text-base">
            <Badge
              variant="subtle"
              :theme="item.color"
              size="md"
              :label="__(item.label)"
              @click="
                (event: Event) =>
                  emit('applyFilter', {
                    event,
                    idx,
                    column,
                    item,
                    firstColumn: columns[0],
                  })
              "
            />
          </div>
          <div v-else-if="column.type === 'Check'">
            <FormControl
              type="checkbox"
              :modelValue="item"
              :disabled="true"
              class="text-ink-gray-9"
            />
          </div>
          <div v-else-if="column.key === '_liked_by'">
            <Button
              variant="ghost"
              @click.stop.prevent="
                () =>
                  emit('likeDoc', {
                    name: (row as { name: string }).name,
                    liked: isLiked(item),
                  })
              "
            >
              <HeartIcon
                class="h-4 w-4"
                :class="isLiked(item) ? 'fill-red-500 text-red-500' : ''"
              />
            </Button>
          </div>
          <div
            v-else-if="label"
            class="truncate text-base"
            @click="
              (event) =>
                emit('applyFilter', {
                  event,
                  idx,
                  column,
                  item,
                  firstColumn: columns[0],
                })
            "
          >
            {{ label }}
          </div>
        </template>
      </ListRowItem>
    </ListRows>
    <ListSelectBanner>
      <template #actions="{ selections, unselectAll }">
        <Dropdown
          :options="listBulkActionsRef?.bulkActions(selections, unselectAll)"
        >
          <Button icon="lucide-more-horizontal" variant="ghost" />
        </Dropdown>
      </template>
    </ListSelectBanner>
  </ListView>
  <ListFooter
    v-model="pageLengthCount"
    class="border-t sm:px-5 px-3 py-2"
    :options="{
      rowCount: options.rowCount,
      totalCount: options.totalCount,
    }"
    @loadMore="emit('loadMore')"
  />
  <ListBulkActions
    ref="listBulkActionsRef"
    v-model="list"
    doctype="Data Import"
    :options="{
      hideEdit: true,
      hideAssign: true,
    }"
  />
</template>
<script setup lang="ts">
import HeartIcon from '@/components/Icons/HeartIcon.vue'
import ListBulkActions from '@/components/ListBulkActions.vue'
import ListRows from '@/components/ListViews/ListRows.vue'
import type { DataImportList, ListColumn } from '@/utils/dataImport'
import { Tooltip, Dropdown } from 'frappe-ui'
import {
  ListView,
  ListHeader,
  ListHeaderItem,
  ListSelectBanner,
  ListRowItem,
  ListFooter,
} from 'frappe-ui/experimental'
import { sessionStore } from '@/stores/session'
import { ref, computed, watch } from 'vue'

interface ColumnWidthUpdate {
  width: string
  save: boolean
}

interface FilterClick {
  event: Event
  idx: number
  column: ListColumn
  item: unknown
  firstColumn: ListColumn
}

withDefaults(
  defineProps<{
    rows: Record<string, unknown>[]
    columns: ListColumn[]
    options?: {
      selectable?: boolean
      showTooltip?: boolean
      resizeColumn?: boolean
      totalCount?: number
      rowCount?: number
    }
  }>(),
  {
    options: () => ({
      selectable: true,
      showTooltip: true,
      resizeColumn: false,
      totalCount: 0,
      rowCount: 0,
    }),
  },
)

const emit = defineEmits<{
  openImport: [name: string]
  loadMore: []
  updatePageCount: [count: number]
  columnWidthUpdated: [column?: ListColumn]
  applyFilter: [data: FilterClick]
  applyLikeFilter: []
  likeDoc: [data: { name: string; liked: boolean }]
  selectionsChanged: [selections: Set<string>]
}>()

const pageLengthCount = defineModel<number>({ required: true })
const list = defineModel<DataImportList>('list', { required: true })

function onColumnWidthUpdated(
  { width, save }: ColumnWidthUpdate,
  column: ListColumn,
) {
  column.width = width
  if (save) emit('columnWidthUpdated', column)
}

const isLikeFilterApplied = computed(() => {
  return list.value.params?.filters?._liked_by ? true : false
})

const { user } = sessionStore()

function isLiked(item: string | null): boolean {
  if (!item) return false
  let likedByMe: (string | null)[] = JSON.parse(item)
  return likedByMe.includes(user)
}

watch(pageLengthCount, (val, old_value) => {
  if (val === old_value) return
  emit('updatePageCount', val)
})

const listBulkActionsRef = ref<InstanceType<typeof ListBulkActions> | null>(
  null,
)

defineExpose({
  customListActions: computed(
    () => listBulkActionsRef.value?.customListActions,
  ),
})
</script>
