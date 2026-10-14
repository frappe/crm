<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
  </LayoutHeader>
  <div class="mx-auto flex min-h-0 w-full max-w-5xl flex-1 flex-col p-5">
    <DataImportWizard
      :dataImport="dataImport"
      @open-list="openList"
      @open-record="openRecord"
      @open-imports="openImports"
      @new-import="newImport"
    />
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import { importListQuery } from '@/utils/dataImport'
import {
  DataImportWizard,
  useDataImport,
} from '@framework/ui/components/DataImport'
import { getSettings } from '@/stores/settings'
import { Breadcrumbs, usePageMeta } from 'frappe-ui'
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const crmPages = {
  'CRM Lead': { title: 'Leads', list: 'Leads', page: 'Lead', param: 'leadId' },
  'CRM Deal': { title: 'Deals', list: 'Deals', page: 'Deal', param: 'dealId' },
  Contact: {
    title: 'Contacts',
    list: 'Contacts',
    page: 'Contact',
    param: 'contactId',
  },
  'CRM Organization': {
    title: 'Organizations',
    list: 'Organizations',
    page: 'Organization',
    param: 'organizationId',
  },
  'CRM Task': { title: 'Tasks', list: 'Tasks' },
  'CRM Call Log': { title: 'Call Logs', list: 'Call Logs' },
}

const route = useRoute()
const router = useRouter()
const { brand } = getSettings()

usePageMeta(() => {
  return {
    title: __('Data Import'),
    icon: brand.favicon,
  }
})

const name = ref(route.params.importName || null)
const dataImport = useDataImport(name, {
  doctype: () => route.params.doctype || undefined,
})

// the first save names a new import; keep the URL on it so a reload reopens it
watch(name, (importName) => {
  if (importName && importName !== route.params.importName) {
    router.replace({ name: 'DataImport', params: { importName } })
  }
})
watch(
  () => route.params.importName,
  (importName) => (name.value = importName || null),
)

const breadcrumbs = computed(() => {
  const doctype = dataImport.doc.value.reference_doctype || route.params.doctype
  const title = crmPages[doctype]?.title || doctype
  const items = [{ label: __('Data Import'), route: { name: 'Data Import' } }]
  // lead with the records list, so it is one click away whatever the outcome
  const page = crmPages[doctype]
  if (page) items.unshift({ label: __(page.title), route: { name: page.list } })
  if (title) items.push({ label: __('Importing {0}', [__(title)]) })
  return items
})

function openList(doctype) {
  const page = crmPages[doctype]
  if (page) {
    router.push({
      name: page.list,
      query: importListQuery(dataImport.doc.value),
    })
  }
}

function openRecord(doctype, docname) {
  const page = crmPages[doctype]
  if (page?.page) {
    router.push({ name: page.page, params: { [page.param]: docname } })
  }
}

function openImports(doctype) {
  router.push({ name: 'Data Import', query: { doctype, status: 'Pending' } })
}

function newImport(doctype) {
  router.push({ name: 'NewDataImport', params: { doctype } })
}
</script>
