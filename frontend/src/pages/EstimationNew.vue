<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <Button :label="__('Cancel')" @click="cancel" />
      <Button
        variant="solid"
        :label="__('Create')"
        :loading="creating"
        @click="createEstimation"
      />
    </template>
  </LayoutHeader>

  <div class="flex-1 overflow-y-auto px-5 py-6">
    <div class="mx-auto max-w-4xl">
      <div
        v-if="tabs.loading"
        class="flex flex-col items-center justify-center gap-3 py-20 text-ink-gray-5"
      >
        <LoadingIndicator class="h-6 w-6" />
        <span>{{ __('Loading...') }}</span>
      </div>

      <FieldLayout
        v-else-if="tabs.data?.length"
        :tabs="tabs.data"
        :data="estimation.doc"
        doctype="CRM Estimation"
      />

      <ErrorMessage v-if="error" class="mt-4" :message="__(error)" />
    </div>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import { Breadcrumbs, Button, ErrorMessage, createResource } from 'frappe-ui'
import { useDocument } from '@/data/document'
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const error = ref(null)
const creating = ref(false)

const { document: estimation } = useDocument('CRM Estimation')

const breadcrumbs = computed(() => [
  { label: __('Estimations'), route: { name: 'Estimations' } },
  { label: __('New Estimation') },
])

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['NewEstimation', 'CRM Estimation'],
  params: { doctype: 'CRM Estimation', type: 'Data Fields' },
  auto: true,
  transform: (_tabs) => {
    _tabs.forEach((tab) =>
      tab.sections.forEach((s) =>
        s.columns.forEach((c) =>
          c.fields.forEach((f) => {
            if (f.fieldtype === 'Table' && !estimation.doc[f.fieldname]) {
              estimation.doc[f.fieldname] = []
            }
          }),
        ),
      ),
    )
    return _tabs
  },
})

onMounted(() => {
  // Filter item per-grid: Revenue di tabel revenue, Expense di tabel expense.
  if (!estimation.fieldPropertyOverrides) estimation.fieldPropertyOverrides = {}
  estimation.fieldPropertyOverrides['revenue_items.type_id'] = {
    link_filters: JSON.stringify({ item_category: 'Revenue' }),
  }
  estimation.fieldPropertyOverrides['expense_items.type_id'] = {
    link_filters: JSON.stringify({ item_category: 'Expense' }),
  }

  if (!estimation.doc.effective_date) {
    estimation.doc.effective_date = new Date().toISOString().slice(0, 10)
  }
  if (!estimation.doc.purpose) estimation.doc.purpose = 'Customer'
})

function createEstimation() {
  error.value = null
  const doc = { ...estimation.doc, doctype: 'CRM Estimation' }
  delete doc.__newDocument

  creating.value = true
  createResource({
    url: 'frappe.client.insert',
    params: { doc },
    auto: true,
    onSuccess(d) {
      creating.value = false
      router.push({ name: 'Estimation', params: { estimationId: d.name } })
    },
    onError(err) {
      creating.value = false
      error.value =
        err.messages?.join('\n') || err.message || __('Failed to create estimation')
    },
  })
}

function cancel() {
  router.push({ name: 'Estimations' })
}
</script>
