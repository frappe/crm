<template>
  <LayoutHeader v-if="customer.doc">
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
  <div v-if="customer.doc" class="flex flex-col h-full overflow-hidden">
    <FileUploader
      @success="changeCustomerImage"
      :validateFile="validateFile"
    >
      <template #default="{ openFileSelector, error }">
        <div class="flex flex-col items-start justify-start gap-4 p-4">
          <div class="flex gap-4 items-center">
            <div class="group relative h-14.5 w-14.5">
              <Avatar
                size="3xl"
                class="h-14.5 w-14.5"
                :label="customer.doc.customer_name"
                :image="customer.doc.image"
              />
              <component
                :is="customer.doc.image ? Dropdown : 'div'"
                v-bind="
                  customer.doc.image
                    ? {
                        options: [
                          {
                            icon: 'upload',
                            label: customer.doc.image
                              ? __('Change image')
                              : __('Upload image'),
                            onClick: openFileSelector,
                          },
                          {
                            icon: 'trash-2',
                            label: __('Remove image'),
                            onClick: () => changeCustomerImage(''),
                          },
                        ],
                      }
                    : { onClick: openFileSelector }
                "
                class="!absolute bottom-0 left-0 right-0"
              >
                <div
                  class="z-1 absolute bottom-0 left-0 right-0 flex h-14 cursor-pointer items-center justify-center rounded-b-full bg-black bg-opacity-40 pt-5 opacity-0 duration-300 ease-in-out group-hover:opacity-100"
                  style="
                    -webkit-clip-path: inset(22px 0 0 0);
                    clip-path: inset(22px 0 0 0);
                  "
                >
                  <CameraIcon class="h-6 w-6 cursor-pointer text-white" />
                </div>
              </component>
            </div>
            <div class="flex flex-col gap-2 truncate">
              <div class="truncate text-lg font-medium">
                {{ customer.doc.name }}
              </div>
              <div class="flex items-center gap-1.5">
                <Button @click="openWebsite">
                  <FeatherIcon name="link" class="h-4 w-4" />
                </Button>
                <Button
                  :label="__('Delete')"
                  theme="red"
                  size="sm"
                  @click="deleteCustomer"
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
      </template>
    </FileUploader>
    <Tabs
      v-model="tabIndex"
      :tabs="tabs"
      tablistClass="!px-4"
      class="overflow-auto"
    >
      <template #tab="{ tab, selected }">
        <button
          v-if="tab.name !== 'Details'"
          class="group flex items-center gap-2 border-b border-transparent py-2.5 text-base text-gray-600 duration-300 ease-in-out hover:border-gray-400 hover:text-gray-900"
          :class="{ 'text-gray-900': selected }"
        >
          <component v-if="tab.icon" :is="tab.icon" class="h-5" />
          {{ __(tab.label) }}
          <Badge
            class="group-hover:bg-gray-900"
            :class="[selected ? 'bg-gray-900' : 'bg-gray-600']"
            variant="solid"
            theme="gray"
            size="sm"
          >
            {{ tab.count }}
          </Badge>
        </button>
      </template>
      <template #default="{ tab }">
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
                    v-model="customer.doc"
                    @update="updateField"
                  />
                </Section>
              </div>
            </div>
          </div>
        </div>
        <OpportunitiesListView
          class="mt-4"
          v-if="tab.label === 'Opportunities' && rows.length"
          :rows="rows"
          :columns="columns"
          :options="{ selectable: false, showTooltip: false }"
        />
        <ContactsListView
          class="mt-4"
          v-if="tab.label === 'Contacts' && rows.length"
          :rows="rows"
          :columns="columns"
          :options="{ selectable: false, showTooltip: false }"
        />
        <div
          v-if="!rows.length && tab.name !== 'Details'"
          class="grid flex-1 place-items-center text-xl font-medium text-gray-500"
        >
          <div class="flex flex-col items-center justify-center space-y-3">
            <component :is="tab.icon" class="!h-10 !w-10" />
            <div>{{ __('No {0} Found', [__(tab.label)]) }}</div>
          </div>
        </div>
      </template>
    </Tabs>
  </div>
  <AddressModal v-model="showAddressModal" v-model:address="_address" />
