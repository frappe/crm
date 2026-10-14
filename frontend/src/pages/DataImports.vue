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
    @applyFilter="(data) => viewControls?.applyFilter(data)"
    @applyLikeFilter="() => viewControls?.applyLikeFilter()"
    @likeDoc="(data) => viewControls?.likeDoc(data)"
    @selectionsChanged="
      (selections) => viewControls?.updateSelections(selections)
    "
  />
  <EmptyState
    v-else-if="dataImports.data && !rows.length"
    name="Data Imports"
    icon="import"
    :filtered="
      !!Object.keys({ ...queryFilters, ...dataImports.params?.filters }).length
    "
    :description="__('Imports you start from a list appear here.')"
  />
</template>

<script setup lang="ts">
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import CustomActions from '@/components/CustomActions.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewControls from '@/components/ViewControls.vue'
import DataImportsListView from '@/components/ListViews/DataImportsListView.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import {
  getDataImportRow,
  type DataImportList,
  type ListColumn,
} from '@/utils/dataImport'
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const dataImportsListView = ref<InstanceType<
  typeof DataImportsListView
> | null>(null)

// dataImports data is loaded in the ViewControls component
const dataImports = ref<DataImportList>({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref<InstanceType<typeof ViewControls> | null>(null)

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
    .map((value) => __(value as string))
    .join(' · '),
)

const rows = computed(() => {
  const list = dataImports.value?.data
  if (!list?.data || !['list', 'group_by'].includes(list.view_type)) return []
  return list.data.map((dataImport) => {
    let _rows: Record<string, unknown> = {}
    list.rows.forEach((row) => {
      _rows[row] = getDataImportRow(row, dataImport)
    })
    return _rows
  })
})

const columns = computed(() => {
  let _columns: ListColumn[] = dataImports.value?.data?.columns || []

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
</script>
