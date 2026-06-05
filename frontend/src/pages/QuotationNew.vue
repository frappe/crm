<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <Button :label="__('Cancel')" @click="cancel" />
      <Button
        variant="solid"
        :label="__('Save')"
        :loading="creating"
        @click="createQuotation"
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
        :data="quotation.doc"
        doctype="CRM Quotation"
      />

      <ErrorMessage v-if="error" class="mt-4" :message="__(error)" />
    </div>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import { Breadcrumbs, Button, ErrorMessage, createResource, call } from 'frappe-ui'
import { useDocument } from '@/data/document'
import { sessionStore } from '@/stores/session'
import { computed, ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const session = sessionStore()
const error = ref(null)
const creating = ref(false)

// Dokumen baru — sama seperti flow create Deal/Lead.
const { document: quotation } = useDocument('CRM Quotation')

const breadcrumbs = computed(() => [
  { label: __('Quotations'), route: { name: 'Quotations' } },
  { label: __('New Quotation') },
])

// Layout yang SAMA dengan halaman detail (Tab Data).
const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  params: { doctype: 'CRM Quotation', type: 'Data Fields' },
  auto: true,
  transform: (_tabs) => {
    // Inisialisasi field Table (products) agar grid bisa dirender.
    _tabs.forEach((tab) =>
      tab.sections.forEach((s) =>
        s.columns.forEach((c) =>
          c.fields.forEach((f) => {
            if (f.fieldtype === 'Table' && !quotation.doc[f.fieldname]) {
              quotation.doc[f.fieldname] = []
            }
          }),
        ),
      ),
    )
    return _tabs
  },
})

// Inquiry yang boleh dipilih: status Won DAN belum dipakai quotation lain.
const availableInquiries = createResource({
  url: 'crm.api.quotation.get_available_inquiries',
  auto: true,
})

watch(
  [() => tabs.data, () => availableInquiries.data],
  ([tabsData, avail]) => {
    if (!tabsData || !avail) return
    const names = avail.map((d) => d.name)
    tabsData.forEach((tab) =>
      tab.sections.forEach((s) =>
        s.columns.forEach((c) =>
          c.fields.forEach((f) => {
            if (f.fieldname === 'inquiry') {
              // Batasi dropdown ke inquiry yang tersedia (Won + belum dipakai).
              f.link_filters = JSON.stringify({ name: ['in', names] })
            }
          }),
        ),
      ),
    )
  },
  { immediate: true },
)

// Saat inquiry dipilih → isi account & subject langsung dari deal
// (live, supaya account read-only langsung muncul tanpa menunggu save).
watch(
  () => quotation.doc.inquiry,
  async (inq) => {
    if (!inq) return
    const deal = await call('frappe.client.get_value', {
      doctype: 'CRM Deal',
      filters: { name: inq },
      fieldname: ['organization', 'subject'],
    })
    if (!deal) return
    quotation.doc.account = deal.organization || ''
    if (!quotation.doc.subject) quotation.doc.subject = deal.subject || ''
  },
)

// Kalkulasi live: amount = qty * price per baris + net_total.
watch(
  () => (quotation.doc.products || []).map((p) => `${p.qty}|${p.price}`).join(';'),
  () => {
    let total = 0
    ;(quotation.doc.products || []).forEach((p) => {
      p.amount = (Number(p.qty) || 0) * (Number(p.price) || 0)
      total += p.amount
    })
    quotation.doc.net_total = total
  },
)

onMounted(() => {
  // Paksa Account selalu tampil (read-only) walau belum terisi —
  // Frappe biasanya menyembunyikan field read-only yang kosong.
  if (!quotation.fieldPropertyOverrides) quotation.fieldPropertyOverrides = {}
  quotation.fieldPropertyOverrides.account = { hidden: false }

  // Default yang nyaman (server tetap menerapkan default doctype saat insert).
  if (!quotation.doc.date) {
    quotation.doc.date = new Date().toISOString().slice(0, 10)
  }
  if (!quotation.doc.currency) quotation.doc.currency = 'IDR'
  if (!quotation.doc.rate) quotation.doc.rate = 1
  // Printed By default = user yang sedang login (yang membuat).
  if (!quotation.doc.printed_by) quotation.doc.printed_by = session.user
})

function createQuotation() {
  error.value = null
  const doc = { ...quotation.doc, doctype: 'CRM Quotation' }
  delete doc.__newDocument

  creating.value = true
  createResource({
    url: 'frappe.client.insert',
    params: { doc },
    auto: true,
    onSuccess(d) {
      creating.value = false
      router.push({ name: 'Quotation', params: { quotationId: d.name } })
    },
    onError(err) {
      creating.value = false
      error.value =
        err.messages?.join('\n') || err.message || __('Failed to create quotation')
    },
  })
}

function cancel() {
  router.push({ name: 'Quotations' })
}
</script>
