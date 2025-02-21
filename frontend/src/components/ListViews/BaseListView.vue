<template>
  <ListView
    :columns="columns"
    :rows="rows"
    :options="{
      getRowRoute: (row) => ({
        name: doctype,
        params: { [routeParamKey]: row.label?.name || row.name },
        query: { view: route.query.view, viewType: route.params.viewType },
      }),
      selectable: options.selectable,
      showTooltip: options.showTooltip,
      resizeColumn: options.resizeColumn,
    }"
    row-key="name"
  >
    <ListHeader
      class="sm:mx-5 mx-3"
      @columnWidthUpdated="emit('columnWidthUpdated')"
    >
      <ListHeaderItem
        v-for="column in columns"
        :key="column.key"
        :item="column"
        @columnWidthUpdated="emit('columnWidthUpdated', column)"
      >
        <Button
          v-if="column.key == '_liked_by'"
          variant="ghosted"
          class="!h-4"
          :class="isLikeFilterApplied ? 'fill-red-500' : 'fill-white'"
          @click="() => emit('applyLikeFilter')"
        >
          <HeartIcon class="h-4 w-4" />
        </Button>
      </ListHeaderItem>
    </ListHeader>
    <ListRows
      class="mx-3 sm:mx-5"
      :rows="rows"
      v-slot="{ idx, column, item }"
      :doctype="doctype"
    >
      <ListRowItem :item="item" :align="column.align">
        <template #prefix>
          <div v-if="column.key === nameField">
            <Avatar
              v-if="item"
              class="flex items-center"
              :image="item.logo"
              :label="typeof item === 'object' ? item.label.name || item.name : item"
              size="sm"
            />
          </div>
        </template>
        <template #default="{ label }">
          <div
            v-if="['modified', 'creation'].includes(column.key)"
            class="truncate text-base"
            @click="handleFilterClick(event, idx, column, item)"
          >
            <Tooltip :text="item.label">
              <div>{{ item.timeAgo }}</div>
            </Tooltip>
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
              variant="ghosted"
              :class="isLiked(item) ? 'fill-red-500' : 'fill-white'"
              @click.stop.prevent="handleLikeClick(row, item)"
            >
              <HeartIcon class="h-4 w-4" />
            </Button>
          </div>
          <div
            v-else
            class="truncate text-base"
            @click="handleFilterClick(event, idx, column, item)"
          >
            {{ item.label && typeof item.label === 'object' ? item.label.name : item.name }}
          </div>
        </template>
      </ListRowItem>
    </ListRows>
    <ListSelectBanner>
      <template #actions="{ selections, unselectAll }">
        <Dropdown
          :options="listBulkActionsRef.bulkActions(selections, unselectAll)"
        >
          <Button icon="more-horizontal" variant="ghost" />
        </Dropdown>
      </template>
    </ListSelectBanner>
  </ListView>
  <ListFooter
    class="border-t sm:px-5 px-3 py-2"
    v-model="pageLengthCount"
    :options="{
      rowCount: options.rowCount,
      totalCount: options.totalCount,
    }"
    @loadMore="emit('loadMore')"
  />
  <ListBulkActions
    ref="listBulkActionsRef"
    v-model="list"
    :doctype="doctype"
    :options="{
      hideAssign: true,
    }"
  />
</template>

<script setup>
import HeartIcon from '@/components/Icons/HeartIcon.vue'
import ListBulkActions from '@/components/ListBulkActions.vue'
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
  Dropdown,
  FormControl,
  Button,
} from 'frappe-ui'
import { sessionStore } from '@/stores/session'
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'

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
      showTooltip: true,
      resizeColumn: false,
      totalCount: 0,
      rowCount: 0,
    }),
  },
  doctype: {
    type: String,
    required: true,
  },
  routeParamKey: {
    type: String,
    required: true,
  },
  nameField: {
    type: String,
    required: true,
  },
})

const emit = defineEmits([
  'loadMore',
  'updatePageCount',
  'columnWidthUpdated',
  'applyFilter',
  'applyLikeFilter',
  'likeDoc',
])

const route = useRoute()
const pageLengthCount = defineModel()
const list = defineModel('list')
const listBulkActionsRef = ref(null)
const { user } = sessionStore()

const isLikeFilterApplied = computed(() => {
  return list.value.params?.filters?._liked_by ? true : false
})

function isLiked(item) {
  if (item) {
    let likedByMe = JSON.parse(item)
    return likedByMe.includes(user)
  }
  return false
}

function handleFilterClick(event, idx, column, item) {
  emit('applyFilter', {
    event,
    idx,
    column,
    item,
    firstColumn: props.columns[0],
  })
}

function handleLikeClick(row, item) {
  emit('likeDoc', { name: row.name, liked: isLiked(item) })
}

watch(pageLengthCount, (val, old_value) => {
  if (val === old_value) return
  emit('updatePageCount', val)
})

defineExpose({
  customListActions: computed(() => listBulkActionsRef.value?.customListActions),
})
</script> 