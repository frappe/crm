<template>
  <div
    v-if="isMobileView"
    class="flex flex-col justify-between gap-2 sm:px-5 px-3 py-4"
  >
    <div class="flex flex-col gap-2">
      <div class="flex items-center justify-between gap-2 overflow-x-auto">
        <div class="flex gap-2">
          <Filter
            v-model="list"
            :doctype="doctype"
            :default_filters="filters"
            @update="updateFilter"
          />
          <GroupBy
            v-if="route.params.viewType === 'group_by'"
            v-model="list"
            :doctype="doctype"
            :hideLabel="isMobileView"
            @update="updateGroupBy"
          />
        </div>

        <div class="flex gap-2">
          <Button :label="__('Refresh')" @click="reload()" :loading="isLoading">
            <template #icon>
              <RefreshIcon class="h-4 w-4" />
            </template>
          </Button>
          <SortBy
            v-if="route.params.viewType !== 'kanban'"
            v-model="list"
            :doctype="doctype"
            @update="updateSort"
            :hideLabel="isMobileView"
          />
          <KanbanSettings
            v-if="route.params.viewType === 'kanban'"
            v-model="list"
            :doctype="doctype"
            @update="updateKanbanSettings"
          />
          <ColumnSettings
            v-else-if="!options.hideColumnsButton"
            v-model="list"
            :doctype="doctype"
            :hideLabel="isMobileView"
            @update="(isDefault) => updateColumns(isDefault)"
          />
        </div>
      </div>
      <div
        v-if="viewUpdated && route.query.view && (!view.public || isManager())"
        class="flex flex-row-reverse items-center gap-2 border-r pr-2"
      >
        <Button :label="__('Cancel')" @click="cancelChanges" />
        <Button :label="__('Save Changes')" @click="saveView" />
      </div>
    </div>
  </div>
  <div
    v-else-if="customizeQuickFilter"
    class="flex items-center justify-between gap-2 p-5"
  >
    <div class="flex flex-1 items-center overflow-hidden pl-1 gap-2">
      <FadedScrollableDiv
        class="flex items-center gap-2 overflow-x-auto -ml-1"
        orientation="horizontal"
      >
        <Draggable
          class="flex gap-2"
          :list="newQuickFilters"
          group="filters"
          item-key="fieldname"
        >
          <template #item="{ element: filter }">
            <Button class="group whitespace-nowrap cursor-grab">
              <template #default>
                <Tooltip :text="filter.fieldname">
                  <span>{{ filter.label }}</span>
                </Tooltip>
              </template>
              <template #suffix>
                <FeatherIcon
                  class="h-3.5 cursor-pointer group-hover:flex hidden"
                  name="x"
                  @click.stop="removeQuickFilter(filter)"
                />
              </template>
            </Button>
          </template>
        </Draggable>
      </FadedScrollableDiv>
      <Autocomplete
        value=""
        :options="quickFilterOptions"
        @change="(e) => addQuickFilter(e)"
      >
        <template #target="{ togglePopover }">
          <Button
            class="whitespace-nowrap mr-2"
            variant="ghost"
            @click="togglePopover()"
            :label="__('Add filter')"
          >
            <template #prefix>
              <FeatherIcon name="plus" class="h-4" />
            </template>
          </Button>
        </template>
        <template #item-label="{ option }">
          <Tooltip :text="option.value" :hover-delay="1">
            <div class="flex-1 truncate text-ink-gray-7">
              {{ option.label }}
            </div>
          </Tooltip>
        </template>
      </Autocomplete>
    </div>
    <div class="-ml-2 h-[70%] border-l" />
    <div class="flex gap-1">
      <Button
        :label="__('Save')"
        :loading="updateQuickFilters.loading"
        @click="saveQuickFilters"
      />
      <Button @click="customizeQuickFilter = false">
        <template #icon>
          <FeatherIcon name="x" class="h-4 w-4" />
        </template>
      </Button>
    </div>
  </div>
  <div v-else class="flex items-center justify-between gap-2 px-5 py-4">
    <FadedScrollableDiv
      class="flex flex-1 items-center overflow-x-auto -ml-1"
      orientation="horizontal"
    >
      <div
        v-for="filter in quickFilterList"
        :key="filter.fieldname"
        class="m-1 min-w-36"
      >
        <QuickFilterField
          :filter="filter"
          @applyQuickFilter="(f, v) => applyQuickFilter(f, v)"
        />
      </div>
    </FadedScrollableDiv>
    <div class="-ml-2 h-[70%] border-l" />
    <div class="flex items-center gap-2">
      <div
        v-if="viewUpdated && route.query.view && (!view.public || isManager())"
        class="flex items-center gap-2 border-r pr-2"
      >
        <Button :label="__('Cancel')" @click="cancelChanges" />
        <Button :label="__('Save Changes')" @click="saveView" />
      </div>
      <div class="flex items-center gap-2">
        <Button :label="__('Refresh')" @click="reload()" :loading="isLoading">
          <template #icon>
            <RefreshIcon class="h-4 w-4" />
          </template>
        </Button>
        <GroupBy
          v-if="route.params.viewType === 'group_by'"
          v-model="list"
          :doctype="doctype"
          @update="updateGroupBy"
        />
        <Filter
          v-model="list"
          :doctype="doctype"
          :default_filters="filters"
          @update="updateFilter"
        />
        <SortBy
          v-if="route.params.viewType !== 'kanban'"
          v-model="list"
          :doctype="doctype"
          @update="updateSort"
        />
        <KanbanSettings
          v-if="route.params.viewType === 'kanban'"
          v-model="list"
          :doctype="doctype"
          @update="updateKanbanSettings"
        />
        <ColumnSettings
          v-else-if="!options.hideColumnsButton"
          v-model="list"
          :doctype="doctype"
          @update="(isDefault) => updateColumns(isDefault)"
        />
        <Dropdown
          v-if="route.params.viewType !== 'kanban' || isManager()"
          :options="[
            {
              group: __('Options'),
              hideLabel: true,
              items: [
                {
                  label: __('Export'),
                  icon: () => h(ExportIcon, { class: 'h-4 w-4' }),
                  onClick: () => (showExportDialog = true),
                  condition: () =>
                    !options.hideColumnsButton &&
                    route.params.viewType !== 'kanban',
                },
                {
                  label: __('Customize quick filters'),
                  icon: () => h(QuickFilterIcon, { class: 'h-4 w-4' }),
                  onClick: () => showCustomizeQuickFilter(),
                  condition: () => isManager(),
                },
              ],
            },
          ]"
        >
          <template #default>
            <Button icon="more-horizontal" />
          </template>
        </Dropdown>
      </div>
    </div>
  </div>
  <ViewModal
    v-model="showViewModal"
    v-model:view="viewModalObj"
    :doctype="doctype"
    :options="{
      afterCreate: async (v) => {
        await reloadView()
        viewUpdated = false
        router.push({
          name: route.name,
          params: { viewType: v.type || 'list' },
          query: { view: v.name },
        })
      },
      afterUpdate: () => {
        viewUpdated = false
        reloadView()
        list.reload()
      },
    }"
  />
  <Dialog
    v-model="showExportDialog"
    :options="{
      title: __('Export'),
      actions: [
        {
          label: __('Download'),
          variant: 'solid',
          onClick: () => exportRows(),
        },
      ],
    }"
  >
    <template #body-content>
      <FormControl
        variant="outline"
        :label="__('Export Type')"
        type="select"
        :options="[
          {
            label: __('Excel'),
            value: 'Excel',
          },
          {
            label: __('CSV'),
            value: 'CSV',
          },
        ]"
        v-model="export_type"
        :placeholder="__('Excel')"
      />
      <div class="mt-3">
        <FormControl
          type="checkbox"
          :label="__('Export All {0} Record(s)', [list.data.total_count])"
          v-model="export_all"
        />
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import ListIcon from '@/components/Icons/ListIcon.vue'
import KanbanIcon from '@/components/Icons/KanbanIcon.vue'
import GroupByIcon from '@/components/Icons/GroupByIcon.vue'
import QuickFilterField from '@/components/QuickFilterField.vue'
import RefreshIcon from '@/components/Icons/RefreshIcon.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import DuplicateIcon from '@/components/Icons/DuplicateIcon.vue'
import CheckIcon from '@/components/Icons/CheckIcon.vue'
import PinIcon from '@/components/Icons/PinIcon.vue'
import UnpinIcon from '@/components/Icons/UnpinIcon.vue'
import ExportIcon from '@/components/Icons/ExportIcon.vue'
import QuickFilterIcon from '@/components/Icons/QuickFilterIcon.vue'
import ViewModal from '@/components/Modals/ViewModal.vue'
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
import SortBy from '@/components/SortBy.vue'
import Filter from '@/components/Filter.vue'
import GroupBy from '@/components/GroupBy.vue'
import FadedScrollableDiv from '@/components/FadedScrollableDiv.vue'
import ColumnSettings from '@/components/ColumnSettings.vue'
import KanbanSettings from '@/components/Kanban/KanbanSettings.vue'
import { getSettings } from '@/stores/settings'
import { globalStore } from '@/stores/global'
import { viewsStore } from '@/stores/views'
import { usersStore } from '@/stores/users'
import { getMeta } from '@/stores/meta'
import { isEmoji } from '@/utils'
import {
  Tooltip,
  createResource,
  Dropdown,
  toast,
  call,
  FeatherIcon,
  usePageMeta,
} from 'frappe-ui'
import { computed, ref, onMounted, watch, h, markRaw } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useDebounceFn } from '@vueuse/core'
import { isMobileView } from '@/composables/settings'
import Draggable from 'vuedraggable'
import _ from 'lodash'

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
  filters: {
    type: Object,
    default: {},
  },
  options: {
    type: Object,
    default: {
      hideColumnsButton: false,
      defaultViewName: '',
      allowedViews: ['list'],
    },
  },
})

