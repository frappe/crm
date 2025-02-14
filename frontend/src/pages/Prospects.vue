<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Prospects" />
    </template>
    <template #right-header>
      <CustomActions v-if="prospectsListView?.customListActions" :actions="prospectsListView.customListActions" />
      <Button variant="solid" :label="__('Create')" @click="showProspectModal = true">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </template>
  </LayoutHeader>
  <ViewControls
    ref="viewControls"
    v-model="prospects"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="Prospect"
    :options="{
      allowedViews: ['list', 'group_by'],
    }"
  />
  <ProspectsListView
    ref="prospectsListView"
    v-if="prospects.data && rows.length"
    v-model="prospects.data.page_length_count"
    v-model:list="prospects"
    :rows="rows"
    :columns="prospects.data.columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: prospects.data.row_count,
      totalCount: prospects.data.total_count,
    }"
    @loadMore="() => loadMore++"
    @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)"
    @applyFilter="(data) => viewControls.applyFilter(data)"
    @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
    @likeDoc="(data) => viewControls.likeDoc(data)"
  />
  <div v-else-if="prospects.data" class="flex h-full items-center justify-center">
    <div class="flex flex-col items-center gap-3 text-xl font-medium text-ink-gray-4">
      <ProspectsIcon class="h-10 w-10" />
      <span>{{ __('No {0} Found', [__('Prospects')]) }}</span>
      <Button :label="__('Create')" @click="showProspectModal = true">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </div>
  </div>
  <ProspectModal
    v-if="showProspectModal"
    v-model="showProspectModal"
    v-model:quickEntry="showQuickEntryModal"
    :defaults="defaults"
  />
  <NoteModal v-if="showNoteModal" v-model="showNoteModal" :note="note" doctype="Prospect" :doc="docname" />
  <ToDoModal v-if="showToDoModal" v-model="showToDoModal" :todo="todo" doctype="Prospect" :doc="docname" />
  <QuickEntryModal v-if="showQuickEntryModal" v-model="showQuickEntryModal" doctype="Prospect" />
</template>

<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import CustomActions from '@/components/CustomActions.vue'
import EmailAtIcon from '@/components/Icons/EmailAtIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import ToDoIcon from '@/components/Icons/ToDoIcon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import ProspectsIcon from '@/components/Icons/ProspectsIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ProspectsListView from '@/components/ListViews/ProspectsListView.vue'
import ProspectModal from '@/components/Modals/ProspectModal.vue'
import NoteModal from '@/components/Modals/NoteModal.vue'
import ToDoModal from '@/components/Modals/ToDoModal.vue'
import QuickEntryModal from '@/components/Modals/QuickEntryModal.vue'
import ViewControls from '@/components/ViewControls.vue'
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import { customersStore } from '@/stores/customers'
import { statusesStore } from '@/stores/statuses'
import { callEnabled } from '@/composables/settings'
import { dateFormat, dateTooltipFormat, timeAgo, website, formatNumberIntoCurrency, formatTime } from '@/utils'
import { Tooltip, Avatar, Dropdown } from 'frappe-ui'
import { useRoute } from 'vue-router'
import { ref, reactive, computed, h } from 'vue'

const { makeCall } = globalStore()
const { getUser } = usersStore()
const { getCustomer } = customersStore()
const { getDealStatus } = statusesStore()

const route = useRoute()

const prospectsListView = ref(null)
const showProspectModal = ref(false)
const showQuickEntryModal = ref(false)

const defaults = reactive({})

// prospects data is loaded in the ViewControls component
const prospects = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

function getRow(name, field) {
  function getValue(value) {
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      return value
    }
    return { label: value }
  }
  return getValue(rows.value?.find((row) => row.name == name)[field])
}

// Rows
const rows = computed(() => {
  if (!prospects.value?.data?.data) return []
  if (prospects.value.data.view_type === 'group_by') {
    if (!prospects.value?.data.group_by_field?.name) return []
    return getGroupedByRows(prospects.value?.data.data, prospects.value?.data.group_by_field)
  } else {
    return parseRows(prospects.value?.data.data)
  }
})

function getGroupedByRows(listRows, groupByField) {
  let groupedRows = []

  groupByField.options?.forEach((option) => {
    let filteredRows = []

    if (!option) {
      filteredRows = listRows.filter((row) => !row[groupByField.name])
    } else {
      filteredRows = listRows.filter((row) => row[groupByField.name] == option)
    }

    let groupDetail = {
      label: groupByField.label,
      group: option || __(' '),
      collapsed: false,
      rows: parseRows(filteredRows),
    }
    if (groupByField.name == 'status') {
      groupDetail.icon = () =>
        h(IndicatorIcon, {
          class: getDealStatus(option)?.iconColorClass,
        })
    }
    groupedRows.push(groupDetail)
  })

  return groupedRows || listRows
}

