<template>
  <ListView
    :class="$attrs.class"
    :columns="columns"
    :rows="rows"
    :options="{
      getRowRoute: (row) => ({ name: 'Lead', params: { leadId: row.name } }),
      selectable: options.selectable,
      showTooltip: options.showTooltip,
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
        <div v-if="column.key === '_assign'" class="flex items-center">
          <MultipleAvatar :avatars="item" size="sm" />
        </div>
        <ListRowItem v-else :item="item">
          <template #prefix>
            <div v-if="column.key === 'status'">
              <IndicatorIcon :class="item.color" />
            </div>
            <div v-else-if="column.key === 'lead_name'">
              <Avatar
                v-if="item.label"
                class="flex items-center"
                :image="item.image"
                :label="item.image_label"
                size="sm"
              />
            </div>
            <div v-else-if="column.key === 'organization'">
              <Avatar
                v-if="item.label"
                class="flex items-center"
                :image="item.logo"
                :label="item.label"
                size="sm"
              />
            </div>
            <div v-else-if="column.key === 'lead_owner'">
              <Avatar
                v-if="item.full_name"
                class="flex items-center"
                :image="item.user_image"
                :label="item.full_name"
                size="sm"
              />
            </div>
            <div v-else-if="column.key === 'mobile_no'">
              <PhoneIcon class="h-4 w-4" />
            </div>
          </template>
          <Tooltip
            :text="item.label"
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
          >
            {{ item.timeAgo }}
          </Tooltip>
          <div
            v-else-if="column.key === 'sla_status'"
            class="truncate text-base"
          >
            <Badge
              v-if="item.value"
              :variant="'subtle'"
              :theme="item.color"
              size="md"
              :label="item.value"
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
        <Dropdown
          v-if="bulkActions.length"
          :options="bulkActions(selections, unselectAll)"
        >
          <Button variant="ghost">
            <template #icon>
              <FeatherIcon name="more-horizontal" class="h-4 w-4" />
            </template>
          </Button>
        </Dropdown>
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
    doctype="CRM Lead"
    :selectedValues="selectedValues"
    @reload="list.reload()"
  />
</template>

<script setup>
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
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
  Dropdown,
  call,
  Tooltip,
} from 'frappe-ui'
import { setupBulkActions, createToast } from '@/utils'
import { globalStore } from '@/stores/global'
import { onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

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
      totalCount: 0,
      rowCount: 0,
    }),
  },
})

const emit = defineEmits(['loadMore', 'updatePageCount'])

const pageLengthCount = defineModel()
const list = defineModel('list')

const router = useRouter()

const { $dialog } = globalStore()

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

const customBulkActions = ref([])

function bulkActions(selections, unselectAll) {
  let actions = [
    {
      label: 'Edit',
      onClick: () => editValues(selections, unselectAll),
    },
  ]
  customBulkActions.value.forEach((action) => {
    actions.push({
      label: action.label,
      onClick: () =>
        action.onClick({
          list: list.value,
          selections,
          unselectAll,
          call,
          createToast,
          $dialog,
          router,
        }),
    })
  })
  return actions
}

onMounted(() => {
  if (!list.value?.data) return
  setupBulkActions(list.value.data)
  customBulkActions.value = list.value?.data?.bulkActions || []
})
</script>
