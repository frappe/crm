<template>
  <LayoutHeader v-if="lead.doc">
    <template #left-header>
      <FeatherIcon
        name="chevron-left"
        class="h-5 cursor-pointer"
        @click="$router.back()"
      />
      <h1 class="font-semibold text-xl">{{ lead.doc.lead_name }}</h1>
      <div
        v-if="lead.doc.organization_name"
        class="flex items-center space-x-2 bg-gray-100 hover:bg-gray-200 p-1 pr-2 rounded ml-2 cursor-pointer"
      >
        <Avatar
          class="flex items-center"
          :image="lead.doc.organization_logo"
          :label="lead.doc.organization_name"
          size="sm"
          shape="square"
        />
        <div class="text-base text-gray-700 truncate">
          {{ lead.doc.organization_name }}
        </div>
      </div>
    </template>
    <template #right-header>
      <div
        v-if="lead.doc.lead_owner"
        class="flex items-center space-x-2 bg-gray-100 hover:bg-gray-200 pl-1.5 py-1 pr-2 rounded ml-2 cursor-pointer"
      >
        <Avatar
          :image="getUser(lead.doc.lead_owner).user_image"
          :label="getUser(lead.doc.lead_owner).full_name"
          size="sm"
        />
        <div class="text-base text-gray-700">
          {{ getUser(lead.doc.lead_owner).full_name }}
        </div>
      </div>
      <Dropdown :options="statusDropdownOptions">
        <template #default="{ open }">
          <Button :label="lead.doc.status">
            <template #prefix>
              <IndicatorIcon :class="indicatorColor[lead.doc.status]" />
            </template>
            <template #suffix
              ><FeatherIcon
                :name="open ? 'chevron-up' : 'chevron-down'"
                class="h-4"
            /></template>
          </Button>
        </template>
      </Dropdown>
      <Button icon="more-horizontal" />
    </template>
  </LayoutHeader>
  <TabGroup v-if="lead.doc">
    <TabList class="flex items-center gap-6 border-b pl-5">
      <Tab
        as="template"
        v-for="tab in tabs"
        :key="tab.label"
        v-slot="{ selected }"
      >
        <button
          class="flex items-center gap-2 py-2 border-b hover:text-gray-900 -mb-[1px]"
          :class="
            selected
              ? 'border-blue-500 text-gray-900 hover:border-blue-500'
              : 'border-transparent text-gray-700 hover:border-gray-400'
          "
        >
          <component v-if="tab.icon" :is="tab.icon" class="h-5" />
          {{ tab.label }}
        </button>
      </Tab>
    </TabList>
    <TabPanels class="flex h-full">
      <TabPanel class="flex-1 bg-gray-50" v-for="tab in tabs">
        <div class="p-6">{{ tab.label }}</div>
      </TabPanel>
      <div class="w-[390px] border-l px-6 py-3">{{ lead.doc.lead_name }}</div>
    </TabPanels>
  </TabGroup>
</template>
<script setup>
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import LayoutHeader from '../components/LayoutHeader.vue'
import { TabGroup, TabList, Tab, TabPanels, TabPanel } from '@headlessui/vue'
import {
  createDocumentResource,
  Avatar,
  FeatherIcon,
  Dropdown,
} from 'frappe-ui'
import { usersStore } from '../stores/users'

const { getUser } = usersStore()

const props = defineProps({
  leadId: {
    type: String,
    required: true,
  },
})
const lead = createDocumentResource({
  doctype: 'CRM Lead',
  name: props.leadId,
  auto: true,
})

const tabs = [
  {
    label: 'Activity',
    icon: ActivityIcon,
  },
  {
    label: 'Emails',
    icon: EmailIcon,
  },
  {
    label: 'Calls',
    icon: PhoneIcon,
  },
  {
    label: 'Tasks',
    icon: TaskIcon,
  },
  {
    label: 'Notes',
    icon: NoteIcon,
  },
]

const statusDropdownOptions = [
  {
    label: 'New',
    icon: IndicatorIcon,
    onClick: () => {
      lead.doc.status = 'New'
    },
  },
  {
    label: 'Contact made',
    icon: IndicatorIcon,
    onClick: () => {
      lead.doc.status = 'Contact made'
    },
  },
  {
    label: 'Proposal made',
    icon: IndicatorIcon,
    onClick: () => {
      lead.doc.status = 'Proposal made'
    },
  },
  {
    label: 'Negotiation',
    icon: IndicatorIcon,
    onClick: () => {
      lead.doc.status = 'Negotiation'
    },
  },
  {
    label: 'Converted',
    icon: IndicatorIcon,
    onClick: () => {
      lead.doc.status = 'Converted'
    },
  },
]

const indicatorColor = {
  New: 'text-gray-600',
  'Contact made': 'text-orange-500',
  'Proposal made': 'text-blue-600',
  Negotiation: 'text-red-600',
  Converted: 'text-green-600',
}
</script>
