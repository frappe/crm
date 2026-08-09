<template>
  <CrudSection
    ref="sectionRef"
    doctype="Payment Entry"
    title="Payments"
    list-resource-url="crm.finance.api.get_customer_payments"
    :list-params="listParams"
    :columns="columns"
    :new-component="PaymentAllocationForm"
    :create-roles="['System Manager', 'Finance Manager', 'AR Accountant']"
    empty-label="No payments found."
  />
</template>

<script setup>
import { ref, markRaw } from 'vue'
import CrudSection from '../components/crud/CrudSection.vue'
import PaymentAllocationFormComp from '../components/crud/PaymentAllocationForm.vue'
import { useCompanyContext } from '../composables/useCompanyContext.js'

const PaymentAllocationForm = markRaw(PaymentAllocationFormComp)
const { company } = useCompanyContext()
const sectionRef = ref(null)

const columns = [
  { key: 'name',               label: 'Payment' },
  { key: 'party',              label: 'Customer' },
  { key: 'posting_date',       label: 'Date',        type: 'date' },
  { key: 'paid_amount',        label: 'Paid',        type: 'currency', align: 'right' },
  { key: 'unallocated_amount', label: 'Unallocated', type: 'currency', align: 'right' },
  { key: 'mode_of_payment',    label: 'Mode' },
]

function listParams() {
  return { company: company.value }
}
</script>
