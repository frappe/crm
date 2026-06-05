<template>
  <Dialog v-model="show" :options="{ title: 'New Quotation', size: '2xl' }">
    <template #body-content>
      <div class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <FormControl v-model="form.subject" label="Subject" required />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <FormControl 
            v-model="form.account" 
            label="Account" 
            type="autocomplete"
            :options="{ doctype: 'CRM Organization' }" 
          />
          <FormControl v-model="form.contact_name" label="Contact" />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <FormControl v-model="form.date" label="Date" type="date" />
          <FormControl 
            v-model="form.inquiry" 
            label="Inquiry" 
            type="autocomplete"
            :options="{ doctype: 'CRM Lead' }" 
          />
        </div>
        <div class="grid grid-cols-3 gap-4">
          <FormControl v-model="form.currency" label="Currency" placeholder="IDR" />
          <FormControl v-model="form.rate" label="Exchange Rate" type="number" placeholder="1" />
          <FormControl v-model="form.cargo1" label="Cargo" />
        </div>
      </div>
    </template>

    <template #actions>
      <Button :label="__('Cancel')" @click="show = false" />
      <Button
        variant="solid"
        :label="__('Create')"
        :loading="createDoc.loading"
        @click="create"
      />
    </template>
  </Dialog>
</template>

<script setup>
import { ref, defineModel } from 'vue'
import { useRouter } from 'vue-router'
import { Dialog, FormControl, Button, createResource } from 'frappe-ui'

const show = defineModel()
const emit = defineEmits(['created'])
const router = useRouter()

const form = ref({
  subject: '',
  account: '',
  contact_name: '',
  date: new Date().toISOString().split('T')[0],
  inquiry: '',
  currency: 'IDR',
  rate: 1,
  cargo1: '',
  state: 'Draft',
})

const createDoc = createResource({
  url: 'frappe.client.insert',
  makeParams() {
    return { doc: { doctype: 'CRM Quotation', ...form.value } }
  },
  onSuccess(doc) {
    show.value = false
    emit('created')
    router.push({ name: 'Quotation', params: { quotationId: doc.name } })
  },
  onError(err) {
    alert(err.message || 'Failed to create')
  },
})

function create() {
  if (!form.value.subject) {
    alert('Subject is required')
    return
  }
  createDoc.submit()
}
</script>