</template>

<script setup>
import Section from '@/components/Section.vue'
import SectionFields from '@/components/SectionFields.vue'
import Icon from '@/components/Icon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import AddressModal from '@/components/Modals/AddressModal.vue'
import OpportunitiesListView from '@/components/ListViews/OpportunitiesListView.vue'
import ContactsListView from '@/components/ListViews/ContactsListView.vue'
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import OpportunitiesIcon from '@/components/Icons/OpportunitiesIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import { statusesStore } from '@/stores/statuses'
import { getView } from '@/utils/view'
import {
  dateFormat,
  dateTooltipFormat,
  timeAgo,
  formatNumberIntoCurrency,
  createToast,
} from '@/utils'
import {
  Breadcrumbs,
  Avatar,
  FileUploader,
  Dropdown,
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
  customerId: {
    type: String,
    required: true,
  },
})

const { getUser } = usersStore()
const { $dialog } = globalStore()
const { getDealStatus } = statusesStore()

const route = useRoute()
const router = useRouter()

const customer = createDocumentResource({
  doctype: 'Customer',
  name: props.customerId,
  cache: ['customer', props.customerId],
  fields: ['*'],
  auto: true,
})

async function updateField(fieldname, value) {
  await customer.setValue.submit({
    [fieldname]: value,
  })
  createToast({
    title: __('Customer updated'),
    icon: 'check',
    iconClasses: 'text-green-600',
  })
}

const breadcrumbs = computed(() => {
  let items = [{ label: __('Customers'), route: { name: 'Customers' } }]

  if (route.query.view || route.query.viewType) {
    let view = getView(
      route.query.view,
      route.query.viewType,
      'Customer',
    )
    if (view) {
      items.push({
        label: __(view.label),
        icon: view.icon,
        route: {
          name: 'Customers',
          params: { viewType: route.query.viewType },
          query: { view: route.query.view },
        },
      })
    }
  }

  items.push({
    label: props.customerId,
    route: {
      name: 'Customer',
      params: { customerId: props.customerId },
    },
  })
  return items
})

usePageMeta(() => {
  return {
    title: props.customerId,
  }
})

function validateFile(file) {
  let extn = file.name.split('.').pop().toLowerCase()
  if (!['png', 'jpg', 'jpeg'].includes(extn)) {
    return __('Only PNG and JPG images are allowed')
  }
}

async function changeCustomerImage(file) {
  await call('frappe.client.set_value', {
    doctype: 'Customer',
    name: props.customerId,
    fieldname: 'image',
    value: file?.file_url || '',
  })
  customer.reload()
}

async function deleteCustomer() {
  $dialog({
    title: __('Delete customer'),
    message: __('Are you sure you want to delete this customer?'),
    actions: [
      {
        label: __('Delete'),
        theme: 'red',
        variant: 'solid',
        async onClick(close) {
          try {
            await call('frappe.client.delete', {
              doctype: 'Customer',
              name: props.customerId,
            })
            close()
            router.push({ name: 'Customers' })
          } catch (error) {
            const errorMessage = 
              error.name === 'LinkExistsError' || error.message.includes('LinkExistsError')
                ? __('Cannot delete this customer because it is linked to other records.')
                : __('Failed to delete the customer. Please try again later.');
            createToast({
              title: __('Error'),
              text: errorMessage,
              icon: 'x',
              iconClasses: 'text-red-600',
            });
          }
        },
      },
    ],
  })
}

function openWebsite() {
  if (!customer.doc.website)
    createToast({
      title: __('Website not found'),
      icon: 'x',
      iconClasses: 'text-red-600',
    })
  else window.open(customer.doc.website, '_blank')
}

const showAddressModal = ref(false)
const _customer = ref({})
const _address = ref({})

