<template>
  <div class="space-y-6">
    <!-- Quote Information -->
    <Section title="Quote Information">
      <div class="grid grid-cols-2 gap-6">
        <!-- Kolom Kiri -->
        <div class="space-y-4">
          <EditableField label="Attention" v-model="doc.attention" @save="save('attention', $event)" />
          <EditableField label="Subject" v-model="doc.subject" @save="save('subject', $event)" />
          <EditableField label="Cargo" v-model="doc.cargo1" @save="save('cargo1', $event)" />
          <EditableField label="Packaging" v-model="doc.cargo1" @save="save('cargo1', $event)" />
          <EditableField label="Loading" v-model="doc.loading" @save="save('loading', $event)" />
          <EditableField label="Unloading" v-model="doc.unloading" @save="save('unloading', $event)" />
        </div>

        <!-- Kolom Kanan -->
        <div class="space-y-4">
          <EditableField label="Date" v-model="doc.date" type="date" @save="save('date', $event)" />
          <InquiryField label="Inquiry" v-model="doc.inquiry" @save="save('inquiry', $event)"
            @select="onInquirySelected" />
          <div>
            <label class="text-xs font-medium uppercase tracking-wide text-ink-gray-5">Account</label>
            <div
              class="mt-1 w-full rounded border border-outline-gray-2 bg-surface-gray-2 px-2 py-1.5 text-sm text-ink-gray-7">
              {{ doc.account || '-' }}
            </div>
          </div>
          <EditableField label="Cost Center" v-model="doc.cost_center" type="link" doctype="Cost Center"
            @save="save('cost_center', $event)" />
          <EditableField label="Currency" v-model="doc.currency" type="link" doctype="Currency"
            @save="save('currency', $event)" />
          <EditableField label="Exchange Rate" v-model="doc.rate" type="number" @save="save('rate', $event)" />
        </div>
      </div>
    </Section>

    <!-- Products -->
    <Section title="Products">
      <template #actions>
        <div class="flex items-center gap-3">
          <span class="text-sm text-ink-gray-5">
            Net Total:
            <strong class="text-ink-gray-9">{{ formatCurrency(doc.net_total) }}</strong>
          </span>
          <Button size="sm" :label="__('Add Product')" iconLeft="plus" @click="addProduct" />
        </div>
      </template>
      <ChildTable :rows="doc.products || []" :columns="productColumns"
        @update="(idx, field, val) => updateChild('products', idx, field, val)"
        @remove="(idx) => removeChild('products', idx)" />
    </Section>

    <!-- Additionals -->
    <Section title="Additionals">
      <div class="grid grid-cols-2 gap-6">
        <div class="space-y-4">
          <h4 class="text-sm font-semibold text-ink-gray-7 border-b border-outline-gray-2 pb-2">
            Rate Include
          </h4>
          <EditableField label="Title" v-model="doc.additional1_title" @save="save('additional1_title', $event)" />
          <EditableField label="Item" v-model="doc.additional1_item" type="textarea"
            @save="save('additional1_item', $event)" />
          <EditableField label="Amount" v-model="doc.additional1_amount" type="currency"
            @save="save('additional1_amount', $event)" />
        </div>

        <div class="space-y-4">
          <h4 class="text-sm font-semibold text-ink-gray-7 border-b border-outline-gray-2 pb-2">
            Rate Exclude
          </h4>
          <EditableField label="Title" v-model="doc.additional2_title" @save="save('additional2_title', $event)" />
          <EditableField label="Item" v-model="doc.additional2_item" type="textarea"
            @save="save('additional2_item', $event)" />
          <EditableField label="Amount" v-model="doc.additional2_amount" type="currency"
            @save="save('additional2_amount', $event)" />
        </div>
      </div>
    </Section>

    <!-- Terms & Payment (2 kolom) -->
    <div class="grid grid-cols-2 gap-6">
      <Section title="Terms & Conditions">
        <div class="space-y-4">
          <EditableField label="Term Title" v-model="doc.term_title" @save="save('term_title', $event)" />
          <EditableField label="Term Detail" v-model="doc.term_detail" type="textarea"
            @save="save('term_detail', $event)" />
        </div>
      </Section>

      <Section title="Payment Term">
        <div class="space-y-4">
          <EditableField label="Validity" v-model="doc.validity" @save="save('validity', $event)" />
          <EditableField label="Payment Term" v-model="doc.payterm" @save="save('payterm', $event)" />
        </div>
      </Section>
    </div>

    <!-- Rate Info -->
    <Section title="Rate Info">
      <div class="space-y-4">
        <div class="grid grid-cols-2 gap-6">
          <EditableField label="Rate Include" v-model="doc.rate_include" type="textarea"
            @save="save('rate_include', $event)" />
          <EditableField label="Rate Exclude" v-model="doc.rate_exclude" type="textarea"
            @save="save('rate_exclude', $event)" />
        </div>
        <EditableField label="Remark" v-model="doc.remark" type="textarea" @save="save('remark', $event)" />
      </div>
    </Section>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Button } from 'frappe-ui'
import Section from './shared/Section.vue'
import EditableField from './shared/EditableField.vue'
import ChildTable from './shared/ChildTable.vue'
import InquiryField from './shared/InquiryField.vue'

const props = defineProps(['quotation'])
const doc = computed(() => props.quotation.doc)

const productColumns = [
  { fieldname: 'product', label: 'Product', type: 'text' },
  { fieldname: 'remark', label: 'Remark', type: 'text' },
  { fieldname: 'qty', label: 'Qty', type: 'number', align: 'right' },
  { fieldname: 'price', label: 'Price', type: 'currency', align: 'right' },
  { fieldname: 'amount', label: 'Amount', type: 'currency', align: 'right', readonly: true },
]

// Save single field
function save(field, value) {
  props.quotation.setValue.submit({ [field]: value })
}

// Update child table row
function updateChild(table, idx, field, val) {
  doc.value[table][idx][field] = val
  if (table === 'products' && (field === 'qty' || field === 'price')) {
    const row = doc.value[table][idx]
    row.amount = (Number(row.qty) || 0) * (Number(row.price) || 0)
  }
  props.quotation.save.submit()
}

function removeChild(table, idx) {
  doc.value[table].splice(idx, 1)
  props.quotation.save.submit()
}

function addProduct() {
  if (!doc.value.products) doc.value.products = []
  doc.value.products.push({ product: '', remark: '', qty: 1, price: 0, amount: 0 })
}

function onInquirySelected(deal) {
  if (deal?.organization) {
    save('account', deal.organization)
  }
}

function formatCurrency(v) {
  if (!v) return '-'
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0,
  }).format(v)
}
</script>