const { brand } = getSettings()
const { $dialog } = globalStore()
const { reload: reloadView, getDefaultView, getView } = viewsStore()
const { isManager } = usersStore()

const list = defineModel()
const loadMore = defineModel('loadMore')
const resizeColumn = defineModel('resizeColumn')
const updatedPageCount = defineModel('updatedPageCount')

const route = useRoute()
const router = useRouter()

const defaultParams = ref('')

const viewUpdated = ref(false)
const showViewModal = ref(false)

function getViewType() {
  let viewType = route.params.viewType || 'list'
  let types = {
    list: {
      name: 'list',
      label: __('List'),
      icon: markRaw(ListIcon),
    },
    group_by: {
      name: 'group_by',
      label: __('Group By'),
      icon: markRaw(GroupByIcon),
    },
    kanban: {
      name: 'kanban',
      label: __('Kanban'),
      icon: markRaw(KanbanIcon),
    },
  }

  return types[viewType]
}

const currentView = computed(() => {
  let _view = getView(route.query.view, route.params.viewType, props.doctype)
  return {
    name: _view?.name || getViewType().name,
    label:
      _view?.label || props.options?.defaultViewName || getViewType().label,
    icon: _view?.icon || getViewType().icon,
    is_standard: !_view || _view.is_standard,
  }
})

