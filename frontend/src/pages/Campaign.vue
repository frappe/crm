
<template>
  <div v-if="campaignData" class="flex flex-1 flex-col overflow-hidden">

        <div class="flex items-start justify-start gap-6 p-5 sm:items-center">
          <div class="flex flex-col justify-center gap-2 sm:gap-0.5">
            <div class="text-3xl font-semibold text-gray-900">
              {{ campaignData.campaign_name}}
            </div>
            <div
              class="flex flex-col flex-wrap gap-3 text-base text-gray-700 sm:flex-row sm:items-center sm:gap-2"
            >
              
              <Tooltip text="Email Template">
                <div
                  v-if="campaignData.email_template"
                  class="flex items-center gap-1.5"
                >
                <FeatherIcon name="message" class="h-4 w-4" />

                  <span class="">{{ campaignData.email_template }}</span>
                </div>
              </Tooltip>
              <span
                class="hidden text-3xl leading-[0] text-gray-600 sm:flex"
              >
                &middot;
              </span>
              <Tooltip text="Campaign Type">
                <div
                  v-if="campaignData.campaign_type"
                  class="flex items-center gap-1.5"
                >
                  <FeatherIcon name="mail" class="h-4 w-4" />
                  <span class="">{{ campaignData.campaign_type }}</span>
                </div>
              </Tooltip>

              <span
                class="hidden text-3xl leading-[0] text-gray-600 sm:flex"
              >
                &middot;
              </span>
              <Tooltip text="Status">
                <div
                  v-if="campaignData.status"
                  class="flex items-center gap-1.5"
                >
                  <FeatherIcon name="bookmark" class="h-4 w-4" />
                  <span class="">{{ campaignData.status }}</span>
                </div>
              </Tooltip>
            
            </div>
          </div>
        </div>

    <Tabs v-model="tabIndex" :tabs="tabs">
      <template #tab="{ tab, selected }">
        <button
          class="group flex items-center gap-2 border-b border-transparent py-2.5 text-base text-gray-600 duration-300 ease-in-out hover:border-gray-400 hover:text-gray-900"
          :class="{ 'text-gray-900': selected }"
        >
          <component v-if="tab.icon" :is="tab.icon" class="h-5" />
          {{ __(tab.label) }}
        </button>
      </template>
      <template #default="{ tab }">
        <LeadsListView
          class="mt-4"
          v-if="tab.label === 'Leads' && rows.length && campaignData"
          :rows="campaignData.campaign_participants[0]['CRM Lead']"
          :columns="leadColumns"
          :options="{ selectable: false, showTooltip: true }"
        />
        <ContactsListView
          class="mt-4"
          v-if="tab.label === 'Contacts' && rows.length && campaignData"
          :rows="campaignData.campaign_participants[1]['Contact']"
          :columns="contactColumns"
          :options="{ selectable: false, showTooltip: true }"
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
</template>

<script setup>
import LeadsListView from '@/components/ListViews/LeadsListView.vue'
import ContactsListView from '@/components/ListViews/ContactsListView.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import { statusesStore } from '@/stores/statuses'
import {
  dateFormat,
  dateTooltipFormat,
  timeAgo,
  customFormatNumberIntoCurrency,
} from '@/utils'
import {
  Tabs,
  Tooltip,
  createListResource,
  createDocumentResource,
  createResource,
} from 'frappe-ui'
import { h, computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'


const props = defineProps({
  campaignId: {
    type: String,
    required: true,
  },
})

const { $dialog } = globalStore()
const { getLeadStatus } = statusesStore()
const campaignData = ref(null)

const route = useRoute()
const router = useRouter()

const organization = createDocumentResource({
  doctype: 'CRM Organization',
  name: props.organizationId,
  cache: ['organization', props.organizationId],
  fields: ['*'],
  auto: true,
})


onMounted(() => {

const campaign = createResource({
  url: 'crm.fcrm.doctype.crm_campaign.crm_campaign.get_doc_view_campaign_data',
  params: { campaign_name: props.campaignId, },
  onSuccess:  (data) => {
    campaignData.value = data;
  },
})

campaign.fetch();

})


const tabIndex = ref(0)
const tabs = [
  {
    label: 'Leads',
    icon: h(LeadsIcon, { class: 'h-4 w-4' }),
    count: computed(() => leads.data?.length),
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
  cache: ['leads', props.organizationId],
  fields: [
    'name',
    'organization',
    'status',
    'email',
    'lead_owner',
    'modified',
  ],
  filters: {
    organization: props.organizationId,
  },
  orderBy: 'modified desc',
  pageLength: 20,
  auto: true,
})

const contacts = createListResource({
  type: 'list',
  doctype: 'Contact',
  cache: ['contacts', props.organizationId],
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
    company_name: props.organizationId,
  },
  orderBy: 'modified desc',
  pageLength: 20,
  auto: true,
})

const rows = computed(() => {
  let list = []
  list = !tabIndex.value ? leads : contacts

  if (!list.data) return []

  return list.data.map((row) => {
    return !tabIndex.value ? getLeadRowObject(row) : getContactRowObject(row)
  })
})

const columns = computed(() => {
  return tabIndex.value === 0 ? leadColumns : contactColumns
})

function getLeadRowObject(lead) {
  return {
    name: lead.name,
    organization: {
      label: lead.organization,
      logo: props.organization?.organization_logo,
    },
    status: {
      label: lead.status,
      color: getLeadStatus(lead.status)?.iconColorClass,
    },
    email: lead.email,
    lead_owner: {
      label: lead.lead_owner && getUser(lead.lead_owner).full_name,
      ...(lead.lead_owner && getUser(lead.lead_owner)),
    },
    modified: {
      label: dateFormat(lead.modified, dateTooltipFormat),
      timeAgo: __(timeAgo(lead.modified)),
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
      timeAgo: __(timeAgo(contact.modified)),
    },
  }
}

const leadColumns = [
  {
    label: __('Name'),
    key: 'full_name',
    width: '11rem',
  },
  {
    label: __('Organization'),
    key: 'organization',
    width: '9rem',
  },
  {
    label: __('Email'),
    key: 'email',
    width: '10rem',
  },
  {
    label: __('Source'),
    key: 'participant_source',
    width: '12rem',
  },
  {
    label: __('Reference Document'),
    key: 'reference_docname',
    width: '11rem',
  }
]

const contactColumns = [
{
    label: __('Name'),
    key: 'full_name',
    width: '11rem',
  },
  {
    label: __('Organization'),
    key: 'organization',
    width: '9rem',
  },
  {
    label: __('Email'),
    key: 'email',
    width: '10rem',
  },
  {
    label: __('Source'),
    key: 'participant_source',
    width: '12rem',
  },
  {
    label: __('Reference Document'),
    key: 'reference_docname',
    width: '11rem',
  }
]
</script>
