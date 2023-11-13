<template>
  <div class="flex flex-1 flex-col overflow-hidden">
    <div class="flex gap-6 p-5">
      <FileUploader
        @success="changeOrganizationImage"
        :validateFile="validateFile"
      >
        <template #default="{ openFileSelector, error }">
          <div class="group relative h-24 w-24">
            <Avatar
              size="3xl"
              :image="organization.organization_logo"
              :label="organization.name"
              class="!h-24 !w-24"
            />
            <component
              :is="organization.organization_logo ? Dropdown : 'div'"
              v-bind="
                organization.organization_logo
                  ? {
                      options: [
                        {
                          icon: 'upload',
                          label: organization.organization_logo
                            ? 'Change image'
                            : 'Upload image',
                          onClick: openFileSelector,
                        },
                        {
                          icon: 'trash-2',
                          label: 'Remove image',
                          onClick: () => changeOrganizationImage(''),
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
            <ErrorMessage class="mt-2" :message="error" />
          </div>
        </template>
      </FileUploader>
      <div class="flex flex-col justify-center gap-2">
        <div class="text-3xl font-semibold text-gray-900">
          {{ organization.name }}
        </div>
        <div class="flex items-center gap-2 text-base text-gray-700">
          <div v-if="organization.website" class="flex items-center gap-1.5">
            <WebsiteIcon class="h-4 w-4" />
            <span class="">{{ website(organization.website) }}</span>
          </div>
          <span
            v-if="organization.industry && organization.website"
            class="text-3xl leading-[0] text-gray-600"
          >
            &middot;
          </span>
          <div v-if="organization.industry" class="flex items-center gap-1.5">
            <FeatherIcon name="briefcase" class="h-4 w-4" />
            <span class="">{{ organization.industry }}</span>
          </div>
          <span
            v-if="
              (organization.website || organization.industry) &&
              organization.annual_revenue
            "
            class="text-3xl leading-[0] text-gray-600"
          >
            &middot;
          </span>
          <div
            v-if="organization.annual_revenue"
            class="flex items-center gap-1.5"
          >
            <FeatherIcon name="dollar-sign" class="h-4 w-4" />
            <span class="">{{ organization.annual_revenue }}</span>
          </div>
        </div>
        <div class="mt-1 flex gap-2">
          <Button label="Edit" size="sm" @click="showOrganizationModal = true">
            <template #prefix>
              <EditIcon class="h-4 w-4" />
            </template>
          </Button>
          <Button
            label="Delete"
            theme="red"
            size="sm"
            @click="deleteOrganization"
          >
            <template #prefix>
              <FeatherIcon name="trash-2" class="h-4 w-4" />
            </template>
          </Button>
          <!-- <Button label="Add lead" size="sm">
              <template #prefix>
                <FeatherIcon name="plus" class="h-4 w-4" />
              </template>
            </Button>
            <Button label="Add deal" size="sm">
              <template #prefix>
                <FeatherIcon name="plus" class="h-4 w-4" />
              </template>
            </Button> -->
        </div>
      </div>
    </div>
    <Tabs v-model="tabIndex" :tabs="tabs">
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
        <div class="flex h-full">
          <LeadsListView
            class="mt-4"
            v-if="tab.label === 'Leads' && rows.length"
            :rows="rows"
            :columns="columns"
            :options="{ selectable: false }"
          />
          <DealsListView
            class="mt-4"
            v-if="tab.label === 'Deals' && rows.length"
            :rows="rows"
            :columns="columns"
            :options="{ selectable: false }"
          />
          <ContactsListView
            class="mt-4"
            v-if="tab.label === 'Contacts' && rows.length"
            :rows="rows"
            :columns="columns"
            :options="{ selectable: false }"
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
        </div>
      </template>
    </Tabs>
    <OrganizationModal
      v-model="showOrganizationModal"
      v-model:reloadOrganizations="organizations"
      :organization="organization"
    />
  </div>
</template>

<script setup>
import {
  FeatherIcon,
  Avatar,
  FileUploader,
  ErrorMessage,
  Dropdown,
  Tabs,
  Badge,
  call,
  createListResource,
} from 'frappe-ui'
import OrganizationModal from '@/components/Modals/OrganizationModal.vue'
import LeadsListView from '@/components/ListViews/LeadsListView.vue'
import DealsListView from '@/components/ListViews/DealsListView.vue'
import ContactsListView from '@/components/ListViews/ContactsListView.vue'
import WebsiteIcon from '@/components/Icons/WebsiteIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import { organizationsStore } from '@/stores/organizations.js'
import {
  dateFormat,
  dateTooltipFormat,
  timeAgo,
  leadStatuses,
  dealStatuses,
  formatNumberIntoCurrency,
} from '@/utils'
import { usersStore } from '@/stores/users'
import { h, computed, ref, watch, onMounted } from 'vue'

const props = defineProps({
  organization: {
    type: Object,
    required: true,
  },
})

const { organizations } = organizationsStore()
const showOrganizationModal = ref(false)

function validateFile(file) {
  let extn = file.name.split('.').pop().toLowerCase()
  if (!['png', 'jpg', 'jpeg'].includes(extn)) {
    return 'Only PNG and JPG images are allowed'
  }
}

async function changeOrganizationImage(file) {
  await call('frappe.client.set_value', {
    doctype: 'CRM Organization',
    name: props.organization.name,
    fieldname: 'organization_logo',
    value: file?.file_url || '',
  })
  organizations.reload()
}

async function deleteOrganization() {
  $dialog({
    title: 'Delete organization',
    message: 'Are you sure you want to delete this organization?',
    actions: [
      {
        label: 'Delete',
        theme: 'red',
        variant: 'solid',
        async onClick({ close }) {
          await call('frappe.client.delete', {
            doctype: 'CRM Organization',
            name: props.organization.name,
          })
          organizations.reload()
          close()
        },
      },
    ],
  })
}

function website(url) {
  return url && url.replace(/^(?:https?:\/\/)?(?:www\.)?/i, '')
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
  {
    label: 'Contacts',
    icon: h(ContactsIcon, { class: 'h-4 w-4' }),
    count: computed(() => contacts.data?.length),
  },
]

const { getUser } = usersStore()

const leads = createListResource({
  type: 'list',
  doctype: 'CRM Lead',
  cache: ['leads', props.organization.name],
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
    organization: props.organization.name,
    converted: 0,
  },
  orderBy: 'modified desc',
  pageLength: 20,
  auto: true,
})

const deals = createListResource({
  type: 'list',
  doctype: 'CRM Deal',
  cache: ['deals', props.organization.name],
  fields: [
    'name',
    'organization',
    'annual_revenue',
    'status',
    'email',
    'mobile_no',
    'deal_owner',
    'modified',
  ],
  filters: {
    organization: props.organization.name,
  },
  orderBy: 'modified desc',
  pageLength: 20,
  auto: true,
})

const contacts = createListResource({
  type: 'list',
  doctype: 'Contact',
  cache: ['contacts', props.organization.name],
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
    company_name: props.organization.name,
  },
  orderBy: 'modified desc',
  pageLength: 20,
  auto: true,
})

const rows = computed(() => {
  let list = []
  list = !tabIndex.value ? leads : tabIndex.value == 1 ? deals : contacts

  if (!list.data) return []

  return list.data.map((row) => {
    return !tabIndex.value
      ? getLeadRowObject(row)
      : tabIndex.value == 1
      ? getDealRowObject(row)
      : getContactRowObject(row)
  })
})

const columns = computed(() => {
  return tabIndex.value === 0
    ? leadColumns
    : tabIndex.value === 1
    ? dealColumns
    : contactColumns
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
      logo: props.organization?.organization_logo,
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
      logo: props.organization?.organization_logo,
    },
    annual_revenue: formatNumberIntoCurrency(deal.annual_revenue),
    status: {
      label: deal.status,
      color: dealStatuses[deal.status]?.color,
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
      logo: props.organization?.organization_logo,
    },
    modified: {
      label: dateFormat(contact.modified, dateTooltipFormat),
      timeAgo: timeAgo(contact.modified),
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

const contactColumns = [
  {
    label: 'Name',
    key: 'full_name',
    width: '17rem',
  },
  {
    label: 'Email',
    key: 'email',
    width: '12rem',
  },
  {
    label: 'Phone',
    key: 'mobile_no',
    width: '12rem',
  },
  {
    label: 'Organization',
    key: 'company_name',
    width: '12rem',
  },
  {
    label: 'Last modified',
    key: 'modified',
    width: '8rem',
  },
]

function reload(val) {
  leads.filters.organization = val
  deals.filters.organization = val
  contacts.filters.company_name = val
  leads.reload()
  deals.reload()
  contacts.reload()
}

watch(
  () => props.organization.name,
  (val) => val && reload(val)
)

onMounted(() => reload(props.organization.name))
</script>
