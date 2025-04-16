<template>
  <LayoutHeader v-if="address.data">
    <header
      class="relative flex h-10.5 items-center justify-between gap-2 py-2.5 pl-2"
    >
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
        </template>
      </Breadcrumbs>
    </header>
  </LayoutHeader>
  <div v-if="address.data" class="flex flex-col h-full overflow-hidden">
    <div class="flex flex-col items-start justify-start gap-4 p-4">
      <div class="flex gap-4 items-center">
        <div class="flex flex-col gap-2 truncate">
          <div class="truncate text-lg font-medium text-ink-gray-9">
            <span>{{ address.data.name }}</span>
          </div>
          <div class="flex items-center gap-1.5">
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
          <ErrorMessage :message="__(error)" />
        </div>
      </div>
    </div>
    <Tabs as="div" v-model="tabIndex" :tabs="tabs" class="overflow-auto">
      <TabList class="!px-4" v-slot="{ tab, selected }">
        <button
          v-if="tab.name == 'Customers'"
          class="group flex items-center gap-2 border-b border-transparent py-2.5 text-base text-ink-gray-5 duration-300 ease-in-out hover:border-outline-gray-3 hover:text-ink-gray-9"
          :class="{ 'text-ink-gray-9': selected }"
        >
          <component v-if="tab.icon" :is="tab.icon" class="h-5" />
          {{ __(tab.label) }}
          <Badge
            class="group-hover:bg-surface-gray-7"
            :class="[selected ? 'bg-surface-gray-7' : 'bg-gray-600']"
            variant="solid"
            theme="gray"
            size="sm"
          >
            {{ tab.count }}
          </Badge>
        </button>
      </TabList>
      <TabPanel v-slot="{ tab }">
        <div v-if="tab.name == 'Details'">
          <div
            v-if="fieldsLayout.data"
            class="flex flex-1 flex-col justify-between overflow-hidden"
          >
            <div class="flex flex-col overflow-y-auto">
              <div
                v-for="(section, i) in fieldsLayout.data"
                :key="section.label"
                class="flex flex-col px-2 py-3 sm:p-3"
                :class="{ 'border-b': i !== fieldsLayout.data.length - 1 }"
              >
                <Section :is-opened="section.opened" :label="section.label">
                  <SectionFields
                    :fields="section.fields"
                    :isLastSection="i == fieldsLayout.data.length - 1"
                    v-model="address.data"
                    @update="updateField"
                  />
                </Section>
              </div>
            </div>
          </div>
        </div>
        <CustomersListView
          v-else-if="tab.label === 'Customers' && rows.length"
          class="mt-4"
          :rows="rows"
          :columns="columns"
          :options="{ selectable: false, showTooltip: false }"
        />
        <div
          v-if="tab.label === 'Customers' && !rows.length"
          class="grid flex-1 place-items-center text-xl font-medium text-ink-gray-4"
        >
          <div class="flex flex-col items-center justify-center space-y-3">
            <component :is="tab.icon" class="!h-10 !w-10" />
            <div>{{ __('No {0} Found', [__(tab.label)]) }}</div>
          </div>
        </div>
      </TabPanel>
    </Tabs>
  </div>
  <AddressModal v-model="showAddressModal" v-model:address="_address" />
</template>

