<template>
  <div
    class="flex h-full w-full flex-col overflow-hidden rounded-4 border border-outline-gray-1 bg-surface-elevation-2"
  >
    <div class="flex h-10 shrink-0 items-center gap-1.5 pl-4 pr-2">
      <span class="truncate text-base-medium text-ink-gray-8">
        {{ title }}
      </span>
      <span v-if="total" class="text-base tabular-nums text-ink-gray-5">
        {{ more ? `${total}+` : total }}
      </span>
      <span v-if="config && doctype !== 'Both'" class="text-sm text-ink-gray-5">
        · {{ doctypeLabels[doctype] }}
      </span>
      <div
        v-if="widget || editing"
        class="ml-auto flex shrink-0 items-center gap-0.5"
        :class="{ 'pointer-events-auto': editing }"
      >
        <Dropdown
          v-if="editing && hasDoctypeSetting"
          :options="[doctypeOptions]"
          align="end"
        >
          <Button
            variant="ghost"
            icon="lucide-list-filter"
            :tooltip="__('Show leads or deals')"
          />
        </Dropdown>
        <!-- Keyed so the popover re-anchors when the trigger changes with edit mode -->
        <ColumnSettings
          v-if="widget"
          :key="editing"
          v-model="columnList"
          v-model:open="editingColumns"
          manual
          :fieldOptions="fieldOptions"
          :lockedColumns="columnInfo?.locked"
          :defaultWidth="(field) => field.width || fieldWidth(field)"
          @update="updateColumns"
        >
          <template #trigger>
            <Button
              v-if="editing"
              variant="ghost"
              icon="lucide-columns-3"
              :tooltip="__('Edit columns')"
              @click="editColumns"
            />
            <Dropdown v-else :options="menuOptions" align="end">
              <Button
                variant="ghost"
                icon="lucide-ellipsis"
                :aria-label="__('Widget options')"
              />
            </Dropdown>
          </template>
        </ColumnSettings>
        <template v-if="editing">
          <Tooltip :text="__('Drag to move')">
            <span
              class="home-drag-handle flex size-7 cursor-grab items-center justify-center rounded text-ink-gray-6 hover:bg-surface-gray-2 active:cursor-grabbing"
              :aria-label="__('Drag to move')"
            >
              <span class="lucide-grip-vertical size-4" aria-hidden="true" />
            </span>
          </Tooltip>
          <Button
            variant="ghost"
            icon="lucide-x"
            :tooltip="__('Remove')"
            @click="emit('remove')"
          />
        </template>
      </div>
    </div>

    <div class="flex min-h-0 flex-1 flex-col overflow-y-auto px-2">
      <div v-if="loading" class="flex flex-1 items-center justify-center">
        <LoadingIndicator class="size-4 text-ink-gray-5" />
      </div>
      <div
        v-else-if="!rows.length"
        class="flex flex-1 flex-col items-center justify-center gap-3 px-4 pb-10 text-center"
      >
        <span
          class="flex size-8 items-center justify-center rounded-full bg-surface-gray-2"
        >
          <span :class="emptyIcon" class="size-4 text-ink-gray-5" />
        </span>
        <span class="max-w-64 text-p-base text-ink-gray-6">
          {{ emptyText }}
        </span>
      </div>
      <slot v-else :rows="rows" :columns="shownColumns" />
    </div>

    <div
      v-if="$slots.footer || (viewAll.length && total)"
      class="flex h-8 shrink-0 items-center justify-end px-2"
    >
      <slot name="footer">
        <Button
          v-if="viewAll.length === 1"
          variant="ghost"
          :label="__('View all')"
          iconRight="lucide-arrow-right"
          :route="viewAll[0].route"
        />
        <Dropdown v-else :options="viewAll" align="end">
          <Button
            variant="ghost"
            :label="__('View all')"
            iconRight="lucide-chevron-down"
          />
        </Dropdown>
      </slot>
    </div>
  </div>
