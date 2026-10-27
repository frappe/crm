<template>
  <HomeWidget
    :title="__('Recently opened')"
    :resource="resource"
    widget="recently_opened"
    :columns="defaultColumns"
    :config="config"
    :emptyText="__('Leads and deals you open will show up here.')"
    emptyIcon="lucide-history"
    @update:config="(value) => emit('update:config', value)"
  >
    <template #default="{ rows, columns }">
      <HomeTable :columns="columns" :rows="rows" :rowRoute="recordRoute" />
    </template>
  </HomeWidget>
</template>
<script setup>
import HomeTable from '@/components/Home/HomeTable.vue'
import HomeWidget from '@/components/Home/HomeWidget.vue'
import { homeColumns } from '@/components/Home/columns'
import { loadWidgetColumns } from '@/composables/homeWidget'
import { sessionStore } from '@/stores/session'
import { recordRoute } from '@/utils/home'
import { readRecent, sortByRecency } from '@/utils/recentRecords'
import { call } from 'frappe-ui'
import { reactive, watch } from 'vue'

const props = defineProps({
  config: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['update:config'])

const FIELDS = {
  'CRM Lead': { title: 'lead_name', subtitle: 'organization' },
  'CRM Deal': { title: 'organization', subtitle: 'lead_name' },
}
const DOCTYPES = { Lead: ['CRM Lead'], Deal: ['CRM Deal'] }

const defaultColumns = [
  homeColumns.record(),
  {
    key: 'doctype',
    label: __('Type'),
    width: '4rem',
    getLabel: ({ row }) =>
      row.doctype === 'CRM Deal' ? __('Deal') : __('Lead'),
  },
  homeColumns.status(),
]

const { user } = sessionStore()

const resource = reactive({ data: null, loading: false })

const extraKeys = () =>
  (props.config.columns || [])
    .map((column) => column.key)
    .filter((key) => !defaultColumns.some((column) => column.key === key))

watch(() => [props.config.doctype, extraKeys().join()], load, {
  immediate: true,
})

async function load() {
  const doctypes = DOCTYPES[props.config.doctype] || Object.keys(FIELDS)
  const recent = readRecent(user).filter((item) =>
    doctypes.includes(item.doctype),
  )
  resource.loading = true
  try {
    const extra = await extraFields()
    const records = await Promise.all(
      doctypes.map((d) => fetchRecords(d, recent, extra)),
    )
    resource.data = { rows: sortByRecency(records.flat(), recent) }
  } finally {
    resource.loading = false
  }
}

async function extraFields() {
  const keys = extraKeys()
  if (!keys.length) return []
  const { fields } = await loadWidgetColumns(
    'recently_opened',
    props.config.doctype || 'Both',
  )
  return keys
    .filter((key) => fields[key])
    .map((key) => ({ ...fields[key], currency: currencyField(fields, key) }))
}

async function fetchRecords(doctype, recent, extra) {
  const names = recent.filter((r) => r.doctype === doctype).map((r) => r.name)
  if (!names.length) return []
  const fields = FIELDS[doctype]
  const records = await call('frappe.client.get_list', {
    doctype,
    filters: { name: ['in', names] },
    fields: [
      'name',
      'status',
      fields.title,
      fields.subtitle,
      ...extra.flatMap((field) => fetchedFields(field, doctype)),
    ],
  })
  return records.map((record) => ({
    ...record,
    doctype,
    title: record[fields.title],
    subtitle: record[fields.subtitle],
  }))
}

function fetchedFields({ fieldname, source, currency }, doctype) {
  if (source) return [`${source[doctype]} as ${fieldname}`]
  return currency ? [fieldname, currency] : [fieldname]
}

// Currency cells format in the row's currency, so its field comes along when the user can add it.
function currencyField(fields, key) {
  const { fieldtype, options } = fields[key]
  return fieldtype === 'Currency' && fields[options] ? options : null
}
</script>
