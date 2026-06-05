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
        @click="createDeal"
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
        :data="deal.doc"
        doctype="CRM Deal"
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
import { usersStore } from '@/stores/users'
import { statusesStore } from '@/stores/statuses'
import { computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const router = useRouter()
const route = useRoute()
const error = ref(null)
const creating = ref(false)
const { getUser } = usersStore()
const { statusOptions } = statusesStore()

// Dokumen baru (CRM Deal = Inquiry).
const { document: deal } = useDocument('CRM Deal')

const breadcrumbs = computed(() => [
  { label: __('Deals'), route: { name: 'Deals' } },
  { label: __('New Deal') },
])

const dealStatuses = computed(() => statusOptions('deal'))

// Layout yang SAMA dengan field yang di-set untuk inquiry (Data Fields).
const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['NewDeal', 'CRM Deal'],
  params: { doctype: 'CRM Deal', type: 'Data Fields' },
  auto: true,
  transform: (_tabs) => {
    _tabs.forEach((tab) =>
      tab.sections.forEach((s) =>
        s.columns.forEach((c) =>
          c.fields.forEach((f) => {
            if (f.fieldtype === 'Table' && !deal.doc[f.fieldname]) {
              deal.doc[f.fieldname] = []
            }
          }),
        ),
      ),
    )
    return _tabs
  },
})

onMounted(() => {
  // Default dari query (mis. klik "+" di kolom kanban).
  if (route.query && Object.keys(route.query).length) {
    Object.assign(deal.doc, route.query)
  }
  if (!deal.doc.deal_owner) deal.doc.deal_owner = getUser().name
  // Status wajib tapi tidak ada di layout → default ke status pertama.
  if (!deal.doc.status && dealStatuses.value?.[0]?.value) {
    deal.doc.status = dealStatuses.value[0].value
  }
  if (!deal.doc.currency) deal.doc.currency = 'IDR'
  if (!deal.doc.exchange_rate) deal.doc.exchange_rate = 1
})

function createDeal() {
  error.value = null
  const doc = { ...deal.doc, doctype: 'CRM Deal' }
  delete doc.__newDocument

  creating.value = true
  createResource({
    url: 'frappe.client.insert',
    params: { doc },
    auto: true,
    onSuccess(d) {
      creating.value = false
      router.push({ name: 'Deal', params: { dealId: d.name } })
    },
    onError(err) {
      creating.value = false
      error.value =
        err.messages?.join('\n') || err.message || __('Failed to create inquiry')
    },
  })
}

function cancel() {
  router.push({ name: 'Deals' })
}
</script>
