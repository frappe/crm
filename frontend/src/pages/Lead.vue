<template>
  <LayoutHeader v-if="lead.doc">
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
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
  <TabGroup v-if="lead.doc" @change="onTabChange">
    <TabList class="flex items-center gap-6 border-b pl-5 relative">
      <Tab
        ref="tabRef"
        as="template"
        v-for="tab in tabs"
        :key="tab.label"
        v-slot="{ selected }"
      >
        <button
          class="flex items-center gap-2 py-[9px] -mb-[1px] text-base text-gray-600 border-b border-transparent hover:text-gray-900 hover:border-gray-400 transition-all duration-300 ease-in-out"
          :class="{ 'text-gray-900': selected }"
        >
          <component v-if="tab.icon" :is="tab.icon" class="h-5" />
          {{ tab.label }}
        </button>
      </Tab>
      <div
        ref="indicator"
        class="h-[1px] bg-gray-900 w-[82px] absolute -bottom-[1px]"
        :style="{ left: `${indicatorLeftValue}px` }"
      />
    </TabList>
    <TabPanels class="flex h-full">
      <TabPanel class="flex-1" v-for="tab in tabs" :key="tab.label">
        <Activities :activities="tab.content" />
      </TabPanel>
      <div class="flex flex-col gap-6.5 border-l px-6 py-3 w-[390px]">
        <div
          v-for="section in detailSections"
          :key="section.label"
          class="flex flex-col"
        >
          <Toggler :is-opened="section.opened" v-slot="{ opened, toggle }">
            <div
              class="flex items-center gap-1 text-base font-semibold leading-5 cursor-pointer"
              @click="toggle()"
            >
              {{ section.label }}
              <FeatherIcon
                :name="opened ? 'chevron-up' : 'chevron-down'"
                class="h-4 text-gray-600"
              />
            </div>
            <transition
              enter-active-class="duration-300 ease-in"
              leave-active-class="duration-300 ease-[cubic-bezier(0, 1, 0.5, 1)]"
              enter-to-class="max-h-[200px] overflow-hidden"
              leave-from-class="max-h-[200px] overflow-hidden"
              enter-from-class="max-h-0 overflow-hidden"
              leave-to-class="max-h-0 overflow-hidden"
            >
              <div v-if="opened" class="flex flex-col gap-3">
                <div
                  v-for="field in section.fields"
                  :key="field.label"
                  class="flex items-center gap-2 text-base leading-5 first:mt-4.5"
                >
                  <div class="text-gray-600 w-[106px]">{{ field.label }}</div>
                  <div class="text-gray-900">{{ field.value }}</div>
                </div>
              </div>
            </transition>
          </Toggler>
        </div>
      </div>
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
import LayoutHeader from '@/components/LayoutHeader.vue'
import Toggler from '@/components/Toggler.vue'
import Activities from '@/components/Activities.vue'
import { TabGroup, TabList, Tab, TabPanels, TabPanel } from '@headlessui/vue'
import {
  createDocumentResource,
  Avatar,
  FeatherIcon,
  Dropdown,
} from 'frappe-ui'
import { TransitionPresets, useTransition } from '@vueuse/core'
import { usersStore } from '@/stores/users'
import { ref, computed, h } from 'vue'
import Breadcrumbs from '@/components/Breadcrumbs.vue'

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

const breadcrumbs = computed(() => {
  let items = [{ label: 'Leads', route: { name: 'Leads' } }]
  items.push({
    label: lead.doc.lead_name,
    route: { name: 'Lead', params: { leadId: lead.doc.name } },
  })
  return items
})

const activities = [
  {
    type: 'change',
    datetime: '2021-08-20 12:00:00',
    value: 'Status changed from New to Contact made',
  },
  {
    type: 'change',
    datetime: '2021-08-20 12:00:00',
    value: 'Status changed from Proposal made to New',
  },
  {
    type: 'email',
    datetime: '2021-08-20 12:00:00',
    value: 'Email sent to Sharon',
  },
  {
    type: 'change',
    datetime: '2021-08-20 12:00:00',
    value: 'Status changed from Contact made to Proposal made',
  },
  {
    type: 'call',
    datetime: '2021-08-20 12:00:00',
    value: 'Call made to Sharon',
  },
]

const tabs = [
  {
    label: 'Activity',
    icon: ActivityIcon,
    content: activities,
  },
  {
    label: 'Emails',
    icon: EmailIcon,
    content: activities.filter((activity) => activity.type === 'email'),
  },
  {
    label: 'Calls',
    icon: PhoneIcon,
    content: activities.filter((activity) => activity.type === 'call'),
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

const tabRef = ref([])
const indicator = ref(null)

let indicatorLeft = ref(20)
const indicatorLeftValue = useTransition(indicatorLeft, {
  duration: 250,
  ease: TransitionPresets.easeOutCubic,
})

function onTabChange(index) {
  const selectedTab = tabRef.value[index].el
  indicator.value.style.width = `${selectedTab.offsetWidth}px`
  indicatorLeft.value = selectedTab.offsetLeft
}

const statusDropdownOptions = [
  {
    label: 'New',
    icon: () => h(IndicatorIcon, { class: '!text-gray-600' }),
    onClick: () => {
      lead.doc.status = 'New'
    },
  },
  {
    label: 'Contact made',
    icon: () => h(IndicatorIcon, { class: 'text-orange-600' }),
    onClick: () => {
      lead.doc.status = 'Contact made'
    },
  },
  {
    label: 'Proposal made',
    icon: () => h(IndicatorIcon, { class: '!text-blue-600' }),
    onClick: () => {
      lead.doc.status = 'Proposal made'
    },
  },
  {
    label: 'Negotiation',
    icon: () => h(IndicatorIcon, { class: 'text-red-600' }),
    onClick: () => {
      lead.doc.status = 'Negotiation'
    },
  },
  {
    label: 'Converted',
    icon: () => h(IndicatorIcon, { class: 'text-green-600' }),
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

const detailSections = computed(() => {
  return [
    {
      label: 'About this lead',
      opened: true,
      fields: [
        {
          label: 'Status',
          value: lead.doc.status,
        },
        {
          label: 'Lead Owner',
          value: getUser(lead.doc.lead_owner).full_name,
        },
        {
          label: 'Organization',
          value: lead.doc.organization_name,
        },
        {
          label: 'Website',
          value: lead.doc.organization_website,
        },
      ],
    },
    {
      label: 'Person',
      opened: true,
      fields: [
        {
          label: 'Name',
          value: lead.doc.lead_name,
        },
        {
          label: 'Email',
          value: lead.doc.email,
        },
        {
          label: 'Mobile No.',
          value: lead.doc.mobile_no,
        },
      ],
    },
  ]
})
</script>
