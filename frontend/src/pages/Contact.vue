<template>
  <LayoutHeader v-if="contact">
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
  </LayoutHeader>
  <div class="flex h-full overflow-hidden">
    <div class="flex w-[352px] shrink-0 flex-col border-r">
      <FileUploader @success="changeContactImage" :validateFile="validateFile">
        <template #default="{ openFileSelector, error }">
          <div class="flex items-center justify-start gap-5 border-b p-5">
            <div class="group relative h-[88px] w-[88px]">
              <Avatar
                size="3xl"
                class="h-[88px] w-[88px]"
                :label="contact.full_name"
                :image="contact.image"
              />
              <component
                :is="contact.image ? Dropdown : 'div'"
                v-bind="
                  contact.image
                    ? {
                        options: [
                          {
                            icon: 'upload',
                            label: contact.image
                              ? 'Change image'
                              : 'Upload image',
                            onClick: openFileSelector,
                          },
                          {
                            icon: 'trash-2',
                            label: 'Remove image',
                            onClick: () => changeContactImage(''),
                          },
                        ],
                      }
                    : { onClick: openFileSelector }
                "
                class="!absolute bottom-0 left-0 right-0"
              >
                <div
                  class="z-1 absolute bottom-0 left-0 right-0 flex h-13 cursor-pointer items-center justify-center rounded-b-full bg-black bg-opacity-40 pt-3 opacity-0 duration-300 ease-in-out group-hover:opacity-100"
                  style="
                    -webkit-clip-path: inset(12px 0 0 0);
                    clip-path: inset(12px 0 0 0);
                  "
                >
                  <CameraIcon class="h-6 w-6 cursor-pointer text-white" />
                </div>
              </component>
            </div>
            <div class="flex flex-col gap-2.5 truncate">
              <Tooltip :text="contact.full_name">
                <div class="truncate text-2xl font-medium">
                  {{ contact.full_name }}
                </div>
              </Tooltip>
              <div class="flex gap-1.5">
                <Button
                  label="Call"
                  size="sm"
                  @click="makeCall(contact.mobile_no)"
                >
                  <template #prefix>
                    <PhoneIcon class="h-4 w-4" />
                  </template>
                </Button>
                <Button
                  label="Delete"
                  theme="red"
                  size="sm"
                  @click="deleteContact"
                >
                  <template #prefix>
                    <FeatherIcon name="trash-2" class="h-4 w-4" />
                  </template>
                </Button>
              </div>
              <ErrorMessage :message="error" />
            </div>
          </div>
        </template>
      </FileUploader>
      <div class="flex flex-col overflow-y-auto">
        <div class="px-5 py-3 text-base font-semibold leading-5">Details</div>
        <div class="flex flex-col gap-1.5 px-2">
          <div
            v-for="field in details"
            :key="field.name"
            class="flex items-center gap-2 px-3 text-base leading-5 last:mb-3"
          >
            <div class="w-[106px] shrink-0 text-gray-600">
              {{ field.label }}
            </div>
            <div class="flex-1 overflow-hidden">
              <Dropdown
                v-if="field.type === 'dropdown'"
                :options="field.options"
                class="form-control show-dropdown-icon w-full flex-1"
              >
                <template #default="{ open }">
                  <div
                    class="dropdown-button flex w-full items-center justify-between gap-2"
                  >
                    <Button
                      :label="contact[field.name]"
                      class="w-full justify-between truncate"
                    >
                      <div class="truncate">{{ contact[field.name] }}</div>
                    </Button>
                    <FeatherIcon
                      :name="open ? 'chevron-up' : 'chevron-down'"
                      class="h-4 text-gray-600"
                    />
                  </div>
                </template>
                <template #footer>
                  <Button
                    variant="ghost"
                    class="w-full !justify-start"
                    label="Create one"
                    @click="field.create()"
                  >
                    <template #prefix>
                      <FeatherIcon name="plus" class="h-4" />
                    </template>
                  </Button>
                </template>
              </Dropdown>
              <FormControl
                v-else-if="field.type === 'link'"
                type="autocomplete"
                :value="contact[field.name]"
                :options="field.options"
                @change="(e) => field.change(e)"
                :placeholder="field.placeholder"
                class="form-control"
              />
              <FormControl
                v-else
                type="text"
                :value="contact[field.name]"
                @change.stop="updateContact(field.name, $event.target.value)"
                class="form-control"
                :debounce="500"
              />
            </div>
            <ExternalLinkIcon
              v-if="field.type === 'link' && field.link && contact[field.name]"
              class="h-4 w-4 shrink-0 cursor-pointer text-gray-600"
              @click="field.link(contact[field.name])"
            />
          </div>
        </div>
      </div>
    </div>
    <Tabs class="overflow-hidden" v-model="tabIndex" :tabs="tabs">
      <template #tab="{ tab, selected }">
        <button
          class="group -mb-px flex items-center gap-2 border-b border-transparent py-2.5 text-base text-gray-600 duration-300 ease-in-out hover:border-gray-400 hover:text-gray-900"
          :class="{ 'text-gray-900': selected }"
        >
          <component v-if="tab.icon" :is="tab.icon" class="h-5" />
          {{ tab.label }}
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
        <LeadsListView
          class="mt-4"
          v-if="tab.label === 'Leads' && rows.length"
          :rows="rows"
          :columns="columns"
        />
        <DealsListView
          class="mt-4"
          v-if="tab.label === 'Deals' && rows.length"
          :rows="rows"
          :columns="columns"
        />
        <div
          v-if="!rows.length"
          class="grid flex-1 place-items-center text-xl font-medium text-gray-500"
        >
          <div class="flex flex-col items-center justify-center space-y-2">
            <component :is="tab.icon" class="!h-10 !w-10" />
            <div>No {{ tab.label.toLowerCase() }} found</div>
          </div>
        </div>
      </template>
    </Tabs>
  </div>
  <Dialog v-model="show" :options="dialogOptions">
    <template #body-content>
      <FormControl
        :type="new_field.type"
        variant="outline"
        v-model="new_field.value"
        :placeholder="new_field.placeholder"
      />
    </template>
  </Dialog>
