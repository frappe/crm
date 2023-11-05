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
      <div class="overflow-y-auto">
        <!-- details -->
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
  <ContactModal
    v-model="showContactModal"
    v-model:reloadContacts="contacts"
    :contact="contact"
  />
</template>

<script setup>
import {
  FeatherIcon,
  Breadcrumbs,
  Avatar,
  FileUploader,
  ErrorMessage,
  Dropdown,
  Tooltip,
  Tabs,
  call,
  createListResource,
} from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ContactModal from '@/components/ContactModal.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import LeadsListView from '@/components/ListViews/LeadsListView.vue'
import DealsListView from '@/components/ListViews/DealsListView.vue'
import {
  dateFormat,
  dateTooltipFormat,
  timeAgo,
  formatNumberIntoCurrency,
  dealStatuses,
  leadStatuses,
} from '@/utils'
import { usersStore } from '@/stores/users.js'
import { contactsStore } from '@/stores/contacts.js'
import { ref, computed, h } from 'vue'

const { getContactByName, contacts } = contactsStore()
const { getUser } = usersStore()

const showContactModal = ref(false)

const props = defineProps({
  contactId: {
    type: String,
    required: true,
  },
})

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
    'organization_name',
    'organization_logo',
    'status',
    'email',
    'mobile_no',
    'lead_owner',
    'modified',
  ],
  filters: {
    email: contact.value.email_id,
    is_deal: 0,
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
    'organization_name',
    'organization_logo',
    'annual_revenue',
    'deal_status',
    'email',
    'mobile_no',
    'lead_owner',
    'modified',
  ],
  filters: {
    email: contact.value.email_id,
    is_deal: 1,
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
    organization_name: {
      label: lead.organization_name,
      logo: lead.organization_logo,
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
    organization_name: {
      label: deal.organization_name,
      logo: deal.organization_logo,
    },
    annual_revenue: formatNumberIntoCurrency(deal.annual_revenue),
    deal_status: {
      label: deal.deal_status,
      color: dealStatuses[deal.deal_status]?.color,
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
    key: 'organization_name',
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
    key: 'organization_name',
    width: '11rem',
  },
  {
    label: 'Amount',
    key: 'annual_revenue',
    width: '9rem',
  },
  {
    label: 'Status',
    key: 'deal_status',
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
</script>