</template>
<script setup>
import ColumnSettings from '@/components/ColumnSettings.vue'
import {
  fieldWidth,
  keepAvailable,
  resolveColumns,
  toSavedColumns,
} from '@/components/Home/columns'
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import { getWidgetColumns, loadWidgetColumns } from '@/composables/homeWidget'
import { Dropdown, Tooltip } from 'frappe-ui'
import { computed, inject, ref, watch } from 'vue'

const props = defineProps({
  title: { type: String, required: true },
  resource: { type: Object, required: true },
  config: { type: Object, default: null },
  // Key in widgets.js; set with `columns` when the widget's columns are editable.
  widget: { type: String, default: null },
  columns: { type: Array, default: () => [] },
  viewAll: { type: Array, default: () => [] },
  emptyText: { type: String, required: true },
  emptyIcon: { type: String, default: 'lucide-check-circle-2' },
})

// Home's `remove` listener falls through each widget component to here.
const emit = defineEmits(['update:config', 'remove'])

const editing = inject('homeEditing', ref(false))

const doctypeLabels = {
  Both: __('Leads & deals'),
  Lead: __('Leads'),
  Deal: __('Deals'),
}

const doctype = computed(() => props.config?.doctype || 'Both')
const rows = computed(() => props.resource.data?.rows || [])
const total = computed(() => props.resource.data?.total || 0)
const more = computed(() => props.resource.data?.more)
const loading = computed(() => props.resource.loading && !props.resource.data)

const hasDoctypeSetting = computed(() => Boolean(props.config?.doctype))
const columnInfo = computed(() => getWidgetColumns(props.widget, doctype.value))
const fields = computed(() => columnInfo.value?.fields || {})

const shownColumns = computed(() =>
  resolveColumns(props.columns, props.config?.columns, fields.value),
)

const savedKeys = () => props.config?.columns?.map((column) => column.key)
watch(
  () => props.widget && savedKeys()?.join(),
  () => {
    const defaults = props.columns.map((column) => column.key)
    if (savedKeys()?.some((key) => !defaults.includes(key)))
      loadWidgetColumns(props.widget, doctype.value)
  },
  { immediate: true },
)

const doctypeOptions = computed(() => ({
  group: __('Show'),
  options: Object.entries(doctypeLabels).map(([value, label]) => ({
    label,
    selected: value === doctype.value,
    onClick: () => setDoctype(value),
  })),
}))

const menuOptions = computed(() => [
  ...(hasDoctypeSetting.value ? [doctypeOptions.value] : []),
  {
    group: __('Columns'),
    hideLabel: true,
    options: [
      {
        label: __('Edit columns'),
        icon: 'lucide-columns-3',
        onClick: editColumns,
      },
    ],
  },
])

async function setDoctype(value) {
  if (value === doctype.value) return
  const config = { ...props.config, doctype: value }
  if (config.columns) {
    const { fields } = await loadWidgetColumns(props.widget, value)
    config.columns = keepAvailable(config.columns, props.columns, fields)
  }
  emit('update:config', config)
}

const editingColumns = ref(false)
// ColumnSettings edits this copy in place and reports each change through `update`.
const columnList = ref({ data: null })

async function editColumns() {
  await loadWidgetColumns(props.widget, doctype.value)
  columnList.value = {
    data: {
      columns: shownColumns.value.map((column) => ({ ...column })),
      rows: shownColumns.value.map((column) => column.key),
      is_default: !props.config?.columns,
    },
  }
  editingColumns.value = true
}

// Built-in columns that were removed can be added back like any field.
const fieldOptions = computed(() => [
  ...props.columns
    .filter((column) => column.label)
    .map((column) => ({
      fieldname: column.key,
      label: column.label,
      fieldtype: column.fieldtype,
      width: column.width,
    })),
  ...Object.values(fields.value),
])

function updateColumns({ columns, isDefault }) {
  const config = { ...props.config }
  if (isDefault) delete config.columns
  else config.columns = toSavedColumns(columns, props.columns, fields.value)
  emit('update:config', config)
}
</script>
