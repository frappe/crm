<template>
  <ListView
    :columns="columns"
    :rows="rows"
    :options="{ resizeColumn: true }"
    row-key="name"
  >
    <ListHeader class="sm:mx-5 mx-3">
      <ListHeaderItem
        v-for="column in columns"
        :key="column.key"
        :item="column"
        @columnWidthUpdated="columnWidthUpdated()"
      >
        <Button
          v-if="column.key == '_liked_by'"
          variant="ghosted"
          class="!h-4"
          :class="isLikeFilterApplied ? 'fill-red-500' : 'fill-white'"
          @click="applyLikeFilter"
        >
          <HeartIcon class="h-4 w-4" />
        </Button>
      </ListHeaderItem>
    </ListHeader>
    <ListRows
      :rows="rows"
      v-slot="{ idx, column, item, row }"
      doctype="CRM Lead"
    >
      <div v-if="column.key === '_assign'" class="flex items-center">
        <MultipleAvatar
          :avatars="item"
          size="sm"
          @click="
            (event) =>
              applyFilter({
                event,
                idx,
                column,
                item,
                firstColumn: columns[0],
              })
          "
        />
      </div>
      <ListRowItem v-else :item="item" :align="column.align">
        <template #default="{ label }">
          <div
            v-if="['modified', 'creation'].includes(column.key)"
            class="truncate text-base"
            @click="
              (event) =>
                applyFilter({
                  event,
                  idx,
                  column,
                  item,
                  firstColumn: columns[0],
                })
            "
          >
            <Tooltip :text="formatDate(item)">
              <div>{{ timeAgo(item) }}</div>
            </Tooltip>
          </div>
          <div v-else-if="column.key === '_liked_by'">
            <Button
              v-if="column.key == '_liked_by'"
              variant="ghosted"
              :class="isLiked(item) ? 'fill-red-500' : 'fill-white'"
              @click.stop.prevent="
                () =>
                  likeDoc({
                    name: row.name,
                    liked: isLiked(item),
                  })
              "
            >
              <HeartIcon class="h-4 w-4" />
            </Button>
          </div>
          <div v-else-if="column.type === 'Check'">
            <FormControl
              type="checkbox"
              :modelValue="item"
              :disabled="true"
              class="text-ink-gray-9"
            />
          </div>
          <div
            v-else
            class="truncate text-base"
            @click="
              (event) =>
                applyFilter({
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
    <!-- <ListSelectBanner>
      <template #actions="{ selections, unselectAll }">
        <Dropdown
          :options="listBulkActionsRef.bulkActions(selections, unselectAll)"
        >
          <Button icon="more-horizontal" variant="ghost" />
        </Dropdown>
      </template>
    </ListSelectBanner> -->
  </ListView>
  <!-- <ListFooter
    v-if="pageLengthCount"
    class="border-t sm:px-5 px-3 py-2"
    v-model="pageLengthCount"
    :options="{
      rowCount: options.rowCount,
      totalCount: options.totalCount,
    }"
    @loadMore="emit('loadMore')"
  /> -->
  <!-- <ListBulkActions ref="listBulkActionsRef" v-model="list" :doctype="doctype" /> -->
</template>

<script setup>
import { useViews } from '@/stores/view'
import { sessionStore } from '@/stores/session'
import { formatDate, timeAgo } from '@/utils'
import { useControls } from './controls'
import { useList } from 'frappe-ui/data-fetching'
import {
  Avatar,
  ListView,
  ListHeader,
  ListHeaderItem,
  ListSelectBanner,
  ListRowItem,
  ListFooter,
  Dropdown,
  Tooltip,
  createResource,
} from 'frappe-ui'
import { computed, inject } from 'vue'

const doctype = inject('doctype')

const { currentView } = useViews(doctype)
const { updateColumns, updateFilter } = useControls()

const columns = computed(() => {
  return currentView.value?.columns || []
})

const rows = computed(() => {
  return list.data || []
})

const fields = () => currentView.value?.columns?.map((col) => col.key) || []

const filters = () => currentView.value?.filters || {}

const orderBy = () => currentView.value?.order_by || 'modified asc'

const list = useList({
  doctype: doctype,
  cacheKey: ['List', doctype],
  fields,
  filters,
  orderBy,
  start: 0,
  limit: 20,
  immediate: false,
})

function columnWidthUpdated() {
  updateColumns()
}

function applyFilter({ event, idx, column, item, firstColumn }) {
  let restrictedFieldtypes = ['Duration', 'Datetime', 'Time']
  if (restrictedFieldtypes.includes(column.type) || idx === 0) return
  if (idx === 1 && firstColumn.key == '_liked_by') return

  event.stopPropagation()
  event.preventDefault()

  let filters = currentView.value?.filters || {}

  let value = item.name || item.label || item

  if (value) {
    filters[column.key] = value
  } else {
    delete filters[column.key]
  }

  if (column.key == '_assign') {
    if (item.length > 1) {
      let target = event.target.closest('.user-avatar')
      if (target) {
        let name = target.getAttribute('data-name')
        filters['_assign'] = ['LIKE', `%${name}%`]
      }
    } else {
      filters['_assign'] = ['LIKE', `%${item[0].name}%`]
    }
  }
  updateFilter()
}

// Like functionality
const { user } = sessionStore()

const isLikeFilterApplied = computed(() => {
  return currentView.value?.filters?._liked_by ? true : false
})

function isLiked(item) {
  if (item) {
    let likedByMe = JSON.parse(item)
    return likedByMe.includes(user)
  }
}

function applyLikeFilter() {
  let filters = currentView.value?.filters || {}
  if (!filters._liked_by) {
    filters['_liked_by'] = ['LIKE', `%@me%`]
  } else {
    delete filters['_liked_by']
  }
  updateFilter()
}

function likeDoc({ name, liked }) {
  createResource({
    url: 'frappe.desk.like.toggle_like',
    params: { doctype: doctype, name: name, add: liked ? 'No' : 'Yes' },
    auto: true,
    onSuccess: () => list.reload(),
  })
}
</script>
