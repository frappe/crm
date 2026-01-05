<template>
  <CustomizeQuickFilter
    v-if="customizeQuickFilter"
    @close="customizeQuickFilter = false"
  />
  <div v-else class="flex items-center justify-between gap-2 px-5 py-4">
    <!-- Quick Filters -->
    <FadedScrollableDiv
      class="flex flex-1 items-center overflow-x-auto -ml-1 h-9"
      orientation="horizontal"
    >
      <div
        v-for="filter in quickFilterList"
        :key="filter.fieldname"
        class="flex items-center mx-1 min-w-36"
      >
        <QuickFilterField
          :filter="filter"
          @applyQuickFilter="(f, v) => applyQuickFilter(f, v, updateFilter)"
        />
      </div>
    </FadedScrollableDiv>

    <div class="-ml-2 h-[70%] border-l" />

    <!-- Filter, Sort, Columns -->
    <div class="flex items-center gap-2">
      <div
        v-if="viewUpdated && route.query.view && (!view.public || isManager())"
        class="flex items-center gap-2 border-r pr-2"
      >
        <Button :label="__('Cancel')" @click="cancelChanges" />
        <Button :label="__('Save Changes')" @click="saveView" />
      </div>
      <div class="flex items-center gap-2">
        <Button
          :tooltip="__('Refresh')"
          :icon="RefreshIcon"
          :loading="list?.loading"
          @click="reload"
        />
        <Filter :default_filters="filters" @update="updateFilter" />
        <SortBy @update="updateSort" />
        <ColumnSettings @update="updateColumns" />
        <Dropdown
          v-if="route?.params.viewType !== 'kanban' || isManager()"
          placement="right"
          :options="[
            {
              group: __('Options'),
              hideLabel: true,
              items: [
                {
                  label: __('Import'),
                  icon: () => h(ImportIcon, { class: 'h-4 w-4' }),
                  onClick: () =>
                    router.push({
                      name: 'NewDataImport',
                      params: { doctype: doctype },
                    }),
                  condition: () =>
                    !options.hideColumnsButton &&
                    route.params.viewType !== 'kanban',
                },
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
            <Button :tooltip="__('More Options')" icon="more-horizontal" />
          </template>
        </Dropdown>
      </div>
    </div>
  </div>
</template>
<script setup>
import Filter from '@/components/Views/List/Filter.vue'
import SortBy from '@/components/Views/List/SortBy.vue'
import ColumnSettings from '@/components/Views/List/ColumnSettings.vue'
import QuickFilterField from '@/components/QuickFilterField.vue'
import RefreshIcon from '@/components/Icons/RefreshIcon.vue'
import ExportIcon from '@/components/Icons/ExportIcon.vue'
import QuickFilterIcon from '@/components/Icons/QuickFilterIcon.vue'
import ImportIcon from '~icons/lucide/import'
import FadedScrollableDiv from '@/components/FadedScrollableDiv.vue'
import CustomizeQuickFilter from './CustomizeQuickFilter.vue'
import { usersStore } from '@/stores/users'
import { useQuickFilters } from './quickFilter'
import { useControls } from './controls'
import { useList } from './list'
import { Dropdown } from 'frappe-ui'
import { h, inject, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const props = defineProps({
  filters: {
    type: Object,
    default: {},
  },
  options: {
    type: Object,
    default: () => ({}),
  },
})

const doctype = inject('doctype')
const router = useRouter()
const route = useRoute()

const viewUpdated = ref(false)

const { isManager } = usersStore()

const {
  customizeQuickFilter,
  showCustomizeQuickFilter,
  quickFilterList,
  applyQuickFilter,
} = useQuickFilters(doctype)

const { list, reload } = useList()
const { updateFilter, updateSort, updateColumns } = useControls()
</script>