usePageMeta(() => {
  let label = currentView.value.label
  if (currentView.value.is_standard) {
    let routeName = route.name
    label = `${routeName} - ${label}`
  }
  return {
    title: label,
    emoji: isEmoji(currentView.value.icon) ? currentView.value.icon : '',
    icon: brand.favicon,
  }
})

const view = ref({
  name: '',
  label: '',
  type: 'list',
  icon: '',
  filters: {},
  order_by: 'modified desc',
  column_field: 'status',
  title_field: '',
  kanban_columns: '',
  kanban_fields: '',
  columns: '',
  rows: '',
  load_default_columns: false,
  pinned: false,
  public: false,
})

const pageLength = computed(() => list.value?.data?.page_length)
const pageLengthCount = computed(() => list.value?.data?.page_length_count)

watch(loadMore, (value) => {
  if (!value) return
  updatePageLength(value, true)
})

watch(resizeColumn, (value) => {
  if (!value) return
  updateColumns()
})

watch(updatedPageCount, (value) => {
  if (!value) return
  updatePageLength(value)
})

function getParams() {
  let _view = getView(route.query.view, route.params.viewType, props.doctype)
  const view_name = _view?.name || ''
  const view_type = _view?.type || route.params.viewType || 'list'
  const filters = (_view?.filters && JSON.parse(_view.filters)) || {}
  const order_by = _view?.order_by || 'modified desc'
  const group_by_field = _view?.group_by_field || 'owner'
  const columns = _view?.columns || ''
  const rows = _view?.rows || ''
  const column_field = _view?.column_field || 'status'
  const title_field = _view?.title_field || ''
  const kanban_columns = _view?.kanban_columns || ''
  const kanban_fields = _view?.kanban_fields || ''

  view.value = {
    name: view_name,
    label: _view?.label || getViewType().label,
    type: view_type,
    icon: _view?.icon || '',
    filters: filters,
    order_by: order_by,
    group_by_field: group_by_field,
    column_field: column_field,
    title_field: title_field,
    kanban_columns: kanban_columns,
    kanban_fields: kanban_fields,
    columns: columns,
    rows: rows,
    route_name: _view?.route_name || route.name,
    load_default_columns: _view?.row || true,
    pinned: _view?.pinned || false,
    public: _view?.public || false,
  }

  return {
    doctype: props.doctype,
    filters: filters,
    order_by: order_by,
    default_filters: props.filters,
    view: {
      custom_view_name: view_name,
      view_type: view_type,
      group_by_field: group_by_field,
    },
    column_field: column_field,
    title_field: title_field,
    kanban_columns: kanban_columns,
    kanban_fields: kanban_fields,
    columns: columns,
    rows: rows,
    page_length: pageLength.value,
    page_length_count: pageLengthCount.value,
  }
}

