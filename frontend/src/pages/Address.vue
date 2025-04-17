<template>
  <LayoutHeader v-if="address.doc">
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
        </template>
      </Breadcrumbs>
    </template>
  </LayoutHeader>
  <div ref="parentRef" class="flex h-full">
    <Resizer
      v-if="address.doc"
      :parent="$refs.parentRef"
      class="flex h-full flex-col overflow-hidden border-r"
    >
      <div class="border-b">
        <div class="flex flex-col items-start justify-start gap-4 p-5">
          <div class="flex gap-4 items-center">
            <div class="flex flex-col gap-2 truncate">
              <div class="truncate text-2xl font-medium text-ink-gray-9">
                <span>{{ address.doc.name }}</span>
              </div>
              <ErrorMessage :message="__(error)" />
            </div>
          </div>
          <div class="flex gap-1.5">
            <Button
              :label="__('Delete')"
              theme="red"
              size="sm"
              @click="deleteAddress"
            >
              <template #prefix>
                <FeatherIcon name="trash-2" class="h-4 w-4" />
              </template>
            </Button>
          </div>
        </div>
      </div>
      <div
        v-if="fieldsLayout.data"
        class="flex flex-1 flex-col justify-between overflow-hidden"
      >
        <div class="flex flex-col overflow-y-auto">
          <div
            v-for="(section, i) in fieldsLayout.data"
            :key="section.label"
            class="flex flex-col p-3"
            :class="{ 'border-b': i !== fieldsLayout.data.length - 1 }"
          >
            <Section :is-opened="section.opened" :label="section.label">
              <template #actions>
                <Button
                  v-if="i == 0 && isManager()"
                  variant="ghost"
                  class="w-7"
                  @click="showSidePanelModal = true"
                >
                  <EditIcon class="h-4 w-4" />
                </Button>
              </template>
              <SectionFields
                v-if="section.fields"
                :fields="section.fields"
                :isLastSection="i == fieldsLayout.data.length - 1"
                v-model="address.doc"
                @update="updateField"
              />
            </Section>
          </div>
        </div>
      </div>
    </Resizer>
    <Tabs as="div" v-model="tabIndex" :tabs="tabs">
      <template #tab-item="{ tab, selected }">
        <button
          class="group flex items-center gap-2 border-b border-transparent py-2.5 text-base text-ink-gray-5 duration-300 ease-in-out hover:border-gray-400 hover:text-ink-gray-9"
          :class="{ 'text-ink-gray-9': selected }"
        >
          <component v-if="tab.icon" :is="tab.icon" class="h-5" />
          {{ __(tab.label) }}
          <Badge
            class="group-hover:bg-surface-gray-9"
            :class="[selected ? 'bg-surface-gray-9' : 'bg-surface-gray-5']"
            variant="solid"
            theme="gray"
            size="sm"
          >
            {{ tab.count || 0 }}
          </Badge>
        </button>
      </template>
      <template #tab-panel="{ tab }">
        <CustomersListView
          class="mt-4"
          v-if="tab.label === 'Customers' && rows?.length"
          :rows="rows"
          :columns="columns"
          :options="{ selectable: false, showTooltip: false }"
        />
        <ProspectsListView
          class="mt-4"
          v-if="tab.label === 'Prospects' && rows?.length"
          :rows="rows"
          :columns="columns"
          :options="{ selectable: false, showTooltip: false }"
        />
        <div
          v-if="!rows.length"
          class="grid flex-1 place-items-center text-xl font-medium text-ink-gray-4"
        >
          <div class="flex flex-col items-center justify-center space-y-3">
            <component :is="tab.icon" class="!h-10 !w-10" />
            <div>{{ __('No {0} Found', [__(tab.label)]) }}</div>
          </div>
        </div>
      </template>
    </Tabs>
  </div>
  <SidePanelModal
    v-if="showSidePanelModal"
    v-model="showSidePanelModal"
    doctype="Address"
    @reload="() => fieldsLayout.reload()"
  />
  <QuickEntryModal
    v-if="showQuickEntryModal"
    v-model="showQuickEntryModal"
    doctype="Address"
  />
  <AddressModal v-model="showAddressModal" v-model:address="_address" />