</template>

<script setup>
import {
  FormControl,
  FeatherIcon,
  Breadcrumbs,
  Dialog,
  Avatar,
  FileUploader,
  ErrorMessage,
  Tooltip,
  Tabs,
  call,
  createResource,
  createListResource,
} from 'frappe-ui'
import Dropdown from '@/components/frappe-ui/Dropdown.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import DropdownItem from '@/components/DropdownItem.vue'
import ExternalLinkIcon from '@/components/Icons/ExternalLinkIcon.vue'
import LeadsListView from '@/components/ListViews/LeadsListView.vue'
import DealsListView from '@/components/ListViews/DealsListView.vue'
import {
  dateFormat,
  dateTooltipFormat,
  timeAgo,
  formatNumberIntoCurrency,
  dealStatuses,
  leadStatuses,
  createToast,
} from '@/utils'
import { usersStore } from '@/stores/users.js'
import { contactsStore } from '@/stores/contacts.js'
import { organizationsStore } from '@/stores/organizations.js'
import { ref, computed, h } from 'vue'
import { useRouter } from 'vue-router'

const { getContactByName, contacts } = contactsStore()
const { getUser } = usersStore()
const { getOrganization, getOrganizationOptions } = organizationsStore()

const props = defineProps({
  contactId: {
    type: String,
    required: true,
  },
})

const router = useRouter()

const contact = computed(() => getContactByName(props.contactId))

const breadcrumbs = computed(() => {
  let items = [{ label: 'Contacts', route: { name: 'Contacts' } }]
  items.push({
    label: contact.value.full_name,
    route: { name: 'Contact', params: { contactId: contact.value.name } },
  })
  return items
})

function validateFile(file) {
  let extn = file.name.split('.').pop().toLowerCase()
  if (!['png', 'jpg', 'jpeg'].includes(extn)) {
    return 'Only PNG and JPG images are allowed'
  }
}

async function changeContactImage(file) {
  await call('frappe.client.set_value', {
    doctype: 'Contact',
    name: props.contactId,
    fieldname: 'image',
    value: file?.file_url || '',
  })
  contacts.reload()
}

