<template>
  <HomeWidget
    :title="__('Recently opened')"
    :resource="resource"
    :config="config"
    :emptyText="__('Leads and deals you open will show up here.')"
    emptyIcon="lucide-history"
    :columns="['1rem', 'minmax(0,1fr)', '4rem']"
    @update:config="(value) => emit('update:config', value)"
  >
    <template #default="{ row }">
      <RecordRow :record="row">
        <ListCell class="justify-end text-ink-gray-5">
          {{ row.doctype === 'CRM Deal' ? __('Deal') : __('Lead') }}
        </ListCell>
      </RecordRow>
    </template>
  </HomeWidget>
</template>
<script setup>
import HomeWidget from '@/components/Home/HomeWidget.vue'
import RecordRow from '@/components/Home/RecordRow.vue'
import { sessionStore } from '@/stores/session'
import { readRecent, sortByRecency } from '@/utils/recentRecords'
import { call } from 'frappe-ui'
import { ListCell } from 'frappe-ui/list'
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

const { user } = sessionStore()

const resource = reactive({ data: null, loading: false })

watch(() => props.config.doctype, load, { immediate: true })

async function load() {
  const doctypes = DOCTYPES[props.config.doctype] || Object.keys(FIELDS)
  const recent = readRecent(user).filter((item) =>
    doctypes.includes(item.doctype),
  )
  resource.loading = true
  try {
    const records = await Promise.all(
      doctypes.map((d) => fetchRecords(d, recent)),
    )
    resource.data = { rows: sortByRecency(records.flat(), recent) }
  } finally {
    resource.loading = false
  }
}

async function fetchRecords(doctype, recent) {
  const names = recent.filter((r) => r.doctype === doctype).map((r) => r.name)
  if (!names.length) return []
  const fields = FIELDS[doctype]
  const records = await call('frappe.client.get_list', {
    doctype,
    filters: { name: ['in', names] },
    fields: ['name', 'status', fields.title, fields.subtitle],
  })
  return records.map((record) => ({
    doctype,
    name: record.name,
    status: record.status,
    title: record[fields.title],
    subtitle: record[fields.subtitle],
  }))
}
</script>
