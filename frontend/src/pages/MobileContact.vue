<template>
  <LayoutHeader v-if="contact.data">
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
  <div v-if="contact.data" class="flex flex-col h-full overflow-hidden">
    <FileUploader @success="changeContactImage" :validateFile="validateIsImageFile">
      <template #default="{ openFileSelector, error }">
        <div class="flex flex-col items-start justify-start gap-4 p-4">
          <div class="flex gap-4 items-center">
            <div class="group relative h-14.5 w-14.5">
              <Avatar
                size="3xl"
                class="h-14.5 w-14.5"
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
            <div class="flex flex-col gap-2 truncate">
              <div class="truncate text-lg font-medium text-ink-gray-9">
                <span v-if="contact.data.salutation">
                  {{ contact.data.salutation + '. ' }}
                </span>
                <span>{{ contact.data.full_name }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <Button
                  v-if="contact.data.actual_mobile_no"
                  :label="__('Make Call')"
                  size="sm"
                  @click="
                    callEnabled && makeCall(contact.data.actual_mobile_no)
                  "
                >
                  <template #prefix>
                    <PhoneIcon class="h-4 w-4" />
                  </template>
                </Button>
                <Button
                  :label="__('Delete')"
                  theme="red"
                  size="sm"
                  @click="deleteContact"
                >
                  <template #prefix>
                    <FeatherIcon name="trash-2" class="h-4 w-4" />
                  </template>
                </Button>
                <Avatar
                  v-if="contact.data.company_name"
                  size="md"
                  :label="contact.data.company_name"
                  :image="
                    getOrganization(contact.data.company_name)
                      ?.organization_logo
                  "
                />
              </div>
              <ErrorMessage :message="__(error)" />
            </div>
          </div>
        </div>
      </template>
    </FileUploader>
    <Tabs as="div" v-model="tabIndex" :tabs="tabs" class="overflow-auto">
      <TabList class="!px-4" v-slot="{ tab, selected }">
        <button
          v-if="tab.name == 'Deals'"
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
            v-if="sections.data"
            class="flex flex-1 flex-col justify-between overflow-hidden"
          >
            <SidePanelLayout
              :sections="sections.data"
              doctype="Contact"
              :docname="contact.data.name"
              @reload="sections.reload"
            />
          </div>
        </div>
        <DealsListView
          v-else-if="tab.label === 'Deals' && rows.length"
          class="mt-4"
          :rows="rows"
          :columns="columns"
          :options="{ selectable: false, showTooltip: false }"
        />
        <div
          v-if="tab.label === 'Deals' && !rows.length"
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
</template>

<script setup>
import Icon from '@/components/Icon.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import DealsListView from '@/components/ListViews/DealsListView.vue'
import { formatDate, timeAgo, validateIsImageFile } from '@/utils'
import { getView } from '@/utils/view'
import { showAddressModal, addressProps } from '@/composables/modals'
import { getSettings } from '@/stores/settings'
import { getMeta } from '@/stores/meta'
import { globalStore } from '@/stores/global.js'
import { usersStore } from '@/stores/users.js'
import { organizationsStore } from '@/stores/organizations.js'
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
  createResource,
  usePageMeta,
  Dropdown,
  toast,
} from 'frappe-ui'
import { ref, computed, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const { brand } = getSettings()
const { $dialog, makeCall } = globalStore()

const { getUser } = usersStore()
const { getOrganization } = organizationsStore()
const { getDealStatus } = statusesStore()
const { doctypeMeta } = getMeta('Contact')

const props = defineProps({
  contactId: {
    type: String,
    required: true,
  },
})

const route = useRoute()
const router = useRouter()

const _contact = ref({})

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
    label: title.value,
    route: { name: 'Contact', params: { contactId: props.contactId } },
  })
  return items
})

const title = computed(() => {
  let t = doctypeMeta['Contact']?.title_field || 'name'
  return contact.data?.[t] || props.contactId
})

usePageMeta(() => {
  return {
    title: title.value,
    icon: brand.favicon,
  }
})

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
    name: 'Details',
    label: __('Details'),
    icon: DetailsIcon,
  },
  {
    name: 'Deals',
    label: __('Deals'),
    icon: h(DealsIcon, { class: 'h-4 w-4' }),
    count: computed(() => deals.data?.length),
  },
]

