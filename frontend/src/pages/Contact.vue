<template>
  <LayoutHeader v-if="contact.data">
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
  </LayoutHeader>
  <div v-if="contact.data" class="flex h-full flex-col overflow-hidden">
    <FileUploader @success="changeContactImage" :validateFile="validateFile">
      <template #default="{ openFileSelector, error }">
        <div class="flex items-start justify-start gap-6 p-5 sm:items-center">
          <div class="group relative h-24 w-24">
            <Avatar
              size="3xl"
              class="h-24 w-24"
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
          <div class="flex flex-col gap-2 truncate sm:gap-0.5">
            <div class="truncate text-3xl font-semibold">
              <span v-if="contact.data.salutation">
                {{ contact.data.salutation + '. ' }}
              </span>
              <span>{{ contact.data.full_name }}</span>
            </div>
            <div
              class="flex flex-col flex-wrap gap-3 text-base text-gray-700 sm:flex-row sm:items-center sm:gap-2"
            >
              <div
                v-if="contact.data.email_id"
                class="flex items-center gap-1.5"
              >
                <Email2Icon class="h-4 w-4" />
                <span class="">{{ contact.data.email_id }}</span>
              </div>
              <span
                v-if="contact.data.email_id"
                class="hidden text-3xl leading-[0] text-gray-600 sm:flex"
              >
                &middot;
              </span>
              <component
                :is="callEnabled ? Tooltip : 'div'"
                :text="__('Make Call')"
                v-if="contact.data.actual_mobile_no"
              >
                <div
                  class="flex items-center gap-1.5"
                  :class="callEnabled ? 'cursor-pointer' : ''"
                  @click="
                    callEnabled && makeCall(contact.data.actual_mobile_no)
                  "
                >
                  <PhoneIcon class="h-4 w-4" />
                  <span class="">{{ contact.data.actual_mobile_no }}</span>
                </div>
              </component>
              <span
                v-if="contact.data.actual_mobile_no"
                class="hidden text-3xl leading-[0] text-gray-600 sm:flex"
              >
                &middot;
              </span>
              <div
                v-if="contact.data.company_name"
                class="flex items-center gap-1.5"
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
              <span
                v-if="contact.data.company_name"
                class="hidden text-3xl leading-[0] text-gray-600 sm:flex"
              >
                &middot;
              </span>
              <Button
                v-if="
                  contact.data.email_id ||
                  contact.data.mobile_no ||
                  contact.data.company_name
                "
                variant="ghost"
                :label="__('More')"
                class="w-fit cursor-pointer hover:text-gray-900 sm:-ml-1"
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
                :label="__('Edit')"
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
            <ErrorMessage :message="__(error)" />
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
  <ContactModal
    v-model="showContactModal"
    v-model:quickEntry="showQuickEntryModal"
    :contact="contact"
    :options="{ detailMode }"
  />
  <QuickEntryModal
    v-if="showQuickEntryModal"
    v-model="showQuickEntryModal"
    doctype="Contact"
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
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import DealsListView from '@/components/ListViews/DealsListView.vue'
import ContactModal from '@/components/Modals/ContactModal.vue'
import QuickEntryModal from '@/components/Settings/QuickEntryModal.vue'
import {
  dateFormat,
  dateTooltipFormat,
  timeAgo,
  formatNumberIntoCurrency,
} from '@/utils'
import { globalStore } from '@/stores/global.js'
import { usersStore } from '@/stores/users.js'
import { organizationsStore } from '@/stores/organizations.js'
import { statusesStore } from '@/stores/statuses'
import { callEnabled } from '@/composables/settings'
import { ref, computed, h } from 'vue'
import { useRouter } from 'vue-router'

const { $dialog, makeCall } = globalStore()

const { getUser } = usersStore()
const { getOrganization } = organizationsStore()
const { getDealStatus } = statusesStore()

const props = defineProps({
  contactId: {
    type: String,
    required: true,
  },
})

const router = useRouter()

const showContactModal = ref(false)
const showQuickEntryModal = ref(false)
const detailMode = ref(false)

const breadcrumbs = computed(() => {
  let items = [{ label: __('Contacts'), route: { name: 'Contacts' } }]
  items.push({
    label: contact.data?.full_name,
    route: { name: 'Contact', params: { contactId: props.contactId } },
  })
  return items
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