list.value = createResource({
  url: 'crm.api.doc.get_data',
  params: getParams(),
  cache: [props.doctype, route.query.view, route.params.viewType],
  onSuccess(data) {
    let cv = getView(route.query.view, route.params.viewType, props.doctype)
    let params = list.value.params ? list.value.params : getParams()
    defaultParams.value = {
      doctype: props.doctype,
      filters: params.filters,
      order_by: params.order_by,
      default_filters: props.filters,
      view: {
        custom_view_name: cv?.name || '',
        view_type: cv?.type || route.params.viewType || 'list',
        group_by_field: params?.view?.group_by_field || 'owner',
      },
      column_field: data.column_field,
      title_field: data.title_field,
      kanban_columns: data.kanban_columns,
      kanban_fields: data.kanban_fields,
      columns: data.columns,
      rows: data.rows,
      page_length: params.page_length,
      page_length_count: params.page_length_count,
    }
  },
})

onMounted(() => useDebounceFn(reload, 100)())

const isLoading = computed(() => list.value?.loading)

function reload() {
  if (isLoading.value) return
  list.value.params = getParams()
  list.value.reload()
}

const showExportDialog = ref(false)
const export_type = ref('Excel')
const export_all = ref(false)
const selectedRows = ref([])

function updateSelections(selections) {
  selectedRows.value = Array.from(selections)
}

async function exportRows() {
  let fields = JSON.stringify(list.value.data.columns.map((f) => f.key))

  let filters = JSON.stringify({
    ...props.filters,
    ...list.value.params.filters,
  })

  let order_by = list.value.params.order_by
  let page_length = list.value.params.page_length
  if (export_all.value) {
    page_length = list.value.data.total_count
  }

  let url = `/api/method/frappe.desk.reportview.export_query?file_format_type=${export_type.value}&title=${props.doctype}&doctype=${props.doctype}&fields=${fields}&filters=${encodeURIComponent(filters)}&order_by=${order_by}&page_length=${page_length}&start=0&view=Report&with_comment_count=1`

  // Add selected items parameter if rows are selected
  if (selectedRows.value?.length && !export_all.value) {
    url += `&selected_items=${JSON.stringify(selectedRows.value)}`
  }

  window.location.href = url

  showExportDialog.value = false
  export_all.value = false
  export_type.value = 'Excel'
}

let standardViews = []
let allowedViews = props.options.allowedViews || ['list']

if (allowedViews.includes('list')) {
  standardViews.push({
    name: 'list',
    label: __(props.options?.defaultViewName) || __('List'),
    icon: markRaw(ListIcon),
    onClick() {
      viewUpdated.value = false
      router.push({ name: route.name })
    },
  })
}
if (allowedViews.includes('kanban')) {
  standardViews.push({
    name: 'kanban',
    label: __(props.options?.defaultViewName) || __('Kanban'),
    icon: markRaw(KanbanIcon),
    onClick() {
      viewUpdated.value = false
      router.push({ name: route.name, params: { viewType: 'kanban' } })
    },
  })
}
if (allowedViews.includes('group_by')) {
  standardViews.push({
    name: 'group_by',
    label: __(props.options?.defaultViewName) || __('Group By'),
    icon: markRaw(GroupByIcon),
    onClick() {
      viewUpdated.value = false
      router.push({ name: route.name, params: { viewType: 'group_by' } })
    },
  })
}

function getIcon(icon, type) {
  if (isEmoji(icon)) {
    return h('div', icon)
  } else if (!icon && type === 'group_by') {
    return markRaw(GroupByIcon)
  } else if (!icon && type === 'kanban') {
    return markRaw(KanbanIcon)
  }
  return icon || markRaw(ListIcon)
}

