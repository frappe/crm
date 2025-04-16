<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Prospects" />
    </template>
    <template #right-header>
      <CustomActions v-if="prospectsListView?.customListActions" :actions="prospectsListView.customListActions" />
      <Button v-if="hasCreateAccess" variant="solid" :label="__('Create')" @click="showProspectModal = true">
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
  <QuickEntryModal v-if="showQuickEntryModal" v-model="showQuickEntryModal" doctype="Prospect" />
</template>

<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import CustomActions from '@/components/CustomActions.vue'
import ProspectsIcon from '@/components/Icons/ProspectsIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ProspectsListView from '@/components/ListViews/ProspectsListView.vue'
import ProspectModal from '@/components/Modals/ProspectModal.vue'
import QuickEntryModal from '@/components/Modals/QuickEntryModal.vue'
import ViewControls from '@/components/ViewControls.vue'
import { usersStore } from '@/stores/users'
import { call } from 'frappe-ui'
import { dateFormat, dateTooltipFormat, timeAgo, website, formatNumberIntoCurrency } from '@/utils'
import { ref, reactive, computed, h } from 'vue'
import { useRoute } from 'vue-router'

const { getUser } = usersStore()

const prospectsListView = ref(null)
const showProspectModal = ref(false)
const showQuickEntryModal = ref(false)

const defaults = reactive({})
const route = useRoute()

let defaultOpenViews = JSON.parse(localStorage.getItem('defaultOpenViews'))
if (!defaultOpenViews) {
  defaultOpenViews = setDefaultViewCache()
  window.location.reload()
}

if (!route.params.viewType && defaultOpenViews.Prospect) {
  route.params.viewType = defaultOpenViews.Prospect
}

// Create button is shown only with write access
const hasCreateAccess = ref(false)

call('next_crm.api.doc.check_create_access', {
  doctype: 'Prospect',
}).then((show) => {
  hasCreateAccess.value = show
})

// prospects data is loaded in the ViewControls component
const prospects = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

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
    groupedRows.push(groupDetail)
  })

  return groupedRows || listRows
}

function parseRows(rows) {
  return rows.map((prospect) => {
    let _rows = {}
    prospects.value.data.rows.forEach((row) => {
      _rows[row] = prospect[row]

      if (row === 'website') {
        _rows[row] = website(prospect.website)
      } else if (row == 'prospect_amount') {
        _rows[row] = formatNumberIntoCurrency(prospect.prospect_amount, prospect.currency)
      } else if (row == 'prospect_owner') {
        _rows[row] = {
          label: prospect.prospect_owner && getUser(prospect.prospect_owner).full_name,
          ...(prospect.prospect_owner && getUser(prospect.prospect_owner)),
        }
      } else if (['modified', 'creation'].includes(row)) {
        _rows[row] = {
          label: dateFormat(prospect[row], dateTooltipFormat),
          timeAgo: __(timeAgo(prospect[row])),
        }
      }
    })
    return _rows
  })
}
</script>
