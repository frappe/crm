<template>
    <div class="space-y-6">
        <!-- Main -->
        <Section title="Quote Information">
            <div class="grid grid-cols-2 gap-6">
                <!-- Kolom Kiri -->
                <div class="space-y-4">
                    <FormField label="Attention" v-model="form.attention" />
                    <FormField label="Subject" v-model="form.subject" required />
                    <FormField label="Cargo" v-model="form.cargo1" />
                    <FormField label="Packaging" v-model="form.cargo1" />
                    <FormField label="Loading" v-model="form.loading" />
                    <FormField label="Unloading" v-model="form.unloading" />
                </div>

                <!-- Kolom Kanan -->
                <div class="space-y-4">
                    <FormField label="Date" v-model="form.date" type="date" />
                    <InquiryField label="Inquiry" v-model="form.inquiry" @select="onInquirySelected" />
                    <FormField label="Account" v-model="form.account" readonly />
                    <FormField label="Cost Center" v-model="form.cost_center" type="link" doctype="Cost Center" />
                    <FormField label="Currency" v-model="form.currency" type="link" doctype="Currency" />
                    <FormField label="Exchange Rate" v-model="form.rate" type="number" />
                </div>
            </div>
        </Section>

        <!-- Products -->
        <Section title="Products">
            <template #actions>
                <div class="flex items-center gap-3">
                    <span class="text-sm text-ink-gray-5">
                        Net Total:
                        <strong class="text-ink-gray-9">{{ formatCurrency(netTotal) }}</strong>
                    </span>
                    <Button size="sm" :label="__('Add Product')" iconLeft="plus" @click="addProduct" />
                </div>
            </template>
            <ChildTable :rows="form.products" :columns="productColumns" @update="updateProduct"
                @remove="removeProduct" />
        </Section>

        <!-- Additional Items -->
        <Section title="Additionals">
            <div class="grid grid-cols-2 gap-6">
                <div class="space-y-4">
                    <h4 class="text-sm font-semibold text-ink-gray-7 border-b border-outline-gray-2 pb-2">
                        Rate Include
                    </h4>
                    <FormField label="Title" v-model="form.additional1_title" />
                    <FormField label="Item" v-model="form.additional1_item" type="textarea" />
                    <FormField label="Amount" v-model="form.additional1_amount" type="currency" />
                </div>

                <div class="space-y-4">
                    <h4 class="text-sm font-semibold text-ink-gray-7 border-b border-outline-gray-2 pb-2">
                        Rate Exclude
                    </h4>
                    <FormField label="Title" v-model="form.additional2_title" />
                    <FormField label="Item" v-model="form.additional2_item" type="textarea" />
                    <FormField label="Amount" v-model="form.additional2_amount" type="currency" />
                </div>
            </div>
        </Section>

        <!-- Terms & Payment (2 kolom) -->
        <div class="grid grid-cols-2 gap-6">
            <Section title="Terms & Conditions">
                <div class="space-y-4">
                    <FormField label="Term Title" v-model="form.term_title" />
                    <FormField label="Term Detail" v-model="form.term_detail" type="textarea" />
                </div>
            </Section>

            <Section title="Payment Term">
                <div class="space-y-4">
                    <FormField label="Validity" v-model="form.validity" />
                    <FormField label="Payment Term" v-model="form.payterm" />
                </div>
            </Section>
        </div>

        <Section title="Rate Info">
            <div class="space-y-4">
                <div class="grid grid-cols-2 gap-6">
                    <FormField label="Rate Include" v-model="form.rate_include" type="textarea" />
                    <FormField label="Rate Exclude" v-model="form.rate_exclude" type="textarea" />
                </div>
                <FormField label="Remark" v-model="form.remark" type="textarea" />
            </div>
        </Section>
    </div>
</template>

<script setup>
import { Button } from 'frappe-ui'
import Section from './shared/Section.vue'
import FormField from './shared/FormField.vue'
import ChildTable from './shared/ChildTable.vue'
import InquiryField from './shared/InquiryField.vue'
import { computed } from 'vue'


const form = defineModel({ required: true })

const netTotal = computed(() => {
    return (form.value.products || []).reduce(
        (sum, p) => sum + (Number(p.amount) || 0),
        0
    )
})

const productColumns = [
    { fieldname: 'product', label: 'Product', type: 'text' },
    { fieldname: 'remark', label: 'Remark', type: 'text' },
    { fieldname: 'qty', label: 'Qty', type: 'number', align: 'right' },
    { fieldname: 'price', label: 'Price', type: 'currency', align: 'right' },
    { fieldname: 'amount', label: 'Amount', type: 'currency', align: 'right', readonly: true },
]

const additionalColumns = [
    { fieldname: 'type', label: 'Type', type: 'select', options: ['additional1', 'additional2'] },
    { fieldname: 'title', label: 'Title', type: 'text' },
    { fieldname: 'item_name', label: 'Item Name', type: 'text' },
    { fieldname: 'price', label: 'Price', type: 'currency', align: 'right' },
]

function onInquirySelected(deal) {
    console.log('Selected deal:', deal)
    form.value.account = deal.organization || ''
}

function addProduct() {
    form.value.products.push({ product: '', remark: '', qty: 1, price: 0, amount: 0 })
}

function removeProduct(idx) {
    form.value.products.splice(idx, 1)
}

function updateProduct(idx, field, val) {
    form.value.products[idx][field] = val
    if (field === 'qty' || field === 'price') {
        const row = form.value.products[idx]
        row.amount = (Number(row.qty) || 0) * (Number(row.price) || 0)
    }
}

function addAdditional() {
    form.value.additionals.push({ type: 'additional1', title: '', item_name: '', price: 0 })
}

function removeAdditional(idx) {
    form.value.additionals.splice(idx, 1)
}

function updateAdditional(idx, field, val) {
    form.value.additionals[idx][field] = val
}

function formatCurrency(v) {
    if (!v) return 'Rp 0'
    return new Intl.NumberFormat('id-ID', {
        style: 'currency',
        currency: 'IDR',
        maximumFractionDigits: 0,
    }).format(v)
}
</script>