async function deleteContact() {
  $dialog({
    title: 'Delete contact',
    message: 'Are you sure you want to delete this contact?',
    actions: [
      {
        label: 'Delete',
        theme: 'red',
        variant: 'solid',
        async onClick({ close }) {
          await call('frappe.client.delete', {
            doctype: 'Contact',
            name: props.contactId,
          })
          contacts.reload()
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
    label: 'Leads',
    icon: h(LeadsIcon, { class: 'h-4 w-4' }),
    count: computed(() => leads.data?.length),
  },
  {
    label: 'Deals',
    icon: h(DealsIcon, { class: 'h-4 w-4' }),
    count: computed(() => deals.data?.length),
  },
]

const leads = createListResource({
  type: 'list',
  doctype: 'CRM Lead',
  cache: ['leads', props.contactId],
  fields: [
    'name',
    'first_name',
    'lead_name',
    'image',
    'organization',
    'status',
    'email',
    'mobile_no',
    'lead_owner',
    'modified',
  ],
  filters: {
    email: contact.value?.email_id,
    converted: 0,
  },
  orderBy: 'modified desc',
  pageLength: 20,
  auto: true,
})

const deals = createListResource({
  type: 'list',
  doctype: 'CRM Lead',
  cache: ['deals', props.contactId],
  fields: [
    'name',
    'organization',
    'annual_revenue',
    'status',
    'email',
    'mobile_no',
    'lead_owner',
    'modified',
  ],
  filters: {
    email: contact.value?.email_id,
    converted: 1,
  },
  orderBy: 'modified desc',
  pageLength: 20,
  auto: true,
})

const rows = computed(() => {
  let list = []
  list = tabIndex.value ? deals : leads

  if (!list.data) return []

  return list.data.map((row) => {
    return tabIndex.value ? getDealRowObject(row) : getLeadRowObject(row)
  })
})

const columns = computed(() => {
  return tabIndex.value ? dealColumns : leadColumns
})

function getLeadRowObject(lead) {
  return {
    name: lead.name,
    lead_name: {
      label: lead.lead_name,
      image: lead.image,
      image_label: lead.first_name,
    },
    organization: {
      label: lead.organization,
      logo: getOrganization(lead.organization)?.organization_logo,
    },
    status: {
      label: lead.status,
      color: leadStatuses[lead.status]?.color,
    },
    email: lead.email,
    mobile_no: lead.mobile_no,
    lead_owner: {
      label: lead.lead_owner && getUser(lead.lead_owner).full_name,
      ...(lead.lead_owner && getUser(lead.lead_owner)),
    },
    modified: {
      label: dateFormat(lead.modified, dateTooltipFormat),
      timeAgo: timeAgo(lead.modified),
    },
  }
}

function getDealRowObject(deal) {
  return {
    name: deal.name,
    organization: {
      label: deal.organization,
      logo: getOrganization(deal.organization)?.organization_logo,
    },
    annual_revenue: formatNumberIntoCurrency(deal.annual_revenue),
    status: {
      label: deal.status,
      color: dealStatuses[deal.status]?.color,
    },
    email: deal.email,
    mobile_no: deal.mobile_no,
    lead_owner: {
      label: deal.lead_owner && getUser(deal.lead_owner).full_name,
      ...(deal.lead_owner && getUser(deal.lead_owner)),
    },
    modified: {
      label: dateFormat(deal.modified, dateTooltipFormat),
      timeAgo: timeAgo(deal.modified),
    },
  }
}

const leadColumns = [
  {
    label: 'Name',
    key: 'lead_name',
    width: '12rem',
  },
  {
    label: 'Organization',
    key: 'organization',
    width: '10rem',
  },
  {
    label: 'Status',
    key: 'status',
    width: '8rem',
  },
  {
    label: 'Email',
    key: 'email',
    width: '12rem',
  },
  {
    label: 'Mobile no',
    key: 'mobile_no',
    width: '11rem',
  },
  {
    label: 'Lead owner',
    key: 'lead_owner',
    width: '10rem',
  },
  {
    label: 'Last modified',
    key: 'modified',
    width: '8rem',
  },
]

const dealColumns = [
  {
    label: 'Organization',
    key: 'organization',
    width: '11rem',
  },
  {
    label: 'Amount',
    key: 'annual_revenue',
    width: '9rem',
  },
  {
    label: 'Status',
    key: 'status',
    width: '10rem',
  },
  {
    label: 'Email',
    key: 'email',
    width: '12rem',
  },
  {
    label: 'Mobile no',
    key: 'mobile_no',
    width: '11rem',
  },
  {
    label: 'Lead owner',
    key: 'lead_owner',
    width: '10rem',
  },
  {
    label: 'Last modified',
    key: 'modified',
    width: '8rem',
  },
]

const details = computed(() => {
  return [
    {
      label: 'Salutation',
      type: 'link',
      name: 'salutation',
      placeholder: 'Mr./Mrs./Ms.',
      options: [
        { label: 'Dr', value: 'Dr' },
        { label: 'Mr', value: 'Mr' },
        { label: 'Mrs', value: 'Mrs' },
        { label: 'Ms', value: 'Ms' },
        { label: 'Mx', value: 'Mx' },
        { label: 'Prof', value: 'Prof' },
        { label: 'Master', value: 'Master' },
        { label: 'Madam', value: 'Madam' },
        { label: 'Miss', value: 'Miss' },
      ],
      change: (data) => {
        contact.value.salutation = data.value
        updateContact('salutation', data.value)
      },
    },
    {
      label: 'First name',
      type: 'data',
      name: 'first_name',
    },
    {
      label: 'Last name',
      type: 'data',
      name: 'last_name',
    },
    {
      label: 'Email',
      type: 'dropdown',
      name: 'email_id',
      options: contact.value?.email_ids?.map((email) => {
        return {
          label: email.email_id,
          value: email.email_id,
          component: h(DropdownItem, {
            value: email.email_id,
            selected: email.email_id === contact.value.email_id,
            onClick: () => setAsPrimary('email', email.email_id),
          }),
        }
      }),
      create: () => {
        new_field.value = { type: 'email', placeholder: 'Add email address' }
        dialogOptions.value = {
          title: 'Add email',
          actions: [
            {
              label: 'Add',
              variant: 'solid',
              onClick: ({ close }) => createNew('email', close),
            },
          ],
        }
        show.value = true
      },
    },
    {
      label: 'Mobile no.',
      type: 'dropdown',
      name: 'mobile_no',
      options: contact.value?.phone_nos?.map((phone) => {
        return {
          label: phone.phone,
          value: phone.phone,
          component: h(DropdownItem, {
            value: phone.phone,
            selected: phone.phone === contact.value.mobile_no,
            onClick: () => setAsPrimary('mobile_no', phone.phone),
          }),
        }
      }),
      create: () => {
        new_field.value = { type: 'phone', placeholder: 'Add mobile no.' }
        dialogOptions.value = {
          title: 'Add mobile no.',
          actions: [
            {
              label: 'Add',
              variant: 'solid',
              onClick: ({ close }) => createNew('phone', close),
            },
          ],
        }
        show.value = true
      },
    },
    {
      label: 'Organization',
      type: 'link',
      name: 'company_name',
      placeholder: 'Select organization',
      options: getOrganizationOptions(),
      change: (data) => {
        contact.value.company_name = data.value
        updateContact('company_name', data.value)
      },
      link: (data) => {
        router.push({
          name: 'Organization',
          params: { organizationId: data.value },
        })
      },
    },
  ]
})

const show = ref(false)
const new_field = ref({})

const dialogOptions = ref({})

function updateContact(fieldname, value) {
  createResource({
    url: 'frappe.client.set_value',
    params: {
      doctype: 'Contact',
      name: props.contactId,
      fieldname,
      value,
    },
    auto: true,
    onSuccess: () => {
      contacts.reload()
      createToast({
        title: 'Contact updated',
        icon: 'check',
        iconClasses: 'text-green-600',
      })
    },
    onError: (err) => {
      createToast({
        title: 'Error updating contact',
        text: err.messages?.[0],
        icon: 'x',
        iconClasses: 'text-red-600',
      })
    },
  })
}

async function setAsPrimary(field, value) {
  let d = await call('crm.api.contact.set_as_primary', {
    contact: props.contactId,
    field,
    value,
  })
  if (d) {
    contacts.reload()
    createToast({
      title: 'Contact updated',
      icon: 'check',
      iconClasses: 'text-green-600',
    })
  }
}

async function createNew(field, close) {
  let d = await call('crm.api.contact.create_new', {
    contact: props.contactId,
    field,
    value: new_field.value.value,
  })
  if (d) {
    contacts.reload()
    createToast({
      title: 'Contact updated',
      icon: 'check',
      iconClasses: 'text-green-600',
    })
  }
  close()
}
</script>

<style scoped>
:deep(.form-control input),
:deep(.form-control select),
:deep(.form-control button) {
  border-color: transparent;
  background: white;
}

:deep(.form-control button) {
  gap: 0;
}

:deep(.form-control button > div) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:deep(.form-control button svg) {
  color: white;
  width: 0;
}

:deep(:has(> .dropdown-button)) {
  width: 100%;
}

:deep(.dropdown-button > button > span) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
