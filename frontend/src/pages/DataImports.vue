<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Data Import" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="dataImportsListView?.customListActions"
        :actions="dataImportsListView.customListActions"
      />
      <Button
        variant="solid"
        :label="__('Create')"
        iconLeft="lucide-plus"
        @click="router.push({ name: 'NewDataImport' })"
      />
    </template>
  </LayoutHeader>
  <ViewControls
    ref="viewControls"
    v-model="dataImports"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="Data Import"
    :filters="queryFilters"
    :filtersLabel="queryFiltersLabel"
    @clearFilters="router.replace({ name: 'Data Import' })"
  />
  <DataImportsListView
    v-if="dataImports.data && rows.length"
    ref="dataImportsListView"
    v-model="dataImports.data.page_length_count"
    v-model:list="dataImports"
    :rows="rows"
    :columns="columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: dataImports.data.row_count,
      totalCount: dataImports.data.total_count,
    }"
    @openImport="
      (importName) =>
        router.push({ name: 'DataImport', params: { importName } })
    "
    @loadMore="() => loadMore++"
    @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)"
    @applyFilter="(data) => viewControls.applyFilter(data)"
    @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
    @likeDoc="(data) => viewControls.likeDoc(data)"
    @selectionsChanged="
      (selections) => viewControls.updateSelections(selections)
    "
  />
  <EmptyState
    v-else-if="dataImports.data && !rows.length"
    name="Data Imports"
    icon="import"
    :description="__('Imports you start from a list appear here.')"
  />
</template>

<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import CustomActions from '@/components/CustomActions.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewControls from '@/components/ViewControls.vue'
import DataImportsListView from '@/components/ListViews/DataImportsListView.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import { getDataImportRow } from '@/utils/dataImport'
import { usePageMeta } from 'frappe-ui'
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const dataImportsListView = ref(null)

// dataImports data is loaded in the ViewControls component
const dataImports = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

// "Review pending imports" in the wizard opens this list for one doctype
const queryFilters = computed(() => {
  const { doctype, status } = route.query
  return {
    ...(doctype && { reference_doctype: doctype }),
    ...(status && { status }),
  }
})

const queryFiltersLabel = computed(() =>
  [route.query.status, route.query.doctype]
    .filter(Boolean)
    .map((value) => __(value))
    .join(' · '),
)

const rows = computed(() => {
  if (
    !dataImports.value?.data?.data ||
    !['list', 'group_by'].includes(dataImports.value.data.view_type)
  )
    return []
  return dataImports.value.data.data.map((dataImport) => {
    let _rows = {}
    dataImports.value.data.rows.forEach((row) => {
      _rows[row] = getDataImportRow(row, dataImport)
    })
    return _rows
  })
})

const columns = computed(() => {
  let _columns = dataImports.value?.data?.columns || []

  // Set align right for last column
  if (_columns.length) {
    _columns = _columns.map((col, index) => {
      if (index === _columns.length - 1) {
        return { ...col, align: 'right' }
      }
      return col
    })
  }

  return _columns
})

usePageMeta(() => ({ title: __('Data Import') }))
</script>
