<template>
  <div class="flex flex-col">
    <div class="flex items-center justify-between gap-8 py-3 px-2">
      <div class="flex flex-col">
        <div class="text-p-base-medium text-ink-gray-7 truncate">
          {{ __('Insights Dashboards') }}
        </div>
        <div class="text-p-sm text-ink-gray-5">
          {{ __('Dashboards people can switch between on the Dashboard page') }}
        </div>
      </div>
      <Link
        class="form-control w-48"
        doctype="Insights Dashboard v3"
        value=""
        :placeholder="__('Add Dashboard')"
        placement="bottom-end"
        @change="addDashboard"
      />
    </div>
    <ul class="flex flex-col">
      <li
        v-for="row in rows"
        :key="row.dashboard"
        class="flex items-center gap-3 py-1.5 px-2"
      >
        <TextInput
          class="flex-1"
          :modelValue="row.label"
          :placeholder="row.dashboard"
          :aria-label="__('Label')"
          @update:modelValue="(label) => (editRow(row).label = label)"
        />
        <Badge v-if="row.customized_from" :label="__('Customized')" />
        <Badge v-if="row.is_default" :label="__('Default')" />
        <Dropdown :options="rowOptions(row)" align="end">
          <Button
            variant="ghost"
            icon="lucide-more-horizontal"
            :aria-label="__('Options')"
          />
        </Dropdown>
      </li>
    </ul>
  </div>
</template>

<script setup>
import Link from '@/components/Controls/Link.vue'
import { useInsightsDashboards } from '@/composables/useInsightsDashboards'
import { ConfirmDelete } from '@/utils'
import { Badge, Button, call, Dropdown, TextInput, toast } from 'frappe-ui'
import { ref } from 'vue'

const { rows, editableRows } = useInsightsDashboards()

const confirmingRemove = ref(false)

function editRow(row) {
  return editableRows().find((r) => r.dashboard === row.dashboard)
}

async function addDashboard(dashboard) {
  if (!dashboard) return
  if (rows.value.some((row) => row.dashboard === dashboard)) {
    toast.error(__('This dashboard is already added'))
    return
  }
  const doc = await call('frappe.client.get_value', {
    doctype: 'Insights Dashboard v3',
    filters: dashboard,
    fieldname: 'title',
  }).catch(() => null)
  editableRows().push({ dashboard, label: doc?.title || '', is_default: 0 })
}

function setDefault(row) {
  for (const r of editableRows())
    r.is_default = r.dashboard === row.dashboard ? 1 : 0
}

function removeRow(row) {
  const all = editableRows()
  all.splice(all.indexOf(editRow(row)), 1)
  if (all.length && !all.some((r) => r.is_default)) all[0].is_default = 1
}

function rowOptions(row) {
  return [
    {
      label: __('Set as Default'),
      icon: 'lucide-star',
      onClick: () => setDefault(row),
      condition: () => !row.is_default,
    },
    ...ConfirmDelete({
      isConfirmingDelete: confirmingRemove,
      onConfirmDelete: () => removeRow(row),
      label: __('Remove'),
    }),
  ]
}
</script>
