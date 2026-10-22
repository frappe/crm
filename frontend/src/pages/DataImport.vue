<template>
  <LegacyDataImport v-if="!dataImport" />
  <template v-else>
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
</template>

<script setup lang="ts">
import LayoutHeader from '@/components/LayoutHeader.vue'
import LegacyDataImport from '@/components/LegacyDataImport.vue'
import { importListQuery } from '@/utils/dataImport'
// Frappe v15 ships only the older DataImport, so these may be missing; a named
// import would fail the build there
import * as dataImportUi from '@framework/ui/components/DataImport'
import { getSettings } from '@/stores/settings'
import { Breadcrumbs, usePageMeta, type BreadcrumbsProps } from 'frappe-ui'
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

interface CrmPage {
  title: string
  list: string
  page?: string
  param?: string
}

const crmPages: Record<string, CrmPage> = {
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
    icon: (brand as { favicon?: string }).favicon,
  }
})

const name = ref<string | null>((route.params.importName as string) || null)
const { DataImportWizard, useDataImport } = dataImportUi as Partial<
  typeof dataImportUi
>
const dataImport = useDataImport?.(name, {
  doctype: () => (route.params.doctype as string) || undefined,
})

// the first save names a new import; keep the URL on it so a reload reopens it
watch(name, (importName) => {
  if (importName && importName !== route.params.importName) {
    router.replace({ name: 'DataImport', params: { importName } })
  }
})
watch(
  () => route.params.importName,
  (importName) => (name.value = (importName as string) || null),
)

const breadcrumbs = computed(() => {
  const doctype =
    dataImport?.doc.value.reference_doctype || (route.params.doctype as string)
  const page = crmPages[doctype]
  const title = page?.title || doctype
  return [
    page && { label: __(page.title), route: { name: page.list } },
    { label: __('Data Imports'), route: { name: 'Data Imports' } },
    title && { label: __('Importing {0}', [__(title)]) },
  ].filter(Boolean) as BreadcrumbsProps['items']
})

function openList(doctype: string) {
  const page = crmPages[doctype]
  if (page) {
    router.push({
      name: page.list,
      query: importListQuery(dataImport!.doc.value),
    })
  }
}

function openRecord(doctype: string, docname: string) {
  const page = crmPages[doctype]
  if (page?.page && page.param) {
    router.push({ name: page.page, params: { [page.param]: docname } })
  }
}

function openImports(doctype: string) {
  router.push({ name: 'Data Imports', query: { doctype, status: 'Pending' } })
}

function newImport(doctype: string) {
  router.push({ name: 'NewDataImport', params: { doctype } })
}
</script>