const fieldsLayout = createResource({
  url: 'next_crm.api.doc.get_sidebar_fields',
  cache: ['fieldsLayout', props.customerId],
  params: { doctype: 'Customer', name: props.customerId },
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
                _customer.value.address = value
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

const tabIndex = ref(0)
const tabs = [
  {
    name: 'Details',
    label: __('Details'),
    icon: DetailsIcon,
  },
  {
    name: 'Opportunities',
    label: __('Opportunities'),
    icon: h(OpportunitiesIcon, { class: 'h-4 w-4' }),
    count: computed(() => opportunities.data?.length),
  },
  {
    name: 'Contacts',
    label: __('Contacts'),
    icon: h(ContactsIcon, { class: 'h-4 w-4' }),
    count: computed(() => contacts.data?.length),
  },
]

const opportunities = createListResource({
  type: 'list',
  doctype: 'Opportunity',
  cache: ['opportunities', props.customerId],
  fields: [
    'name',
    'customer',
    'currency',
    'opportunity_amount',
    'status',
    'contact_email',
    'contact_mobile',
    'opportunity_owner',
    'modified',
  ],
  filters: {
    customer: props.customerId,
  },
  orderBy: 'modified desc',
  pageLength: 20,
  auto: true,
})

const contacts = createListResource({
  type: 'list',
  doctype: 'Contact',
  cache: ['contacts', props.customerId],
  fields: [
    'name',
    'full_name',
    'image',
    'email_id',
    'mobile_no',
    'company_name',
    'modified',
  ],
  filters: {
    company_name: props.customerId,
  },
  orderBy: 'modified desc',
  pageLength: 20,
  auto: true,
})

const rows = computed(() => {
  let list = []
  list = !tabIndex.value ? opportunities : contacts

  if (!list.data) return []

  return list.data.map((row) => {
    return !tabIndex.value ? getOpportunityRowObject(row) : getContactRowObject(row)
  })
})

const columns = computed(() => {
  return tabIndex.value === 0 ? opportunityColumns : contactColumns
})

function getOpportunityRowObject(opportunity) {
  return {
    name: opportunity.name,
    customer: {
      label: opportunity.customer,
      logo: props.customer?.image,
    },
    opportunity_amount: formatNumberIntoCurrency(
      opportunity.opportunity_amount,
      opportunity.currency,
    ),
    status: {
      label: opportunity.status,
      color: getDealStatus(opportunity.status)?.iconColorClass,
    },
    email: opportunity.contact_email,
    mobile_no: opportunity.contact_mobile,
    opportunity_owner: {
      label: opportunity.opportunity_owner && getUser(opportunity.opportunity_owner).full_name,
      ...(opportunity.opportunity_owner && getUser(opportunity.opportunity_owner)),
    },
    modified: {
      label: dateFormat(opportunity.modified, dateTooltipFormat),
      timeAgo: __(timeAgo(opportunity.modified)),
    },
  }
}

function getContactRowObject(contact) {
  return {
    name: contact.name,
    full_name: {
      label: contact.full_name,
      image_label: contact.full_name,
      image: contact.image,
    },
    email: contact.email_id,
    mobile_no: contact.mobile_no,
    company_name: {
      label: contact.company_name,
      logo: props.customer?.image,
    },
    modified: {
      label: dateFormat(contact.modified, dateTooltipFormat),
      timeAgo: __(timeAgo(contact.modified)),
    },
  }
}

const opportunityColumns = [
  {
    label: __('Customer'),
    key: 'customer',
    width: '11rem',
  },
  {
    label: __('Amount'),
    key: 'opportunity_amount',
    width: '9rem',
  },
  {
    label: __('Status'),
    key: 'status',
    width: '10rem',
  },
  {
    label: __('Email'),
    key: 'contact_email',
    width: '12rem',
  },
  {
    label: __('Mobile no'),
    key: 'contact_mobile',
    width: '11rem',
  },
  {
    label: __('Opportunity owner'),
    key: 'opportunity_owner',
    width: '10rem',
  },
  {
    label: __('Last modified'),
    key: 'modified',
    width: '8rem',
  },
]

const contactColumns = [
  {
    label: __('Name'),
    key: 'full_name',
    width: '17rem',
  },
  {
    label: __('Email'),
    key: 'email',
    width: '12rem',
  },
  {
    label: __('Phone'),
    key: 'mobile_no',
    width: '12rem',
  },
  {
    label: __('Customer'),
    key: 'company_name',
    width: '12rem',
  },
  {
    label: __('Last modified'),
    key: 'modified',
    width: '8rem',
  },
]
</script>