const viewsDropdownOptions = computed(() => {
  let _views = [
    {
      group: __('Standard Views'),
      hideLabel: true,
      items: standardViews,
    },
  ]

  if (list.value?.data?.views) {
    list.value.data.views.forEach((view) => {
      view.name = view.name
      view.label = __(view.label)
      view.type = view.type || 'list'
      view.icon = getIcon(view.icon, view.type)
      view.filters =
        typeof view.filters == 'string'
          ? JSON.parse(view.filters)
          : view.filters
      view.onClick = () => {
        viewUpdated.value = false
        router.push({
          name: route.name,
          params: { viewType: view.type },
          query: { view: view.name },
        })
      }
    })
    let publicViews = list.value.data.views.filter((v) => v.public)
    let savedViews = list.value.data.views.filter(
      (v) => !v.pinned && !v.public && !v.is_standard,
    )
    let pinnedViews = list.value.data.views.filter((v) => v.pinned)

    savedViews.length &&
      _views.push({
        group: __('Saved Views'),
        items: savedViews,
      })
    publicViews.length &&
      _views.push({
        group: __('Public Views'),
        items: publicViews,
      })
    pinnedViews.length &&
      _views.push({
        group: __('Pinned Views'),
        items: pinnedViews,
      })
  }

  _views.push({
    group: __('Actions'),
    hideLabel: true,
    items: [
      {
        label: __('Create View'),
        icon: 'plus',
        onClick: () => createView(),
      },
    ],
  })

  return _views
})

const { getFields } = getMeta(props.doctype)

const customizeQuickFilter = ref(false)

function showCustomizeQuickFilter() {
  customizeQuickFilter.value = true
  setupNewQuickFilters(quickFilters.data)
}

const newQuickFilters = ref([])

function addQuickFilter(f) {
  if (!newQuickFilters.value.some((filter) => filter.fieldname === f.value)) {
    newQuickFilters.value.push({
      label: f.label,
      fieldname: f.value,
      fieldtype: f.fieldtype,
    })
  }
}

function removeQuickFilter(f) {
  newQuickFilters.value = newQuickFilters.value.filter(
    (filter) => filter.fieldname !== f.fieldname,
  )
}

const updateQuickFilters = createResource({
  url: 'crm.api.doc.update_quick_filters',
  onSuccess() {
    customizeQuickFilter.value = false

    quickFilters.update({ params: { doctype: props.doctype, cached: false } })
    quickFilters.reload()
    toast.success(__('Quick Filters updated successfully'))
  },
})

function saveQuickFilters() {
  let new_filters =
    newQuickFilters.value?.map((filter) => filter.fieldname) || []
  let old_filters = quickFilters.data?.map((filter) => filter.fieldname) || []

  updateQuickFilters.update({
    params: {
      quick_filters: JSON.stringify(new_filters),
      old_filters: JSON.stringify(old_filters),
      doctype: props.doctype,
    },
  })

  updateQuickFilters.fetch()
}

const quickFilterOptions = computed(() => {
  let fields = getFields()
  if (!fields) return []

  let existingQuickFilters = newQuickFilters.value.map((f) => f.fieldname)
  let restrictedFieldtypes = [
    'Tab Break',
    'Section Break',
    'Column Break',
    'Table',
    'Table MultiSelect',
    'HTML',
    'Button',
    'Image',
    'Fold',
    'Heading',
  ]
  let options = fields
    .filter((f) => f.label && !restrictedFieldtypes.includes(f.fieldtype))
    .filter((f) => !existingQuickFilters.includes(f.fieldname))
    .map((field) => ({
      label: field.label,
      value: field.fieldname,
      fieldtype: field.fieldtype,
    }))

  if (!options.some((f) => f.fieldname === 'name')) {
    options.push({
      label: __('Name'),
      value: 'name',
      fieldtype: 'Data',
    })
  }

  return options
})

const quickFilterList = computed(() => {
  let filters = quickFilters.data || []

  filters.forEach((filter) => {
    filter['value'] = filter.fieldtype == 'Check' ? false : ''
    if (list.value.params?.filters[filter.fieldname]) {
      let value = list.value.params.filters[filter.fieldname]
      if (Array.isArray(value)) {
        if (
          (['Check', 'Select', 'Link', 'Date', 'Datetime'].includes(
            filter.fieldtype,
          ) &&
            value[0]?.toLowerCase() == 'like') ||
          value[0]?.toLowerCase() != 'like'
        )
          return
        filter['value'] = value[1]?.replace(/%/g, '')
      } else if (typeof value == 'boolean') {
        filter['value'] = value
      } else {
        filter['value'] = value?.replace(/%/g, '')
      }
    }
  })

  return filters
})

const quickFilters = createResource({
  url: 'crm.api.doc.get_quick_filters',
  params: { doctype: props.doctype },
  cache: ['Quick Filters', props.doctype],
  onSuccess(filters) {
    setupNewQuickFilters(filters)
  },
})

