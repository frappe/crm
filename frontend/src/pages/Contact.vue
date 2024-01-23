<template>
  <LayoutHeader v-if="contact">
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
  </LayoutHeader>
  <div class="flex h-full flex-col overflow-hidden">
    <FileUploader @success="changeContactImage" :validateFile="validateFile">
      <template #default="{ openFileSelector, error }">
        <div class="flex items-center justify-start gap-6 p-5">
          <div class="group relative h-24 w-24">
            <Avatar
              size="3xl"
              class="h-24 w-24"
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
                class="z-1 absolute bottom-0 left-0 right-0 flex h-14 cursor-pointer items-center justify-center rounded-b-full bg-black bg-opacity-40 pt-3 opacity-0 duration-300 ease-in-out group-hover:opacity-100"
                style="
                  -webkit-clip-path: inset(12px 0 0 0);
                  clip-path: inset(12px 0 0 0);
                "
              >
                <CameraIcon class="h-6 w-6 cursor-pointer text-white" />
              </div>
            </component>
          </div>
          <div class="flex flex-col gap-0.5 truncate">
            <Tooltip :text="contact.full_name">
              <div class="truncate text-3xl font-semibold">
                <span v-if="contact.salutation">
                  {{ contact.salutation + '. ' }}
                </span>
                <span>{{ contact.full_name }}</span>
              </div>
            </Tooltip>
            <div class="flex items-center gap-2 text-base text-gray-700">
              <div v-if="contact.email_id" class="flex items-center gap-1.5">
                <EmailIcon class="h-4 w-4" />
                <span class="">{{ contact.email_id }}</span>
              </div>
              <span
                v-if="contact.email_id"
                class="text-3xl leading-[0] text-gray-600"
              >
                &middot;
              </span>
              <Tooltip text="Make Call" v-if="contact.mobile_no">
                <div
                  class="flex cursor-pointer items-center gap-1.5"
                  @click="makeCall(contact.mobile_no)"
                >
                  <PhoneIcon class="h-4 w-4" />
                  <span class="">{{ contact.mobile_no }}</span>
                </div>
              </Tooltip>
              <span
                v-if="contact.mobile_no"
                class="text-3xl leading-[0] text-gray-600"
              >
                &middot;
              </span>
              <div
                v-if="contact.company_name"
                class="flex items-center gap-1.5"
              >
                <Avatar
                  size="xs"
                  :label="contact.company_name"
                  :image="
                    getOrganization(contact.company_name)?.organization_logo
                  "
                />
                <span class="">{{ contact.company_name }}</span>
              </div>
              <span
                v-if="contact.company_name"
                class="text-3xl leading-[0] text-gray-600"
              >
                &middot;
              </span>
              <Button
                v-if="
                  contact.email_id || contact.mobile_no || contact.company_name
                "
                variant="ghost"
                label="More"
                class="-ml-1 cursor-pointer hover:text-gray-900"
                @click="
                  () => {
                    detailMode = true
                    showContactModal = true
                  }
                "
              />
            </div>
            <div class="mt-2 flex gap-1.5">
              <Button
                label="Edit"
                size="sm"
                @click="
                  () => {
                    detailMode = false
                    showContactModal = true
                  }
                "
              >
                <template #prefix>
                  <EditIcon class="h-4 w-4" />
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
    <Tabs class="overflow-hidden" v-model="tabIndex" :tabs="tabs">
      <template #tab="{ tab, selected }">
        <button
          class="group flex items-center gap-2 border-b border-transparent py-2.5 text-base text-gray-600 duration-300 ease-in-out hover:border-gray-400 hover:text-gray-900"
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
        <DealsListView
          v-if="tab.label === 'Deals' && rows.length"
          class="mt-4"
          :rows="rows"
          :columns="columns"
          :options="{ selectable: false }"
        />
        <div
          v-if="!rows.length"
          class="grid flex-1 place-items-center text-xl font-medium text-gray-500"
        >
          <div class="flex flex-col items-center justify-center space-y-3">
            <component :is="tab.icon" class="!h-10 !w-10" />
            <div>No {{ tab.label }} Found</div>
          </div>
        </div>
      </template>
    </Tabs>
  </div>
  <ContactModal
    v-model="showContactModal"
    :contact="contact"
    :options="{ detailMode }"
  />
</template>

<script setup>
import {
  Breadcrumbs,
  Avatar,
  FileUploader,
  Tooltip,
  Tabs,
  call,
  createResource,
} from 'frappe-ui'
import Dropdown from '@/components/frappe-ui/Dropdown.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import DealsListView from '@/components/ListViews/DealsListView.vue'
import ContactModal from '@/components/Modals/ContactModal.vue'
import {
  dateFormat,
  dateTooltipFormat,
  timeAgo,
  formatNumberIntoCurrency,
} from '@/utils'
import { globalStore } from '@/stores/global.js'
import { usersStore } from '@/stores/users.js'
import { contactsStore } from '@/stores/contacts.js'
import { organizationsStore } from '@/stores/organizations.js'
import { statusesStore } from '@/stores/statuses'
import { viewsStore } from '@/stores/views'
import { ref, computed, h } from 'vue'
import { useRouter } from 'vue-router'

const { $dialog, makeCall } = globalStore()

const { getContactByName, contacts } = contactsStore()
const { getUser } = usersStore()
const { getOrganization } = organizationsStore()
const { getDealStatus } = statusesStore()
const { getDefaultView } = viewsStore()

const props = defineProps({
  contactId: {
    type: String,
    required: true,
  },
})

const router = useRouter()

const contact = computed(() => getContactByName(props.contactId))

const showContactModal = ref(false)
const detailMode = ref(false)

const breadcrumbs = computed(() => {
  let defaultView = getDefaultView()
  let route = { name: 'Contacts' }
  if (defaultView?.route_name == 'Contacts' && defaultView?.is_view) {
    route = { name: 'Contacts', query: { view: defaultView.name } }
  }
  let items = [{ label: 'Contacts', route: route }]
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

const columns = computed(() => dealColumns)

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
      timeAgo: timeAgo(deal.modified),
    },
  }
}

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
    label: 'Deal owner',
    key: 'deal_owner',
    width: '10rem',
  },
  {
    label: 'Last modified',
    key: 'modified',
    width: '8rem',
  },
]
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
