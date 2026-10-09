<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
  </LayoutHeader>
  <DataImportList
    :list="list"
    @open="
      (importName) =>
        router.push({ name: 'DataImport', params: { importName } })
    "
    @new="router.push({ name: 'NewDataImport' })"
  />
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import {
  DataImportList,
  useDataImportList,
} from '@framework/ui/components/DataImport'
import { Breadcrumbs } from 'frappe-ui'
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

// "Review pending imports" opens this list for one doctype and status
const { doctype, status } = route.query
const list = useDataImportList({
  doctype: doctype || undefined,
  status: status || undefined,
})

const breadcrumbs = computed(() =>
  doctype
    ? [
        { label: __('Data Import'), route: { name: 'DataImportList' } },
        { label: __(doctype) },
      ]
    : [{ label: __('Data Import') }],
)
</script>