if (!quickFilters.data) quickFilters.fetch()

function setupNewQuickFilters(filters) {
  newQuickFilters.value = filters.map((f) => ({
    label: f.label,
    fieldname: f.fieldname,
    fieldtype: f.fieldtype,
  }))
}

function applyQuickFilter(filter, value) {
  let filters = { ...list.value.params.filters }
  let field = filter.fieldname
  if (value) {
    if (
      ['Check', 'Select', 'Link', 'Date', 'Datetime'].includes(filter.fieldtype)
    ) {
      filters[field] = value
    } else {
      filters[field] = ['LIKE', `%${value}%`]
    }
    filter['value'] = value
  } else {
    delete filters[field]
    filter['value'] = ''
  }
  updateFilter(filters)
}

function updateFilter(filters) {
  viewUpdated.value = true
  if (!defaultParams.value) {
    defaultParams.value = getParams()
  }
  list.value.params = defaultParams.value
  list.value.params.filters = filters
  view.value.filters = filters
  list.value.reload()

  if (!route.query.view) {
    createOrUpdateStandardView()
  }
}

function updateSort(order_by) {
  viewUpdated.value = true
  if (!defaultParams.value) {
    defaultParams.value = getParams()
  }
  list.value.params = defaultParams.value
  list.value.params.order_by = order_by
  view.value.order_by = order_by
  list.value.reload()

  if (!route.query.view) {
    createOrUpdateStandardView()
  }
}

function updateGroupBy(group_by_field) {
  viewUpdated.value = true
  if (!defaultParams.value) {
    defaultParams.value = getParams()
  }
  list.value.params = defaultParams.value
  list.value.params.view.group_by_field = group_by_field
  view.value.group_by_field = group_by_field
  list.value.reload()

  if (!route.query.view) {
    createOrUpdateStandardView()
  }
}

function updateColumns(obj) {
  if (!obj) {
    obj = {
      columns: list.value.data.columns,
      rows: list.value.data.rows,
      isDefault: false,
    }
  }

  if (!defaultParams.value) {
    defaultParams.value = getParams()
  }
  defaultParams.value.columns = view.value.columns = obj.isDefault
    ? ''
    : obj.columns
  defaultParams.value.rows = view.value.rows = obj.isDefault ? '' : obj.rows
  view.value.load_default_columns = obj.isDefault

  if (obj.reset) {
    defaultParams.value.columns = getParams().columns
    defaultParams.value.rows = getParams().rows
  }

  if (obj.reload) {
    list.value.params = defaultParams.value
    list.value.reload()
  }
  viewUpdated.value = true

  if (!route.query.view) {
    createOrUpdateStandardView()
  }
}

async function updateKanbanSettings(data) {
  if (data.item && data.to) {
    await call('frappe.client.set_value', {
      doctype: props.doctype,
      name: data.item,
      fieldname: view.value.column_field,
      value: data.to,
    })
  }
  let isDirty = viewUpdated.value

  viewUpdated.value = true
  if (!defaultParams.value) {
    defaultParams.value = getParams()
  }
  list.value.params = defaultParams.value
  if (data.kanban_columns) {
    list.value.params.kanban_columns = data.kanban_columns
    view.value.kanban_columns = data.kanban_columns
  }
  if (data.kanban_fields) {
    list.value.params.kanban_fields = data.kanban_fields
    view.value.kanban_fields = data.kanban_fields
  }
  if (data.column_field && data.column_field != view.value.column_field) {
    list.value.params.column_field = data.column_field
    view.value.column_field = data.column_field
    list.value.params.kanban_columns = ''
    view.value.kanban_columns = ''
  }
  if (data.title_field && data.title_field != view.value.title_field) {
    list.value.params.title_field = data.title_field
    view.value.title_field = data.title_field
  }

  list.value.reload()

  if (!route.query.view) {
    createOrUpdateStandardView()
  } else if (!data.column_field) {
    if (isDirty) {
      $dialog({
        title: __('Unsaved Changes'),
        message: __('You have unsaved changes. Do you want to save them?'),
        variant: 'danger',
        actions: [
          {
            label: __('Update'),
            variant: 'solid',
            onClick: (close) => {
              updateCustomView()
              close()
            },
          },
        ],
      })
    } else {
      updateCustomView()
    }
  }
}

function loadMoreKanban(columnName) {
  let columns = list.value.data.kanban_columns || '[]'

  if (typeof columns === 'string') {
    columns = JSON.parse(columns)
  }

  let column = columns.find((c) => c.name == columnName)

  if (!column.page_length) {
    column.page_length = 40
  } else {
    column.page_length += 20
  }
  list.value.params.kanban_columns = columns
  view.value.kanban_columns = columns
  list.value.reload()
}

