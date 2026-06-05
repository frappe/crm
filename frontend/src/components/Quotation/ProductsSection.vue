<template>
  <div class="border-t border-outline-gray-modals pt-6 mt-6">
    <div class="mb-4 flex items-center justify-between">
      <h3 class="text-base font-semibold text-ink-gray-9">Products</h3>
      <div class="flex items-center gap-3">
        <span class="text-sm text-ink-gray-5">
          Net Total: <strong class="text-ink-gray-9">{{ formatCurrency(quotation.doc?.net_total) }}</strong>
        </span>
        <Button size="sm" :label="__('Add Product')" iconLeft="plus" @click="addProduct" />
      </div>
    </div>
    <ChildTable
      :rows="quotation.doc?.products || []"
      :columns="productColumns"
      @update="updateRow"
      @remove="removeRow"
    />
  </div>
</template>

<script setup>
import { Button } from 'frappe-ui'
import ChildTable from '@/components/Quotation/shared/ChildTable.vue'

const props = defineProps(['quotation'])

const productColumns = [
  { fieldname: 'product', label: 'Product', type: 'text' },
  { fieldname: 'remark', label: 'Remark', type: 'text' },
  { fieldname: 'qty', label: 'Qty', type: 'number', align: 'right' },
  { fieldname: 'price', label: 'Price', type: 'currency', align: 'right' },
  { fieldname: 'amount', label: 'Amount', type: 'currency', align: 'right', readonly: true },
]

function updateRow(idx, field, val) {
  const products = props.quotation.doc.products
  products[idx][field] = val
  if (field === 'qty' || field === 'price') {
    products[idx].amount = (Number(products[idx].qty) || 0) * (Number(products[idx].price) || 0)
  }
  props.quotation.save.submit()
}

function removeRow(idx) {
  props.quotation.doc.products.splice(idx, 1)
  props.quotation.save.submit()
}

function addProduct() {
  if (!props.quotation.doc.products) props.quotation.doc.products = []
  props.quotation.doc.products.push({ product: '', remark: '', qty: 1, price: 0, amount: 0 })
  props.quotation.save.submit()
}

function formatCurrency(v) {
  if (!v) return 'IDR 0'
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0,
  }).format(v)
}
</script>