function parseRows(rows) {
  return rows.map((prospect) => {
    let _rows = {}
    prospects.value.data.rows.forEach((row) => {
      _rows[row] = prospect[row]

      if (row == 'customer') {
        _rows[row] = {
          label: prospect.customer,
          logo: getCustomer(prospect.customer)?.image,
        }
      } else if (row === 'website') {
        _rows[row] = website(prospect.website)
      } else if (row == 'prospect_amount') {
        _rows[row] = formatNumberIntoCurrency(prospect.prospect_amount, prospect.currency)
      } else if (row == 'status') {
        _rows[row] = {
          label: prospect.status,
          color: getDealStatus(prospect.status)?.iconColorClass,
        }
      } else if (row == 'sla_status') {
        let value = prospect.sla_status
        let tooltipText = value
        let color = prospect.sla_status == 'Failed' ? 'red' : prospect.sla_status == 'Fulfilled' ? 'green' : 'orange'
        if (value == 'First Response Due') {
          value = __(timeAgo(prospect.response_by))
          tooltipText = dateFormat(prospect.response_by, dateTooltipFormat)
          if (new Date(prospect.response_by) < new Date()) {
            color = 'red'
          }
        }
        _rows[row] = {
          label: tooltipText,
          value: value,
          color: color,
        }
      } else if (row == 'prospect_owner') {
        _rows[row] = {
          label: prospect.prospect_owner && getUser(prospect.prospect_owner).full_name,
          ...(prospect.prospect_owner && getUser(prospect.prospect_owner)),
        }
      } else if (row == '_assign') {
        let assignees = JSON.parse(prospect._assign || '[]')
        if (!assignees.length && prospect.prospect_owner) {
          assignees = [prospect.prospect_owner]
        }
        _rows[row] = assignees.map((user) => ({
          name: user,
          image: getUser(user).user_image,
          label: getUser(user).full_name,
        }))
      } else if (['modified', 'creation'].includes(row)) {
        _rows[row] = {
          label: dateFormat(prospect[row], dateTooltipFormat),
          timeAgo: __(timeAgo(prospect[row])),
        }
      } else if (['first_response_time', 'first_responded_on', 'response_by'].includes(row)) {
        let field = row == 'response_by' ? 'response_by' : 'first_responded_on'
        _rows[row] = {
          label: prospect[field] ? dateFormat(prospect[field], dateTooltipFormat) : '',
          timeAgo: prospect[row]
            ? row == 'first_response_time'
              ? formatTime(prospect[row])
              : __(timeAgo(prospect[row]))
            : '',
        }
      }
    })
    _rows['_email_count'] = prospect._email_count
    _rows['_note_count'] = prospect._note_count
    _rows['_todo_count'] = prospect._todo_count
    _rows['_comment_count'] = prospect._comment_count
    return _rows
  })
}

function onNewClick(column) {
  let column_field = prospects.value.params.column_field

  if (column_field) {
    defaults[column_field] = column.column.name
  }

  showProspectModal.value = true
}

function actions(itemName) {
  let mobile_no = getRow(itemName, 'mobile_no')?.label || ''
  let actions = [
    {
      icon: h(PhoneIcon, { class: 'h-4 w-4' }),
      label: __('Make a Call'),
      onClick: () => makeCall(mobile_no),
      condition: () => mobile_no && callEnabled.value,
    },
    {
      icon: h(NoteIcon, { class: 'h-4 w-4' }),
      label: __('New Note'),
      onClick: () => showNote(itemName),
    },
    {
      icon: h(ToDoIcon, { class: 'h-4 w-4' }),
      label: __('New ToDo'),
      onClick: () => showToDo(itemName),
    },
  ]
  return actions.filter((action) => (action.condition ? action.condition() : true))
}

const docname = ref('')
const showNoteModal = ref(false)
const note = ref({
  title: '',
  content: '',
})

function showNote(name) {
  docname.value = name
  showNoteModal.value = true
}

const showToDoModal = ref(false)
const todo = ref({
  title: '',
  description: '',
  allocated_to: '',
  date: '',
  priority: 'Low',
  status: 'Backlog',
})

function showToDo(name) {
  docname.value = name
  showToDoModal.value = true
}
</script>
