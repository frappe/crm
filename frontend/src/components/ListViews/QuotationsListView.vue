<template>
  <ListView :class="$attrs.class" :columns="columns" :rows="rows" :options="{
    getRowRoute: (row) => ({
      name: 'Quotation',
      params: { quotationId: row.name },
      query: { view: route.query.view, viewType: route.params.viewType },
    }),
    selectable: options.selectable,
    showTooltip: options.showTooltip,
    resizeColumn: options.resizeColumn,
  }" row-key="name" @update:selections="(selections) => emit('selectionsChanged', selections)">
    <ListHeader class="sm:mx-5 mx-3" @columnWidthUpdated="emit('columnWidthUpdated')">
      <ListHeaderItem v-for="column in columns" :key="column.key" :item="column"
        @columnWidthUpdated="emit('columnWidthUpdated', column)">
        <Button v-if="column.key == '_liked_by'" variant="ghosted" class="!h-4"
          :class="isLikeFilterApplied ? 'fill-red-500' : 'fill-white'" @click="() => emit('applyLikeFilter')">
          <HeartIcon class="h-4 w-4" />
        </Button>
      </ListHeaderItem>
    </ListHeader>

    <ListRows v-slot="{ idx, column, item, row }" :rows="rows" doctype="CRM Quotation">
      <ListRowItem :item="item" :align="column.align" class="overflow-hidden">
        <template #prefix>
          <div v-if="column.key === '_assign'" class="flex items-center truncate">
            <MultipleAvatar :avatars="item" size="sm" @click="
              (event) =>
                emit('applyFilter', {
                  event,
                  idx,
                  column,
                  item,
                  firstColumn: columns[0],
                })
            " />
          </div>
          <div v-else-if="column.key === 'state'">
            <IndicatorIcon :class="getStateColor(item?.label || item)" />
          </div>
          <div v-else-if="column.key === '_liked_by'">
            <Button variant="ghosted" :class="isLiked(item) ? 'fill-red-500' : 'fill-white'" @click.stop.prevent="
              () => emit('likeDoc', { name: row.name, liked: isLiked(item) })
            ">
              <HeartIcon class="h-4 w-4" />
            </Button>
          </div>
        </template>

        <template #default="{ label }">
          <div v-if="['modified', 'creation'].includes(column.key)" class="truncate text-base" @click="
            (event) =>
              emit('applyFilter', {
                event,
                idx,
                column,
                item,
                firstColumn: columns[0],
              })
          ">
            <Tooltip :text="item?.label">
              <div>{{ item?.timeAgo }}</div>
            </Tooltip>
          </div>

          <div v-else-if="column.key === 'state'" class="truncate text-base">
            <Badge v-if="label" :variant="'subtle'" :theme="getStateTheme(label)" size="md" :label="label" @click="
              (event) =>
                emit('applyFilter', {
                  event,
                  idx,
                  column,
                  item,
                  firstColumn: columns[0],
                })
            " />
          </div>

          <div v-else-if="column.type === 'Check'">
            <FormControl type="checkbox" :modelValue="item" :disabled="true" class="text-ink-gray-9" />
          </div>

          <div v-else-if="label" class="truncate text-base" @click="
            (event) =>
              emit('applyFilter', {
                event,
                idx,
                column,
                item,
                firstColumn: columns[0],
              })
          ">
            {{ getLabel(label, column) }}
          </div>
        </template>
      </ListRowItem>
    </ListRows>

    <ListSelectBanner>
      <template #actions="{ selections, unselectAll }">
        <Dropdown :options="listBulkActionsRef.bulkActions(selections, unselectAll)">
          <Button icon="more-horizontal" variant="ghost" />
        </Dropdown>
      </template>
    </ListSelectBanner>
  </ListView>

  <ListFooter v-if="pageLengthCount" v-model="pageLengthCount" class="border-t sm:px-5 px-3 py-2" :options="{
    rowCount: options.rowCount,
    totalCount: options.totalCount,
  }" @loadMore="emit('loadMore')" />

  <ListBulkActions ref="listBulkActionsRef" v-model="list" doctype="CRM Quotation" />
</template>

<script setup>
import HeartIcon from '@/components/Icons/HeartIcon.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import ListBulkActions from '@/components/ListBulkActions.vue'
import ListRows from '@/components/ListViews/ListRows.vue'
import { isTranslatable, formatDuration } from '@/utils'
import {
  Badge,
  ListView,
  ListHeader,
  ListHeaderItem,
  ListRowItem,
  ListSelectBanner,
  ListFooter,
  Dropdown,
  Tooltip,
  FormControl,
} from 'frappe-ui'
import { sessionStore } from '@/stores/session'
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'

defineProps({
  rows: { type: Array, required: true },
  columns: { type: Array, required: true },
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
})

const emit = defineEmits([
  'loadMore',
  'updatePageCount',
  'columnWidthUpdated',
  'applyFilter',
  'applyLikeFilter',
  'likeDoc',
  'selectionsChanged',
])

const route = useRoute()

const pageLengthCount = defineModel({ type: Number })
const list = defineModel('list', { type: Object })

function getLabel(label, column) {
  if (column.type === 'Duration') return formatDuration(label)
  if (column.type === 'Currency') return label
  if (column.options && isTranslatable(column.options)) return __(label)
  return label
}

function getStateColor(state) {
  return {
    Draft: 'text-ink-gray-5',
    Created: 'text-ink-blue-3',
    Sent: 'text-ink-blue-3',
    Approved: 'text-ink-green-3',
    Rejected: 'text-ink-red-4',
    Expired: 'text-ink-orange-3',
  }[state] || 'text-ink-gray-5'
}

function getStateTheme(state) {
  return {
    Draft: 'gray',
    Created: 'blue',
    Sent: 'blue',
    Approved: 'green',
    Rejected: 'red',
    Expired: 'orange',
  }[state] || 'gray'
}

const isLikeFilterApplied = computed(() => {
  return list.value.params?.filters?._liked_by ? true : false
})

const { user } = sessionStore()

function isLiked(item) {
  if (item) {
    let likedByMe = JSON.parse(item)
    return likedByMe.includes(user)
  }
}

watch(pageLengthCount, (val, old_value) => {
  if (val === old_value) return
  emit('updatePageCount', val)
})

const listBulkActionsRef = ref(null)

defineExpose({
  customListActions: computed(
    () => listBulkActionsRef.value?.customListActions,
  ),
})
</script>