const deals = createResource({
  url: 'crm.api.contact.get_linked_deals',
  cache: ['deals', props.contactId],
  params: { contact: props.contactId },
  auto: true,
})

const rows = computed(() => {
  if (!deals.data || deals.data == []) return []

  return deals.data.map((row) => getDealRowObject(row))
})

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
  cache: ['sidePanelSections', 'Contact'],
  params: { doctype: 'Contact' },
  auto: true,
  transform: (data) => computed(() => getParsedSections(data)),
})

function getParsedSections(_sections) {
  return _sections.map((section) => {
    section.columns = section.columns.map((column) => {
      column.fields = column.fields.map((field) => {
        if (field.fieldname === 'email_id') {
          return {
            ...field,
            type: 'dropdown',
            options:
              contact.data?.email_ids?.map((email) => {
                return {
                  name: email.name,
                  value: email.email_id,
                  selected: email.email_id === contact.data.email_id,
                  placeholder: 'john@doe.com',
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
                      editOption(
                        'Contact Email',
                        option.name,
                        'email_id',
                        option.value,
                      )
                    }
                  },
                  onDelete: async (option, isNew) => {
                    contact.data.email_ids = contact.data.email_ids.filter(
                      (email) => email.name !== option.name,
                    )
                    !isNew && (await deleteOption('Contact Email', option.name))
                    if (_contact.value.email_id === option.value) {
                      if (contact.data.email_ids.length === 0) {
                        _contact.value.email_id = ''
                      } else {
                        _contact.value.email_id = contact.data.email_ids.find(
                          (email) => email.is_primary,
                        )?.email_id
                      }
                    }
                  },
                }
              }) || [],
            create: () => {
              contact.data?.email_ids?.push({
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
            read_only: false,
            fieldtype: 'dropdown',
            options:
              contact.data?.phone_nos?.map((phone) => {
                return {
                  name: phone.name,
                  value: phone.phone,
                  selected: phone.phone === contact.data.actual_mobile_no,
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
                      editOption(
                        'Contact Phone',
                        option.name,
                        'phone',
                        option.value,
                      )
                    }
                  },
                  onDelete: async (option, isNew) => {
                    contact.data.phone_nos = contact.data.phone_nos.filter(
                      (phone) => phone.name !== option.name,
                    )
                    !isNew && (await deleteOption('Contact Phone', option.name))
                    if (_contact.value.actual_mobile_no === option.value) {
                      if (contact.data.phone_nos.length === 0) {
                        _contact.value.actual_mobile_no = ''
                      } else {
                        _contact.value.actual_mobile_no =
                          contact.data.phone_nos.find(
                            (phone) => phone.is_primary_mobile_no,
                          )?.phone
                      }
                    }
                  },
                }
              }) || [],
            create: () => {
              contact.data?.phone_nos?.push({
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
              _contact.value.address = value
              openAddressModal()
              close()
            },
            edit: (address) => openAddressModal(address),
          }
        } else {
          return field
        }
      })
      return column
    })
    return section
  })
}

async function setAsPrimary(field, value) {
  let d = await call('crm.api.contact.set_as_primary', {
    contact: contact.data.name,
    field,
    value,
  })
  if (d) {
    contact.reload()
    toast.success(___('Contact updated'))
  }
}

async function createNew(field, value) {
  if (!value) return
  let d = await call('crm.api.contact.create_new', {
    contact: contact.data.name,
    field,
    value,
  })
  if (d) {
    contact.reload()
    toast.success(__('Contact updated'))
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
    contact.reload()
    toast.success(__('Contact updated'))
  }
}

async function deleteOption(doctype, name) {
  await call('frappe.client.delete', {
    doctype,
    name,
  })
  await contact.reload()
  toast.success(__('Contact updated'))
}

const { getFormattedCurrency } = getMeta('CRM Deal')

const columns = computed(() => dealColumns)

function getDealRowObject(deal) {
  return {
    name: deal.name,
    organization: {
      label: deal.organization,
      logo: getOrganization(deal.organization)?.organization_logo,
    },
    annual_revenue: getFormattedCurrency('annual_revenue', deal),
    status: {
      label: deal.status,
      color: getDealStatus(deal.status)?.color,
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
    align: 'right',
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

function openAddressModal(_address) {
  showAddressModal.value = true
  addressProps.value = {
    doctype: 'Address',
    address: _address,
  }
}
</script>
