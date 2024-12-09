<template>
  <ListView
    :class="$attrs.class"
    :columns="columns"
    :rows="rows"
    :options="{
      getRowRoute: (row) => ({
        name: 'Lead',
        params: { leadId: row.name },
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
          @click="applyLikeFilter"
        >
          <HeartIcon class="h-4 w-4" />
        </Button>
      </ListHeaderItem>
    </ListHeader>
    <ListRows :rows="rows" v-slot="{ idx, column, item, row }">
      <div v-if="column.key === '_assign'" class="flex items-center">
        <MultipleAvatar
          :avatars="item || []"
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
      <ListRowItem v-else :item="item">
        <template #prefix>
          <div v-if="column.key === 'status'">
            <IndicatorIcon :class="item?.color || ''" />
          </div>
          <div v-else-if="column.key === 'lead_name'">
            <Avatar
              v-if="item?.label"
              class="flex items-center"
              :image="item?.image"
              :label="item?.image_label || item?.label"
              size="sm"
            />
          </div>
          <div v-else-if="column.key === 'organization'">
            <Avatar
              v-if="item"
              class="flex items-center"
              :image="item"
              :label="item"
              size="sm"
            />
          </div>
          <div v-else-if="column.key === 'lead_owner'">
            <Avatar
              v-if="item?.full_name"
              class="flex items-center"
              :image="item?.user_image"
              :label="item?.full_name"
              size="sm"
            />
          </div>
          <div v-else-if="column.key === 'mobile_no'">
            <PhoneIcon class="h-4 w-4" />
          </div>
        </template>
        <template #default="{ label }">
          <div
            v-if="
              [
                'modified',
                'creation',
                'first_response_time',
                'first_responded_on',
                'response_by',
              ].includes(column.key)
            "
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
            <Tooltip :text="item?.label || ''">
              <div>{{ item?.timeAgo || '' }}</div>
            </Tooltip>
          </div>
          <div v-else-if="column.key === '_liked_by'">
            <Button
              variant="ghosted"
              :class="isLiked(item) ? 'fill-red-500' : 'fill-white'"
              @click.stop.prevent="
                () =>
                  emit('likeDoc', {
                    name: row.name,
                    liked: isLiked(item),
                  })
              "
            >
              <HeartIcon class="h-4 w-4" />
            </Button>
          </div>
          <div
            v-else-if="column.key === 'sla_status'"
            class="truncate text-base"
          >
            <Badge
              v-if="item?.value"
              :variant="'subtle'"
              :theme="item?.color || 'gray'"
              size="md"
              :label="item?.value"
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
          <div v-else-if="column.type === 'Check'">
            <FormControl
              type="checkbox"
              :modelValue="item || false"
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
            {{ label || '' }}
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
    v-if="pageLengthCount"
    class="border-t sm:px-5 px-3 py-2"
    v-model="pageLengthCount"
    :options="{
      rowCount: options.rowCount,
      totalCount: options.totalCount,
    }"
    @loadMore="emit('loadMore')"
  />
  <ListBulkActions ref="listBulkActionsRef" v-model="list" doctype="CRM Lead" />
</template>

<script setup>
import HeartIcon from '@/components/Icons/HeartIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
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
  Dropdown,
  Tooltip,
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

const isLikeFilterApplied = computed(() => {
  return list.value.params?.filters?._liked_by ? true : false
})

const { user } = sessionStore()

function isLiked(item) {
  if (item) {
    let likedByMe = JSON.parse(item)
    return likedByMe.includes(user)
  }
  return false
}

function applyFilter({ event, idx, column, item, firstColumn }) {
  let restrictedFieldtypes = ['Duration', 'Datetime', 'Time']
  if (restrictedFieldtypes.includes(column.type) || idx === 0) return
  if (idx === 1 && firstColumn.key == '_liked_by') return
  if (!column.key) return

  event.stopPropagation()
  event.preventDefault()

  let filters = { ...list.value.params?.filters } || {}
  let value = item?.name || item?.label || item?.value || item || ''

  // Handle special cases
  if (column.key === '_assign') {
    if (Array.isArray(item) && item.length > 1) {
      let target = event.target.closest('.user-avatar')
      if (target) {
        let name = target.getAttribute('data-name')
        if (name) {
          filters['_assign'] = ['LIKE', `%${name}%`]
        }
      }
    } else if (Array.isArray(item) && item.length === 1) {
      filters['_assign'] = ['LIKE', `%${item[0].name}%`]
    }
  } else if (value) {
    if (column.type === 'Link' || column.type === 'Select') {
      filters[column.key] = value
    } else {
      filters[column.key] = ['LIKE', `%${value}%`]
    }
  } else {
    delete filters[column.key]
  }

  emit('applyFilter', filters)
}

function applyLikeFilter() {
  let filters = { ...list.value.params?.filters } || {}
  if (!filters._liked_by) {
    filters['_liked_by'] = ['LIKE', '%@me%']
  } else {
    delete filters['_liked_by']
  }

  // Remove any filters with undefined keys
  Object.keys(filters).forEach(key => {
    if (key === 'undefined' || key === undefined) {
      delete filters[key]
    }
  })

  emit('applyFilter', filters)
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
