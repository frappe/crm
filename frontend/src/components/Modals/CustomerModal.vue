<template>
  <Dialog v-model="show" :options="dialogOptions">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ __(dialogOptions.title) || __('Untitled') }}
            </h3>
          </div>
          <div class="flex items-center gap-1">
            <Button
              v-if="isManager() || detailMode"
              variant="ghost"
              class="w-7"
              @click="detailMode ? (detailMode = false) : openQuickEntryModal()"
            >
              <EditIcon class="h-4 w-4" />
            </Button>
            <Button variant="ghost" class="w-7" @click="show = false">
              <FeatherIcon name="x" class="h-4 w-4" />
            </Button>
          </div>
        </div>
        <div>
          <div v-if="detailMode" class="flex flex-col gap-3.5">
            <div class="flex h-7 items-center gap-2 text-base text-ink-gray-8" v-for="field in fields" :key="field.name">
              <div class="grid w-7 place-content-center">
                <component :is="field.icon" />
              </div>
              <div>{{ field.value }}</div>
            </div>
          </div>
          <Fields v-else-if="filteredSections" :sections="filteredSections" :data="_customer" />
        </div>
      </div>
      <div v-if="!detailMode" class="px-4 pb-7 pt-4 sm:px-6">
        <div class="space-y-2">
          <Button
            class="w-full"
            v-for="action in dialogOptions.actions"
            :key="action.label"
            v-bind="action"
            :label="__(action.label)"
            :loading="loading"
          />
        </div>
      </div>
    </template>
  </Dialog>
  <AddressModal v-model="showAddressModal" v-model:address="_address" />
</template>

<script setup>
import Fields from '@/components/Fields.vue'
import AddressModal from '@/components/Modals/AddressModal.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import MoneyIcon from '@/components/Icons/MoneyIcon.vue'
import WebsiteIcon from '@/components/Icons/WebsiteIcon.vue'
import CustomersIcon from '@/components/Icons/CustomersIcon.vue'
import TerritoryIcon from '@/components/Icons/TerritoryIcon.vue'
import { usersStore } from '@/stores/users'
import { formatNumberIntoCurrency } from '@/utils'
import { capture } from '@/telemetry'
import { call, FeatherIcon, createResource } from 'frappe-ui'
import { ref, nextTick, watch, computed, h } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  options: {
    type: Object,
    default: {
      redirect: true,
      detailMode: false,
      afterInsert: () => {},
    },
  },
})

const { isManager } = usersStore()

const router = useRouter()
const show = defineModel()
const customer = defineModel('customer')

const loading = ref(false)
const title = ref(null)
const detailMode = ref(false)
const editMode = ref(false)
let _address = ref({})
let _customer = ref({
  customer_name: '',
  website: '',
  annual_revenue: '',
  no_of_employees: '1-10',
  industry: '',
})

const showAddressModal = ref(false)

let doc = ref({})

async function updateCustomer() {
  const old = { ...doc.value }
  const newOrg = { ..._customer.value }

  const nameChanged = old.customer_name !== newOrg.customer_name
  delete old.customer_name
  delete newOrg.customer_name

  const otherFieldChanged = JSON.stringify(old) !== JSON.stringify(newOrg)
  const values = newOrg

  if (!nameChanged && !otherFieldChanged) {
    show.value = false
    return
  }

  let name
  loading.value = true
  if (nameChanged) {
    name = await callRenameDoc()
  }
  if (otherFieldChanged) {
    name = await callSetValue(values)
  }
  handleCustomerUpdate({ name }, nameChanged)
}

async function callRenameDoc() {
  const d = await call('frappe.client.rename_doc', {
    doctype: 'Customer',
    old_name: doc.value?.customer_name,
    new_name: _customer.value.customer_name,
  })
  loading.value = false
  return d
}

async function callSetValue(values) {
  const d = await call('frappe.client.set_value', {
    doctype: 'Customer',
    name: _customer.value.name,
    fieldname: values,
  })
  loading.value = false
  return d.name
}

async function callInsertDoc() {
  const doc = await call('frappe.client.insert', {
    doc: {
      doctype: 'Customer',
      ..._customer.value,
    },
  })
  loading.value = false
  if (doc.name) {
    capture('customer_created')
    handleCustomerUpdate(doc)
  }
}

function handleCustomerUpdate(doc, renamed = false) {
  if (doc.name && (props.options.redirect || renamed)) {
    router.push({
      name: 'Customer',
      params: { customerId: doc.name },
    })
  } else {
    customer.value.reload?.()
  }
  show.value = false
  props.options.afterInsert && props.options.afterInsert(doc)
}

const dialogOptions = computed(() => {
  let title = !editMode.value ? __('New Customer') : __(_customer.value.customer_name)
  let size = detailMode.value ? '' : 'xl'
  let actions = detailMode.value
    ? []
    : [
        {
          label: editMode.value ? __('Save') : __('Create'),
          variant: 'solid',
          onClick: () => (editMode.value ? updateCustomer() : callInsertDoc()),
        },
      ]

  return { title, size, actions }
})

const fields = computed(() => {
  let details = [
    {
      icon: CustomersIcon,
      name: 'customer_name',
      value: _customer.value.customer_name,
    },
    {
      icon: WebsiteIcon,
      name: 'website',
      value: _customer.value.website,
    },
    {
      icon: TerritoryIcon,
      name: 'territory',
      value: _customer.value.territory,
    },
    {
      icon: MoneyIcon,
      name: 'annual_revenue',
      value: formatNumberIntoCurrency(_customer.value.annual_revenue, _customer.value.currency),
    },
    {
      icon: h(FeatherIcon, { name: 'hash', class: 'h-4 w-4' }),
      name: 'no_of_employees',
      value: _customer.value.no_of_employees,
    },
    {
      icon: h(FeatherIcon, { name: 'briefcase', class: 'h-4 w-4' }),
      name: 'industry',
      value: _customer.value.industry,
    },
  ]

  return details.filter((field) => field.value)
})

const sections = createResource({
  url: 'next_crm.ncrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['quickEntryFields', 'Customer'],
  params: { doctype: 'Customer', type: 'Quick Entry' },
  auto: true,
})

const filteredSections = computed(() => {
  let allSections = sections.data || []
  if (!allSections.length) return []

  allSections.forEach((s) => {
    s.fields.forEach((field) => {
      if (field.name == 'address') {
        field.create = (value, close) => {
          _customer.value.address = value
          _address.value = {}
          showAddressModal.value = true
          close()
        }
        field.edit = async (addr) => {
          _address.value = await call('frappe.client.get', {
            doctype: 'Address',
            name: addr,
          })
          showAddressModal.value = true
        }
      }
    })
  })

  return allSections
})

watch(
  () => show.value,
  (value) => {
    if (!value) return
    editMode.value = false
    detailMode.value = props.options.detailMode
    nextTick(() => {
      // TODO: Issue with FormControl
      // title.value.el.focus()
      doc.value = customer.value?.doc || customer.value || {}
      _customer.value = { ...doc.value }
      if (_customer.value.name) {
        editMode.value = true
      }
    })
  },
)

const showQuickEntryModal = defineModel('quickEntry')

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  nextTick(() => {
    show.value = false
  })
}
</script>