<script setup>
import Icon from '@/components/Icon.vue'
import Section from '@/components/Section.vue'
import SectionFields from '@/components/SectionFields.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import CustomersIcon from '@/components/Icons/CustomersIcon.vue'
import CustomersListView from '@/components/ListViews/CustomersListView.vue'
import AddressModal from '@/components/Modals/AddressModal.vue'
import {
  dateFormat,
  dateTooltipFormat,
  timeAgo,
  formatNumberIntoCurrency,
  createToast,
} from '@/utils'
import { getView } from '@/utils/view'
import { globalStore } from '@/stores/global.js'
import { usersStore } from '@/stores/users.js'
import { customersStore } from '@/stores/customers.js'
import { statusesStore } from '@/stores/statuses'
import { callEnabled } from '@/composables/settings'
import {
  Breadcrumbs,
  Avatar,
  FileUploader,
  Tabs,
  TabList,
  TabPanel,
  call,
  createListResource,
  createResource,
  usePageMeta,
  Dropdown,
} from 'frappe-ui'
import { ref, computed, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const { $dialog, makeCall } = globalStore()

const { getUser } = usersStore()
const { getCustomer } = customersStore()
const { getDealStatus } = statusesStore()

const props = defineProps({
  addressId: {
    type: String,
    required: true,
  },
})

const route = useRoute()
const router = useRouter()

const showAddressModal = ref(false)
const _address = ref({})

const address = createResource({
  url: 'next_crm.api.address.get_address',
  cache: ['address', props.addressId],
  params: {
    name: props.addressId,
  },
  auto: true,
  transform: (data) => {
    return {
      ...data,
      actual_mobile_no: data.mobile_no,
      mobile_no: data.mobile_no,
    }
  },
})

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

const tabIndex = ref(0)
const tabs = [
  {
    name: 'Details',
    label: __('Details'),
    icon: DetailsIcon,
  },
  {
    name: 'Customers',
    label: __('Customers'),
    icon: h(CustomersIcon, { class: 'h-4 w-4' }),
    count: computed(() => customers.value.data?.length),
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

const customers = ref();

async function setCustomersList() {
  customers.value = await getCustomersList()
}
setCustomersList()

const rows = computed(() => {
  if (!customers.value.data || customers.value.data == []) return []
  return customers.value.data.map((row) => getCustomerRowObject(row))
})

function getCustomerRowObject(customer) {

  return {
    name: customer.name,
    customer_name: {
      label: customer.name,
      logo: customer?.image,
    },
    website: customer.website,
    Industry: customer.industry,
    mobile_no: customer.contact_mobile,
    modified: {
      label: dateFormat(customer.modified, dateTooltipFormat),
      timeAgo: __(timeAgo(customer.modified)),
    },
  }
}

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
          if (field.name === 'email_id') {
            return {
              ...field,
              type: 'dropdown',
              options:
                address.data?.email_ids?.map((email) => {
                  return {
                    name: email.name,
                    value: email.email_id,
                    selected: email.email_id === address.data.email_id,
                    placeholder: 'john@doe.com',
                    onClick: () => {
                      _address.value.email_id = email.email_id
                      setAsPrimary('email', email.email_id)
                    },
                    onSave: (option, isNew) => {
                      if (isNew) {
                        createNew('email', option.value)
                        if (address.data.email_ids.length === 1) {
                          _address.value.email_id = option.value
                        }
                      } else {
                        editOption(
                          'Address Email',
                          option.name,
                          'email_id',
                          option.value,
                        )
                      }
                    },
                    onDelete: async (option, isNew) => {
                      address.data.email_ids = address.data.email_ids.filter(
                        (email) => email.name !== option.name,
                      )
                      !isNew &&
                        (await deleteOption('Address Email', option.name))
                      if (_address.value.email_id === option.value) {
                        if (address.data.email_ids.length === 0) {
                          _address.value.email_id = ''
                        } else {
                          _address.value.email_id = address.data.email_ids.find(
                            (email) => email.is_primary,
                          )?.email_id
                        }
                      }
                    },
                  }
                }) || [],
              create: () => {
                address.data?.email_ids?.push({
                  name: 'new-1',
                  value: '',
                  selected: false,
                  isNew: true,
                })
              },
            }
          } else if (field.name === 'mobile_no') {
            return {
              ...field,
              type: 'dropdown',
              options:
                address.data?.phone_nos?.map((phone) => {
                  return {
                    name: phone.name,
                    value: phone.phone,
                    selected: phone.phone === address.data.actual_mobile_no,
                    onClick: () => {
                      _address.value.actual_mobile_no = phone.phone
                      _address.value.mobile_no = phone.phone
                      setAsPrimary('mobile_no', phone.phone)
                    },
                    onSave: (option, isNew) => {
                      if (isNew) {
                        createNew('phone', option.value)
                        if (address.data.phone_nos.length === 1) {
                          _address.value.actual_mobile_no = option.value
                        }
                      } else {
                        editOption(
                          'Address Phone',
                          option.name,
                          'phone',
                          option.value,
                        )
                      }
                    },
                    onDelete: async (option, isNew) => {
                      address.data.phone_nos = address.data.phone_nos.filter(
                        (phone) => phone.name !== option.name,
                      )
                      !isNew &&
                        (await deleteOption('Address Phone', option.name))
                      if (_address.value.actual_mobile_no === option.value) {
                        if (address.data.phone_nos.length === 0) {
                          _address.value.actual_mobile_no = ''
                        } else {
                          _address.value.actual_mobile_no =
                            address.data.phone_nos.find(
                              (phone) => phone.is_primary_mobile_no,
                            )?.phone
                        }
                      }
                    },
                  }
                }) || [],
              create: () => {
                address.data?.phone_nos?.push({
                  name: 'new-1',
                  value: '',
                  selected: false,
                  isNew: true,
                })
              },
            }
          } else if (field.name === 'address') {
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

async function setAsPrimary(field, value) {
  let d = await call('next_crm.api.address.set_as_primary', {
    address: address.data.name,
    field,
    value,
  })
  if (d) {
    address.reload()
    createToast({
      title: 'Address updated',
      icon: 'check',
      iconClasses: 'text-ink-green-3',
    })
  }
}

async function createNew(field, value) {
  if (!value) return
  let d = await call('next_crm.api.address.create_new', {
    address: address.data.name,
    field,
    value,
  })
  if (d) {
    address.reload()
    createToast({
      title: 'Address updated',
      icon: 'check',
      iconClasses: 'text-ink-green-3',
    })
  }
}

async function editOption(doctype, name, fieldname, value) {
  let d = await call('frappe.client.set_value', {
    doctype,
    name,
    fieldname,
    value,
  })
  if (d) {
    address.reload()
    createToast({
      title: 'Address updated',
      icon: 'check',
      iconClasses: 'text-ink-green-3',
    })
  }
}

async function deleteOption(doctype, name) {
  await call('frappe.client.delete', {
    doctype,
    name,
  })
  await address.reload()
  createToast({
    title: 'Address updated',
    icon: 'check',
    iconClasses: 'text-ink-green-3',
  })
}

async function updateField(fieldname, value) {
  await call('frappe.client.set_value', {
    doctype: 'Address',
    name: props.addressId,
    fieldname,
    value,
  })
  createToast({
    title: 'Address updated',
    icon: 'check',
    iconClasses: 'text-ink-green-3',
  })

  address.reload()
}

const columns = computed(() => customerColumns)

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
</script>