function createOrUpdateStandardView() {
  if (route.query.view) return
  view.value.doctype = props.doctype
  call(
    'crm.fcrm.doctype.crm_view_settings.crm_view_settings.create_or_update_standard_view',
    {
      view: view.value,
    },
  ).then(() => {
    reloadView()
    view.value = {
      label: view.value.label,
      type: view.value.type || 'list',
      icon: view.value.icon,
      name: view.value.name,
      filters: defaultParams.value.filters,
      order_by: defaultParams.value.order_by,
      group_by_field: defaultParams.value.view?.group_by_field,
      column_field: defaultParams.value.column_field,
      title_field: defaultParams.value.title_field,
      kanban_columns: defaultParams.value.kanban_columns,
      kanban_fields: defaultParams.value.kanban_fields,
      columns: defaultParams.value.columns,
      rows: defaultParams.value.rows,
      route_name: route.name,
      load_default_columns: view.value.load_default_columns,
    }
    viewUpdated.value = false
  })
}

function updateCustomView() {
  viewUpdated.value = false
  view.value = {
    doctype: props.doctype,
    label: view.value.label,
    type: view.value.type || 'list',
    icon: view.value.icon,
    name: view.value.name,
    filters: defaultParams.value.filters,
    order_by: defaultParams.value.order_by,
    group_by_field: defaultParams.value.view.group_by_field,
    column_field: defaultParams.value.column_field,
    title_field: defaultParams.value.title_field,
    kanban_columns: defaultParams.value.kanban_columns,
    kanban_fields: defaultParams.value.kanban_fields,
    columns: defaultParams.value.columns,
    rows: defaultParams.value.rows,
    route_name: route.name,
    load_default_columns: view.value.load_default_columns,
  }
  call('crm.fcrm.doctype.crm_view_settings.crm_view_settings.update', {
    view: view.value,
  }).then(() => reloadView())
}

function updatePageLength(value, loadMore = false) {
  if (list.value.loading) return
  if (!defaultParams.value) {
    defaultParams.value = getParams()
  }
  list.value.params = defaultParams.value
  if (loadMore) {
    list.value.params.page_length += list.value.params.page_length_count
  } else {
    if (
      value == list.value.params.page_length &&
      value == list.value.params.page_length_count
    )
      return
    list.value.params.page_length = value
    list.value.params.page_length_count = value
  }
  list.value.reload()
}

// View Actions
const viewActions = (view) => {
  let isStandard = typeof view.name === 'string'
  let _view = getView(view.name)

  if (isStandard) {
    _view = getView(null, view.name, props.doctype)
  }

  if (!_view) {
    _view = {
      label: view.label,
      type: view.name,
      dt: props.doctype,
    }
  }

  let actions = [
    {
      group: __('Actions'),
      hideLabel: true,
      items: [
        {
          label: __('Duplicate'),
          icon: () => h(DuplicateIcon, { class: 'h-4 w-4' }),
          onClick: () => duplicateView(_view),
        },
      ],
    },
  ]

  if (!isDefaultView(_view, isStandard)) {
    actions[0].items.unshift({
      label: __('Set as default'),
      icon: () => h(CheckIcon, { class: 'h-4 w-4' }),
      onClick: () => setAsDefault(_view),
    })
  }

  if (!isStandard && (!_view.public || isManager())) {
    actions[0].items.push({
      label: __('Edit'),
      icon: () => h(EditIcon, { class: 'h-4 w-4' }),
      onClick: () => editView(_view),
    })

    if (!_view.public) {
      actions[0].items.push({
        label: _view.pinned ? __('Unpin View') : __('Pin View'),
        icon: () => h(_view.pinned ? UnpinIcon : PinIcon, { class: 'h-4 w-4' }),
        onClick: () => pinView(_view),
      })
    }

    if (isManager()) {
      actions[0].items.push({
        label: _view.public ? __('Make Private') : __('Make Public'),
        icon: () =>
          h(FeatherIcon, {
            name: _view.public ? 'lock' : 'unlock',
            class: 'h-4 w-4',
          }),
        onClick: () => publicView(_view),
      })
    }

    actions.push({
      group: __('Delete View'),
      hideLabel: true,
      items: [
        {
          label: __('Delete'),
          icon: 'trash-2',
          onClick: () =>
            $dialog({
              title: __('Delete View'),
              message: __('Are you sure you want to delete "{0}" view?', [
                _view.label,
              ]),
              variant: 'danger',
              actions: [
                {
                  label: __('Delete'),
                  variant: 'solid',
                  theme: 'red',
                  onClick: (close) => deleteView(_view, close),
                },
              ],
            }),
        },
      ],
    })
  }
  return actions
}

