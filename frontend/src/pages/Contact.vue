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
            <div class="flex flex-col items-start justify-start gap-4 p-5">
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
                <div class="flex flex-col gap-2 truncate">
                  <div class="truncate text-2xl font-medium">
                    <span v-if="contact.data.salutation">
                      {{ contact.data.salutation + '. ' }}
                    </span>
                    <span>{{ contact.data.full_name }}</span>
                  </div>
                  <div
                    v-if="contact.data.company_name"
                    class="flex items-center gap-1.5 text-base text-gray-800"
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
              <div class="flex gap-1.5">
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
              </div>
            </div>
          </template>
        </FileUploader>
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
                v-model="contact.data"
                @update="updateField"
              />
            </Section>
          </div>
        </div>
      </div>
    </Resizer>
    <Tabs class="overflow-hidden" v-model="tabIndex" :tabs="tabs">
      <template #tab="{ tab, selected }">
        <button
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
        <DealsListView
          v-if="tab.label === 'Deals' && rows.length"
          class="mt-4"
          :rows="rows"
          :columns="columns"
          :options="{ selectable: false, showTooltip: false }"
        />
        <div
          v-if="!rows.length"
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
  <SidePanelModal
    v-if="showSidePanelModal"
    v-model="showSidePanelModal"
    doctype="Contact"
    @reload="() => fieldsLayout.reload()"
  />
  <AddressModal v-model="showAddressModal" v-model:address="_address" />
</template>

<script setup>
import Resizer from '@/components/Resizer.vue'
import Icon from '@/components/Icon.vue'
import Section from '@/components/Section.vue'
import SectionFields from '@/components/SectionFields.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import DealsListView from '@/components/ListViews/DealsListView.vue'
import SidePanelModal from '@/components/Settings/SidePanelModal.vue'
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
import { organizationsStore } from '@/stores/organizations.js'
import { statusesStore } from '@/stores/statuses'
import { callEnabled } from '@/composables/settings'
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
                      !isNew &&
                        (await deleteOption('Contact Email', option.name))
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
              type: 'dropdown',
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
                      !isNew &&
                        (await deleteOption('Contact Phone', option.name))
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
  let d = await call('crm.api.contact.set_as_primary', {
    contact: contact.data.name,
    field,
    value,
  })
  if (d) {
    contact.reload()
    createToast({
      title: 'Contact updated',
      icon: 'check',
      iconClasses: 'text-green-600',
    })
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
    createToast({
      title: 'Contact updated',
      icon: 'check',
      iconClasses: 'text-green-600',
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
    contact.reload()
    createToast({
      title: 'Contact updated',
      icon: 'check',
      iconClasses: 'text-green-600',
    })
  }
}

async function deleteOption(doctype, name) {
  await call('frappe.client.delete', {
    doctype,
    name,
  })
  await contact.reload()
  createToast({
    title: 'Contact updated',
    icon: 'check',
    iconClasses: 'text-green-600',
  })
}

async function updateField(fieldname, value) {
  await call('frappe.client.set_value', {
    doctype: 'Contact',
    name: props.contactId,
    fieldname,
    value,
  })
  createToast({
    title: 'Contact updated',
    icon: 'check',
    iconClasses: 'text-green-600',
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
      label: deal.status,
      color: getDealStatus(deal.status)?.iconColorClass,
    },
    email: deal.email,
    mobile_no: deal.mobile_no,
    deal_owner: {
      label: deal.deal_owner && getUser(deal.deal_owner).full_name,
      ...(deal.deal_owner && getUser(deal.deal_owner)),
    },
    modified: {
      label: dateFormat(deal.modified, dateTooltipFormat),
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
</script>