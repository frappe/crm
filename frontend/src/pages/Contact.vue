<template>
  <LayoutHeader v-if="contact.data">
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
      v-if="contact.data"
      :parent="$refs.parentRef"
      class="flex h-full flex-col overflow-hidden border-r"
    >
      <div class="border-b">
        <FileUploader
          @success="changeContactImage"
          :validateFile="validateFile"
        >
          <template #default="{ openFileSelector, error }">
            <div class="flex flex-col gap-4 p-5">
              <div class="flex gap-4 items-center">
                <div class="group relative h-15.5 w-15.5">
                  <Avatar
                    size="3xl"
                    class="h-15.5 w-15.5"
                    :label="contact.data.full_name"
                    :image="contact.data.image"
                  />
                  <component
                    :is="contact.data.image ? Dropdown : 'div'"
                    v-bind="
                      contact.data.image
                        ? {
                            options: [
                              {
                                icon: 'upload',
                                label: contact.data.image
                                  ? __('Change image')
                                  : __('Upload image'),
                                onClick: openFileSelector,
                              },
                              {
                                icon: 'trash-2',
                                label: __('Remove image'),
                                onClick: () => changeContactImage(''),
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
                <div class="flex flex-col gap-2 truncate text-ink-gray-9">
                  <div class="truncate text-2xl font-medium">
                    <span v-if="contact.data.salutation">
                      {{ contact.data.salutation + '. ' }}
                    </span>
                    <span>{{ contact.data.full_name }}</span>
                  </div>
                  <div
                    v-if="contact.data.company_name"
                    class="flex items-center gap-1.5 text-base text-ink-gray-8"
                  >
                    <Avatar
                      size="xs"
                      :label="contact.data.company_name"
                      :image="
                        getOrganization(contact.data.company_name)
                          ?.organization_logo
                      "
                    />
                    <span class="">{{ contact.data.company_name }}</span>
                  </div>
                  <ErrorMessage :message="__(error)" />
                </div>
              </div>
              <div class="flex p-3">
                <div class="flex gap-1.5">
                  <Button
                    v-if="contact.data.actual_mobile_no && callEnabled"
                    size="sm"
                    class="dark:text-white dark:hover:bg-gray-700"
                    @click="makeCall(contact.data.actual_mobile_no)"
                  >
                    <template #prefix>
                      <PhoneIcon class="h-4 w-4" />
                    </template>
                    {{ __('Make Call') }}
                  </Button>

                  <Button
                    v-if="contact.data.actual_mobile_no && !callEnabled"
                    size="sm"
                    class="dark:text-white dark:hover:bg-gray-700"
                    @click="trackPhoneActivities('phone')"
                  >
                    <template #prefix>
                      <PhoneIcon class="h-4 w-4" />
                    </template>
                    {{ __('Make Call') }}
                  </Button>

                  <Button
                    v-if="contact.data.actual_mobile_no"
                    size="sm"
                    class="dark:text-white dark:hover:bg-gray-700"
                    @click="trackPhoneActivities('whatsapp')"
                  >
                    <template #prefix>
                      <WhatsAppIcon class="h-4 w-4" />
                    </template>
                    {{ __('Chat') }}
                  </Button>
                </div>

                <Button
                  :label="__('Delete')"
                  variant="ghost"
                  theme="red"
                  size="sm"
                  class="dark:text-red-400 dark:hover:bg-gray-700"
                  @click="deleteContact"
                >
                  <template #prefix>
                    <FeatherIcon name="trash-2" class="h-4 w-4" />
                  </template>
                  {{ __('Delete') }}  
                </Button>
              </div>
            </div>
          </template>
        </FileUploader>
      </div>
      <div
        v-if="fieldsLayout.data"
        class="flex flex-1 flex-col justify-between overflow-hidden"
      >
        <div class="flex flex-col overflow-y-auto dark-scrollbar">
          <div
            v-for="(section, i) in fieldsLayout.data"
            :key="section.label"
            class="flex flex-col p-3"
            :class="{ 'border-b': i !== fieldsLayout.data.length - 1 }"
          >
            <Section :label="section.label" :opened="section.opened">
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
              <SidePanelLayout
                v-if="section.fields"
                :fields="section.fields"
                :isLastSection="i == fieldsLayout.data.length - 1"
                v-model="contact.data"
                @update="updateField"
              />
            </Section>
          </div>
        </div>
      </div>
    </Resizer>
    <Tabs class="!h-full" v-model="tabIndex" :tabs="tabs">
      <template #tab="{ tab, selected }">
        <button
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
      </template>
      <template #default="{ tab }">
        <DealsListView
          v-if="tab.label === 'Deals' && rows.length"
          class="mt-4"
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
            <div>{{ __('No Deals Found') }}</div>
          </div>
        </div>
      </template>
    </Tabs>
  </div>
  <SidePanelModal
    v-if="showSidePanelModal"
    v-model="showSidePanelModal"
    doctype="Contact"
    @reload="() => fieldsLayout.reload()"
  />
  <AddressModal v-model="showAddressModal" v-model:address="_address" />
  <ContactModal v-model="showContactModal" :contact="contact" :options="{ redirect: false, afterInsert: () => contact.reload() }" />
</template>

<script setup>
import Resizer from '@/components/Resizer.vue'
import Icon from '@/components/Icon.vue'
import Section from '@/components/Section.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import DealsListView from '@/components/ListViews/DealsListView.vue'
import SidePanelModal from '@/components/Modals/SidePanelModal.vue'
import AddressModal from '@/components/Modals/AddressModal.vue'
import ContactModal from '@/components/Modals/ContactModal.vue'
import {
  formatDate,
  timeAgo,
  formatNumberIntoCurrency,
  createToast,
} from '@/utils'
import { getView } from '@/utils/view'
import { globalStore } from '@/stores/global.js'
import { usersStore } from '@/stores/users.js'
import { organizationsStore } from '@/stores/organizations.js'
import { statusesStore } from '@/stores/statuses'
import { callEnabled } from '@/composables/settings'
import { translateDealStatus } from '@/utils/dealStatusTranslations'
import {
  Breadcrumbs,
  Avatar,
  FileUploader,
  Tabs,
  call,
  createResource,
  usePageMeta,
  Dropdown,
} from 'frappe-ui'
import { ref, computed, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { normalizePhoneNumber } from '@/utils/communicationUtils'
import { trackCommunication } from '@/utils/communicationUtils'

const { $dialog, makeCall } = globalStore()

const { getUser, isManager } = usersStore()
const { getOrganization } = organizationsStore()
const { getDealStatus } = statusesStore()

const props = defineProps({
  contactId: {
    type: String,
    required: true,
  },
})

const route = useRoute()
const router = useRouter()

const showAddressModal = ref(false)
const showSidePanelModal = ref(false)
const showContactModal = ref(false)
const _contact = ref({})
const _address = ref({})

const contact = createResource({
  url: 'crm.api.contact.get_contact',
  cache: ['contact', props.contactId],
  params: {
    name: props.contactId,
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
  let items = [{ label: __('Contacts'), route: { name: 'Contacts' } }]

  if (route.query.view || route.query.viewType) {
    let view = getView(route.query.view, route.query.viewType, 'Contact')
    if (view) {
      items.push({
        label: __(view.label),
        icon: view.icon,
        route: {
          name: 'Contacts',
          params: { viewType: route.query.viewType },
          query: { view: route.query.view },
        },
      })
    }
  }

  items.push({
    label: contact.data?.full_name,
    route: { name: 'Contact', params: { contactId: props.contactId } },
  })
  return items
})

usePageMeta(() => {
  return {
    title: contact.data?.full_name || contact.data?.name,
  }
})

function validateFile(file) {
  let extn = file.name.split('.').pop().toLowerCase()
  if (!['png', 'jpg', 'jpeg'].includes(extn)) {
    return __('Only PNG and JPG images are allowed')
  }
}

async function changeContactImage(file) {
  await call('frappe.client.set_value', {
    doctype: 'Contact',
    name: props.contactId,
    fieldname: 'image',
    value: file?.file_url || '',
  })
  contact.reload()
}

async function deleteContact() {
  $dialog({
    title: __('Delete contact'),
    message: __('Are you sure you want to delete this contact?'),
    actions: [
      {
        label: __('Delete'),
        theme: 'red',
        variant: 'solid',
        async onClick(close) {
          await call('frappe.client.delete', {
            doctype: 'Contact',
            name: props.contactId,
          })
          close()
          router.push({ name: 'Contacts' })
        },
      },
    ],
  })
}

const tabIndex = ref(0)
const tabs = [
  {
    label: 'Deals',
    icon: h(DealsIcon, { class: 'h-4 w-4' }),
    count: computed(() => deals.data?.length),
  },
]

const deals = createResource({
  url: 'crm.api.contact.get_linked_deals',
  cache: ['deals', props.contactId],
  params: {
    contact: props.contactId,
  },
  auto: true,
})

const rows = computed(() => {
  if (!deals.data || deals.data == []) return []

  return deals.data.map((row) => getDealRowObject(row))
})

const fieldsLayout = createResource({
  url: 'crm.api.doc.get_sidebar_fields',
  cache: ['fieldsLayout', props.contactId],
  params: { doctype: 'Contact', name: props.contactId },
  auto: true,
  transform: (data) => getParsedFields(data),
})

function getParsedFields(data) {
  if (!data?.[0]?.sections) return []
  
  const sectionList = data[0].sections
  sectionList.forEach((section) => {
    // Convert array of field names to array of field objects if needed
    if (Array.isArray(section.fields) && typeof section.fields[0] === 'string') {
      section.fields = section.fields.map(fieldName => {
        // Try to get field metadata from both the API response and fields_meta
        const field = (typeof section.fields_meta === 'object' && section.fields_meta[fieldName]) || 
                     (contact.data?.fields_meta && contact.data.fields_meta[fieldName]) || {}
        
        // Get translated field label
        const translatedLabel = __(field.label || fieldName.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' '))
        
        // Determine placeholder verb based on field type
        const getPlaceholderVerb = (fieldtype) => {
          switch(fieldtype?.toLowerCase()) {
            case 'select':
            case 'link':
              return __('Select')
            case 'date':
            case 'datetime':
              return __('Set')
            default:
              return __('Enter')
          }
        }

        // Base field data with translations
        const fieldData = {
          name: fieldName,
          label: translatedLabel,
          type: field.fieldtype || 'text',
          all_properties: field || {},
          placeholder: field.placeholder || `${getPlaceholderVerb(field.fieldtype)} ${translatedLabel}`,
          create: (value, close) => {
            showContactModal.value = true
            close?.()
          }
        }

        // Handle special case for email_id field
        if (fieldName === 'email_id') {
          const translatedLabel = __('Email')
          return {
            ...fieldData,
            type: 'dropdown',
            options: computed(() => 
              contact.data?.email_ids?.map((email) => ({
                name: email.name,
                value: email.email_id,
                selected: email.email_id === contact.data.email_id,
                placeholder: `${__('Enter')} ${translatedLabel}`,
                isNew: email.isNew,
                onClick: () => {
                  _contact.value.email_id = email.email_id
                  setAsPrimary('email', email.email_id)
                },
                onSave: (option, isNew) => {
                  if (isNew) {
                    createNew('email', option.value)
                    if (contact.data.email_ids.length === 1) {
                      _contact.value.email_id = option.value
                    }
                  } else {
                    editOption('email', option.name, option.value)
                  }
                },
                onDelete: () => {
                  if (email.isNew) {
                    contact.data.email_ids = contact.data.email_ids.filter(e => e.name !== email.name)
                    if (_contact.value.email_id === email.email_id) {
                      _contact.value.email_id = contact.data.email_ids.find(e => e.is_primary)?.email_id || ''
                    }
                  } else {
                    deleteOption('email', email.name)
                  }
                }
              })) || []
            ),
            create: () => {
              contact.data.email_ids = contact.data.email_ids || []
              const newEmail = {
                name: 'new-1',
                email_id: '',
                is_primary: contact.data.email_ids.length === 0,
                selected: false,
                isNew: true,
              }
              contact.data.email_ids.push(newEmail)
            }
          }
        }

        // Handle special case for gender field
        if (fieldName === 'gender') {
          return {
            ...fieldData,
            type: 'select',
            options: [
              { label: __('Male'), value: 'Male' },
              { label: __('Female'), value: 'Female' }
            ],
            placeholder: `${__('Select')} ${translatedLabel}`
          }
        }

        // Handle special case for mobile_no field
        if (fieldName === 'mobile_no') {
          const translatedLabel = __('Phone')
          return {
            ...fieldData,
            type: 'dropdown',
            options: computed(() => 
              contact.data?.phone_nos?.map((phone) => ({
                name: phone.name,
                value: phone.phone,
                selected: phone.phone === contact.data.actual_mobile_no,
                placeholder: `${__('Enter')} ${translatedLabel}`,
                isNew: phone.isNew,
                onClick: () => {
                  _contact.value.actual_mobile_no = phone.phone
                  _contact.value.mobile_no = phone.phone
                  setAsPrimary('mobile_no', phone.phone)
                },
                onSave: (option, isNew) => {
                  if (isNew) {
                    createNew('phone', option.value)
                    if (contact.data.phone_nos.length === 1) {
                      _contact.value.actual_mobile_no = option.value
                    }
                  } else {
                    editOption('phone', option.name, option.value)
                  }
                },
                onDelete: () => {
                  if (phone.isNew) {
                    contact.data.phone_nos = contact.data.phone_nos.filter(p => p.name !== phone.name)
                    if (_contact.value.actual_mobile_no === phone.phone) {
                      _contact.value.actual_mobile_no = contact.data.phone_nos.find(p => p.is_primary_mobile_no)?.phone || ''
                    }
                  } else {
                    deleteOption('phone', phone.name)
                  }
                }
              })) || []
            ),
            create: () => {
              contact.data.phone_nos = contact.data.phone_nos || []
              const newPhone = {
                name: 'new-1',
                phone: '',
                is_primary_mobile_no: contact.data.phone_nos.length === 0,
                selected: false,
                isNew: true,
              }
              contact.data.phone_nos.push(newPhone)
            }
          }
        }

        // Handle special case for address field
        if (fieldName === 'address') {
          return {
            ...fieldData,
            type: 'link',
            doctype: 'Address',
            create: (value, close) => {
              _address.value = { address_title: value }
              showAddressModal.value = true
              close()
            },
            edit: async (addr) => {
              _address.value = await call('frappe.client.get', {
                doctype: 'Address',
                name: addr,
              })
              showAddressModal.value = true
            }
          }
        }

        // Handle field types that need special treatment
        switch (field.fieldtype?.toLowerCase()) {
          case 'select':
            // Convert select fields to use Link component for better UX
            fieldData.type = 'link'
            if (field.options) {
              fieldData.options = field.options.split('\n').map(option => ({
                label: __(option),
                value: option
              }))
              if (!fieldData.options.find(opt => opt.value === '')) {
                fieldData.options.unshift({ label: '', value: '' })
              }
            }
            break

          case 'link':
            fieldData.type = 'link'
            fieldData.doctype = field.options
            break

          case 'date':
            fieldData.type = 'Date'
            break
        }

        return fieldData
      })
    }
  })
  
  return sectionList
}

async function setAsPrimary(type, value) {
  await call('crm.api.contact.set_as_primary', {
    contact: contact.data.name,
    field: type,
    value,
  })
  await contact.reload()
  createToast({
    title: __('Contact Updated'),
    icon: 'check',
    iconClasses: 'text-ink-green-3',
  })
}

async function editOption(type, name, value) {
  const doctype = type === 'email' ? 'Contact Email' : 'Contact Phone'
  const fieldname = type === 'email' ? 'email_id' : 'phone'
  await call('frappe.client.set_value', {
    doctype,
    name,
    fieldname,
    value,
  })
  await contact.reload()
  createToast({
    title: __('Contact Updated'),
    icon: 'check',
    iconClasses: 'text-ink-green-3',
  })
}

async function deleteOption(type, name) {
  const doctype = type === 'email' ? 'Contact Email' : 'Contact Phone'
  await call('frappe.client.delete', {
    doctype,
    name,
  })
  await contact.reload()
  createToast({
    title: __('Contact Updated'),
    icon: 'check',
    iconClasses: 'text-ink-green-3',
  })
}

async function createNew(type, value) {
  if (!value) return
  let d = await call('crm.api.contact.create_new', {
    contact: contact.data.name,
    field: type,
    value,
  })
  if (d) {
    contact.reload()
    createToast({
      title: __('Contact Updated'),
      icon: 'check',
      iconClasses: 'text-ink-green-3',
    })
  }
}

async function updateField(fieldname, value) {
  await call('frappe.client.set_value', {
    doctype: 'Contact',
    name: props.contactId,
    fieldname,
    value,
  })
  createToast({
    title: __('Contact updated'),
    icon: 'check',
    iconClasses: 'text-ink-green-3',
  })

  contact.reload()
}

const columns = computed(() => dealColumns)

function getDealRowObject(deal) {
  return {
    name: deal.name,
    organization: {
      label: deal.organization,
      logo: getOrganization(deal.organization)?.organization_logo,
    },
    annual_revenue: formatNumberIntoCurrency(
      deal.annual_revenue,
      deal.currency,
    ),
    status: {
      label: translateDealStatus(deal.status),
      color: getDealStatus(deal.status)?.iconColorClass,
    },
    email: deal.email,
    mobile_no: deal.mobile_no,
    deal_owner: {
      label: deal.deal_owner && getUser(deal.deal_owner).full_name,
      ...(deal.deal_owner && getUser(deal.deal_owner)),
    },
    modified: {
      label: formatDate(deal.modified),
      timeAgo: __(timeAgo(deal.modified)),
    },
  }
}

const dealColumns = [
  {
    label: __('Organization'),
    key: 'organization',
    width: '11rem',
  },
  {
    label: __('Amount'),
    key: 'annual_revenue',
    width: '9rem',
  },
  {
    label: __('Status'),
    key: 'status',
    width: '10rem',
  },
  {
    label: __('Email'),
    key: 'email',
    width: '12rem',
  },
  {
    label: __('Mobile no'),
    key: 'mobile_no',
    width: '11rem',
  },
  {
    label: __('Deal owner'),
    key: 'deal_owner',
    width: '10rem',
  },
  {
    label: __('Last modified'),
    key: 'modified',
    width: '8rem',
  },
]

function trackPhoneActivities(type = 'phone') {
  if (!contact.data.actual_mobile_no) {
    errorMessage(__('No phone number set'))
    return
  }
  trackCommunication({
    type,
    doctype: 'Contact',
    docname: contact.data.name,
    phoneNumber: contact.data.actual_mobile_no,
    activities: null,
    contactName: contact.data.full_name
  })
}
</script>
