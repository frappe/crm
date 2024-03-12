<template>
  <ListView
    :class="$attrs.class"
    :columns="columns"
    :rows="rows"
    :options="{
      getRowRoute: (row) => ({
        name: 'Contact',
        params: { contactId: row.name },
      }),
      selectable: options.selectable,
      showTooltip: options.showTooltip,
      resizeColumn: options.resizeColumn,
    }"
    row-key="name"
  >
    <ListHeader class="mx-5" @columnWidthUpdated="emit('columnWidthUpdated')" />
    <ListRows id="list-rows">
      <ListRow
        class="mx-5"
        v-for="row in rows"
        :key="row.name"
        v-slot="{ idx, column, item }"
        :row="row"
      >
        <ListRowItem
          :item="item"
          @click="(event) => emit('applyFilter', { event, idx, column, item })"
        >
          <template #prefix>
            <div v-if="column.key === 'full_name'">
              <Avatar
                v-if="item.label"
                class="flex items-center"
                :image="item.image"
                :label="item.image_label"
                size="sm"
              />
            </div>
            <div v-else-if="column.key === 'company_name'">
              <Avatar
                v-if="item.label"
                class="flex items-center"
                :image="item.logo"
                :label="item.label"
                size="sm"
              />
            </div>
            <div v-else-if="column.key === 'mobile_no'">
              <PhoneIcon class="h-4 w-4" />
            </div>
          </template>
          <Tooltip
            :text="item.label"
            v-if="['modified', 'creation'].includes(column.key)"
            class="truncate text-base"
          >
            {{ item.timeAgo }}
          </Tooltip>
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
          variant="subtle"
          label="Edit"
          @click="editValues(selections, unselectAll)"
        >
          <template #prefix>
            <EditIcon class="h-3 w-3" />
          </template>
        </Button>
      </template>
    </ListSelectBanner>
  </ListView>
  <ListFooter
    v-if="pageLengthCount"
    class="border-t px-5 py-2"
    v-model="pageLengthCount"
    :options="{
      rowCount: options.rowCount,
      totalCount: options.totalCount,
    }"
    @loadMore="emit('loadMore')"
  />
  <EditValueModal
    v-model="showEditModal"
    v-model:unselectAll="unselectAllAction"
    doctype="Contact"
    :selectedValues="selectedValues"
    @reload="emit('reload')"
  />
</template>
<script setup>
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import EditValueModal from '@/components/Modals/EditValueModal.vue'
import {
  Avatar,
  ListView,
  ListHeader,
  ListRows,
  ListRow,
  ListSelectBanner,
  ListRowItem,
  ListFooter,
  Tooltip,
} from 'frappe-ui'
import { ref, watch } from 'vue'

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
  'reload',
  'columnWidthUpdated',
  'applyFilter',
])

const pageLengthCount = defineModel()

watch(pageLengthCount, (val, old_value) => {
  if (val === old_value) return
  emit('updatePageCount', val)
})

const showEditModal = ref(false)
const selectedValues = ref([])
const unselectAllAction = ref(() => {})

function editValues(selections, unselectAll) {
  selectedValues.value = selections
  showEditModal.value = true
  unselectAllAction.value = unselectAll
}
</script>