</template>
  
<script setup>
import Resizer from '@/components/Resizer.vue'
import Section from '@/components/Section.vue'
import SectionFields from '@/components/SectionFields.vue'
import SidePanelModal from '@/components/Settings/SidePanelModal.vue'
import Icon from '@/components/Icon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import QuickEntryModal from '@/components/Modals/QuickEntryModal.vue'
import AddressModal from '@/components/Modals/AddressModal.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import CustomersIcon from '@/components/Icons/CustomersIcon.vue'
import ProspectsIcon from '@/components/Icons/ProspectsIcon.vue'
import CustomersListView from '@/components/ListViews/CustomersListView.vue'
import ProspectsListView from '@/components/ListViews/ProspectsListView.vue'
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import { customersStore } from '@/stores/customers.js'
import { statusesStore } from '@/stores/statuses'
import { getView } from '@/utils/view'
import {
  dateFormat,
  dateTooltipFormat,
  timeAgo,
  createToast,
} from '@/utils'
import {
  Breadcrumbs,
  Tabs,
  call,
  createListResource,
  createDocumentResource,
  usePageMeta,
  createResource,
} from 'frappe-ui'
import { h, computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const props = defineProps({
  addressId: {
    type: String,
    required: true,
  },
})
  
const { getUser, isManager } = usersStore()
const { $dialog } = globalStore()
const { getDealStatus } = statusesStore()
const { getCustomer } = customersStore()
const showSidePanelModal = ref(false)
const showQuickEntryModal = ref(false)

const route = useRoute()
const router = useRouter()

const tabIndex = ref(0)
const tabs = [
  {
    label: 'Customers',
    icon: h(CustomersIcon, { class: 'h-4 w-4' }),
    count: computed(() => customers.value.data?.length),
  },
  {
    label: 'Prospects',
    icon: h(ProspectsIcon, { class: 'h-4 w-4' }),
    count: computed(() => prospects.value.data?.length),
  },
]

async function getCustomersList() { 
  const customer_names = await call('next_crm.api.address.get_linked_docs', {
    link_doctype: 'Customer',
    address: props.addressId,
  })

  const list = createListResource({
    type: 'list',
    doctype: 'Customer',
    fields: [
      'name',
      "customer_name",
      'industry',
      'website',
      'modified',
      'image',
    ],
    filters: {
      customer_name: ['in', customer_names],
    },
    orderBy: 'modified desc',
    pageLength: 20,
    auto: true,
  })

  return list
}

const customers = ref([]);

async function setCustomersList() {
  customers.value = await getCustomersList()
}
setCustomersList()

function getCustomerRowObject(customer) {

  return {
    name: customer.name,
    customer_name: {
      label: customer.name,
      logo: customer?.image,
    },
    website: customer.website,
    Industry: customer.industry,
    modified: {
      label: dateFormat(customer.modified, dateTooltipFormat),
      timeAgo: __(timeAgo(customer.modified)),
    },
  }
}

async function getProspectsList() { 
  const prospect_names = await call('next_crm.api.address.get_linked_docs', {
    link_doctype: 'Prospect',
    address: props.addressId,
  })

  const list = createListResource({
    type: 'list',
    doctype: 'Prospect',
    fields: [
      'name',
      "company_name",
      'industry',
      'website',
      'modified',
    ],
    filters: {
      company_name: ['in', prospect_names],
    },
    orderBy: 'modified desc',
    pageLength: 20,
    auto: true,
  })

  return list
}

const prospects = ref([]);

async function setProspectsList() {
  prospects.value = await getProspectsList()
}
setProspectsList()

const rows = computed(() => {
  let list = ref([])
  if (tabIndex.value === 0)
    list.value = customers.value
  else if (tabIndex.value === 1)
    list.value = prospects.value

  if (!list.value?.data) return []
  return list.value?.data.map((row) => {
    if (tabIndex.value === 0)
      return getCustomerRowObject(row)
    else if (tabIndex.value === 1)
      return getProspectRowObject(row)
  })
})

function getProspectRowObject(prospect) {
  return {
    name: prospect.name,
    company_name: prospect.company_name,
    website: prospect.website,
    Industry: prospect.industry,
    modified: {
      label: dateFormat(prospect.modified, dateTooltipFormat),
      timeAgo: __(timeAgo(prospect.modified)),
    },
  }
}

const address = createDocumentResource({
  doctype: 'Address',
  name: props.addressId,
  cache: ['address', props.addressId],
  fields: ['*'],
  auto: true,
})

async function updateField(fieldname, value) {
  await address.setValue.submit({
    [fieldname]: value,
  })
  createToast({
    title: __('Address updated'),
    icon: 'check',
    iconClasses: 'text-ink-green-3',
  })
}
  
const breadcrumbs = computed(() => {
  let items = [{ label: __('Addresses'), route: { name: 'Addresses' } }]

  if (route.query.view || route.query.viewType) {
    let view = getView(
      route.query.view,
      route.query.viewType,
      'Address',
    )
    if (view) {
      items.push({
        label: __(view.label),
        icon: view.icon,
        route: {
          name: 'Addresses',
          params: { viewType: route.query.viewType },
          query: { view: route.query.view },
        },
      })
    }
  }
  
  items.push({
    label: props.addressId,
    route: {
      name: 'Address',
      params: { addressId: props.addressId },
    },
  })
  return items
})
  
usePageMeta(() => {
  return {
    title: props.addressId,
  }
})

async function deleteAddress() {
  $dialog({
    title: __('Delete address'),
    message: __('Are you sure you want to delete this address?'),
    actions: [
      {
        label: __('Delete'),
        theme: 'red',
        variant: 'solid',
        async onClick(close) {
          try {
            await call('frappe.client.delete', {
              doctype: 'Address',
              name: props.addressId,
            })
            close()
            router.push({ name: 'Addresses' })
          } catch (error) {
            const errorMessage = 
              error.name === 'LinkExistsError' || error.message.includes('LinkExistsError')
                ? __('Cannot delete this address because it is linked to other records.')
                : __('Failed to delete the address. Please try again later.');
            createToast({
              title: __('Error'),
              text: errorMessage,
              icon: 'x',
              iconClasses: 'text-ink-red-4',
            });
          }
        },
      },
    ],
  })
}

const showAddressModal = ref(false)
const _address = ref({})

const fieldsLayout = createResource({
  url: 'next_crm.api.doc.get_sidebar_fields',
  cache: ['fieldsLayout', props.addressId],
  params: { doctype: 'Address', name: props.addressId },
  auto: true,
  transform: (data) => getParsedFields(data),
})
  
function getParsedFields(data) {
  return data.map((section) => {
    return {
      ...section,
      fields: computed(() =>
        section.fields.map((field) => {
          if (field.name === 'address') {
            return {
              ...field,
              create: (value, close) => {
                _address.value.address = value
                _address.value = {}
                showAddressModal.value = true
                close()
              },
              edit: async (addr) => {
                _address.value = await call('frappe.client.get', {
                  doctype: 'Address',
                  name: addr,
                })
                showAddressModal.value = true
              },
            }
          } else {
            return field
          }
        }),
      ),
    }
  })
}

const columns = computed(() => {
  if (tabIndex.value === 0)
    return customerColumns
  else if (tabIndex.value === 1)
    return prospectColumns
})

const customerColumns = [
  {
    label: __('Name'),
    key: 'customer_name',
    width: '11rem',
  },
  {
    label: __('Website'),
    key: 'website',
    width: '9rem',
  },
  {
    label: __('Industry'),
    key: 'industry',
    width: '10rem',
  },
  {
    label: __('Last modified'),
    key: 'modified',
    width: '8rem',
  },
]

const prospectColumns = [
  {
    label: __('Name'),
    key: 'company_name',
    width: '11rem',
  },
  {
    label: __('Website'),
    key: 'website',
    width: '9rem',
  },
  {
    label: __('Industry'),
    key: 'industry',
    width: '10rem',
  },
  {
    label: __('Last modified'),
    key: 'modified',
    width: '8rem',
  },
]
</script>