function isDefaultView(v, isStandard) {
  let defaultView = getDefaultView()

  if (!defaultView || (isStandard && !v.name)) return false

  return defaultView.name == v.name
}

const viewModalObj = ref({})

function createView() {
  view.value.name = ''
  view.value.label = ''
  view.value.icon = ''
  viewModalObj.value = view.value
  viewModalObj.value.mode = 'create'
  showViewModal.value = true
}

function setAsDefault(v) {
  call('crm.fcrm.doctype.crm_view_settings.crm_view_settings.set_as_default', {
    name: v.name,
    type: v.type,
    doctype: v.dt,
  }).then(() => {
    reloadView()
    list.value.reload()
  })
}

function duplicateView(v) {
  v.label = v.label + __(' (New)')
  viewModalObj.value = v
  viewModalObj.value.mode = 'duplicate'
  showViewModal.value = true
}

function editView(v) {
  viewModalObj.value = v
  viewModalObj.value.mode = 'edit'
  showViewModal.value = true
}

function publicView(v) {
  call('crm.fcrm.doctype.crm_view_settings.crm_view_settings.public', {
    name: v.name,
    value: !v.public,
  }).then(() => {
    v.public = !v.public
    reloadView()
    list.value.reload()
  })
}

function pinView(v) {
  call('crm.fcrm.doctype.crm_view_settings.crm_view_settings.pin', {
    name: v.name,
    value: !v.pinned,
  }).then(() => {
    v.pinned = !v.pinned
    reloadView()
    list.value.reload()
  })
}

function deleteView(v, close) {
  call('crm.fcrm.doctype.crm_view_settings.crm_view_settings.delete', {
    name: v.name,
  }).then(() => {
    router.push({ name: route.name })
    reloadView()
    list.value.reload()
  })
  close()
}

function cancelChanges() {
  reload()
  viewUpdated.value = false
}

function saveView() {
  view.value = {
    label: view.value.label,
    type: view.value.type || 'list',
    icon: view.value.icon,
    name: view.value.name,
    filters: defaultParams.value.filters,
    order_by: defaultParams.value.order_by,
    group_by_field: defaultParams.value.view.group_by_field,
    column_field: defaultParams.value.column_field,
    title_field: defaultParams.value.title_field,
    kanban_columns: defaultParams.value.kanban_columns,
    kanban_fields: defaultParams.value.kanban_fields,
    columns: defaultParams.value.columns,
    rows: defaultParams.value.rows,
    route_name: route.name,
    load_default_columns: view.value.load_default_columns,
  }
  viewModalObj.value = view.value
  viewModalObj.value.mode = 'edit'
  showViewModal.value = true
}

function applyFilter({ event, idx, column, item, firstColumn }) {
  let restrictedFieldtypes = ['Duration', 'Datetime', 'Time']
  if (restrictedFieldtypes.includes(column.type) || idx === 0) return
  if (idx === 1 && firstColumn.key == '_liked_by') return

  event.stopPropagation()
  event.preventDefault()

  let filters = { ...list.value.params.filters }

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
  updateFilter(filters)
}

function applyLikeFilter() {
  let filters = { ...list.value.params.filters }
  if (!filters._liked_by) {
    filters['_liked_by'] = ['LIKE', '%@me%']
  } else {
    delete filters['_liked_by']
  }
  updateFilter(filters)
}

function likeDoc({ name, liked }) {
  createResource({
    url: 'frappe.desk.like.toggle_like',
    params: { doctype: props.doctype, name: name, add: liked ? 'No' : 'Yes' },
    auto: true,
    onSuccess: () => reload(),
  })
}

defineExpose({
  applyFilter,
  applyLikeFilter,
  likeDoc,
  updateKanbanSettings,
  loadMoreKanban,
  viewActions,
  viewsDropdownOptions,
  currentView,
  updateSelections,
})

// Watchers
watch(
  () => getView(route.query.view, route.params.viewType, props.doctype),
  (value, old_value) => {
    if (_.isEqual(value, old_value)) return
    reload()
  },
  { deep: true },
)

watch([() => route, () => route.params.viewType], (value, old_value) => {
  if (value[0] === old_value[0] && value[1] === value[0]) return
  reload()
})
</script>
