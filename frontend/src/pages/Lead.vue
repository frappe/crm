<template>
  <LayoutHeader v-if="lead.data">
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <Autocomplete
        :options="activeAgents"
        :value="getUser(lead.data.lead_owner).full_name"
        @change="(option) => (lead.data.lead_owner = option.email)"
        placeholder="Lead owner"
      >
        <template #prefix>
          <UserAvatar class="mr-2" :user="lead.data.lead_owner" size="sm" />
        </template>
        <template #item-prefix="{ option }">
          <UserAvatar class="mr-2" :user="option.email" size="sm" />
        </template>
      </Autocomplete>
      <Dropdown :options="statusDropdownOptions">
        <template #default="{ open }">
          <Button :label="lead.data.status">
            <template #prefix>
              <IndicatorIcon :class="indicatorColor[lead.data.status]" />
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
  <TabGroup v-if="lead.data" @change="onTabChange">
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
    <TabPanels class="flex h-full overflow-hidden">
      <TabPanel
        class="flex-1 overflow-y-auto"
        v-for="tab in tabs"
        :key="tab.label"
      >
        <Activities :title="tab.activityTitle" :activities="tab.content" />
      </TabPanel>
      <div
        class="flex flex-col justify-between border-l w-[390px] overflow-hidden"
      >
        <div class="flex flex-col gap-6.5 p-3 overflow-y-auto">
          <div
            v-for="section in detailSections"
            :key="section.label"
            class="flex flex-col"
          >
            <Toggler :is-opened="section.opened" v-slot="{ opened, toggle }">
              <div
                class="flex items-center gap-1 text-base font-semibold leading-5 pr-3 cursor-pointer max-w-fit"
                @click="toggle()"
              >
                <FeatherIcon
                  name="chevron-right"
                  class="h-4 text-gray-600 transition-all duration-300 ease-in-out"
                  :class="{ 'rotate-90': opened }"
                />
                {{ section.label }}
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
                    class="flex items-center px-3 gap-2 text-base leading-5 first:mt-4.5"
                  >
                    <div class="text-gray-600 w-[106px]">{{ field.label }}</div>
                    <div class="flex-1 w-full">
                      <FormControl
                        v-if="field.type === 'select'"
                        type="select"
                        :options="field.options"
                        v-model="lead.data[field.name]"
                      >
                        <template #prefix>
                          <IndicatorIcon
                            :class="indicatorColor[lead.data[field.name]]"
                          />
                        </template>
                      </FormControl>
                      <FormControl
                        v-else-if="field.type === 'email'"
                        type="email"
                        v-model="lead.data[field.name]"
                      />
                      <Autocomplete
                        v-else-if="field.type === 'link'"
                        :options="activeAgents"
                        :value="getUser(lead.data[field.name]).full_name"
                        @change="
                          (option) => (lead.data[field.name] = option.email)
                        "
                        placeholder="Lead owner"
                      >
                        <template #prefix>
                          <UserAvatar
                            class="mr-2"
                            :user="lead.data[field.name]"
                            size="sm"
                          />
                        </template>
                        <template #item-prefix="{ option }">
                          <UserAvatar
                            class="mr-2"
                            :user="option.email"
                            size="sm"
                          />
                        </template>
                      </Autocomplete>
                      <Dropdown
                        v-else-if="field.type === 'dropdown'"
                        :options="statusDropdownOptions"
                        class="w-full flex-1"
                      >
                        <template #default="{ open }">
                          <Button
                            :label="lead.data[field.name]"
                            class="justify-between w-full"
                          >
                            <template #prefix>
                              <IndicatorIcon
                                :class="indicatorColor[lead.data[field.name]]"
                              />
                            </template>
                            <template #default>{{
                              lead.data[field.name]
                            }}</template>
                            <template #suffix>
                              <FeatherIcon
                                :name="open ? 'chevron-up' : 'chevron-down'"
                                class="h-4"
                              />
                            </template>
                          </Button>
                        </template>
                      </Dropdown>
                      <FormControl
                        v-else
                        type="text"
                        v-model="lead.data[field.name]"
                      />
                    </div>
                  </div>
                </div>
              </transition>
            </Toggler>
          </div>
        </div>
        <div
          class="flex items-center gap-1 text-sm px-6 p-3 leading-5 cursor-pointer"
        >
          <span class="text-gray-600">Created </span>
          <Tooltip :text="dateFormat(lead.data.creation, dateTooltipFormat)">
            {{ timeAgo(lead.data.creation) }}
          </Tooltip>
          <span>&nbsp;&middot;&nbsp;</span>
          <span class="text-gray-600">Updated </span>
          <Tooltip :text="dateFormat(lead.data.modified, dateTooltipFormat)">
            {{ timeAgo(lead.data.modified) }}
          </Tooltip>
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
  createResource,
  FeatherIcon,
  Autocomplete,
  FormControl,
  Dropdown,
  Tooltip,
} from 'frappe-ui'
import { TransitionPresets, useTransition } from '@vueuse/core'
import { usersStore } from '@/stores/users'
import { dateFormat, timeAgo, dateTooltipFormat } from '@/utils'
import { ref, computed, h } from 'vue'
import Breadcrumbs from '@/components/Breadcrumbs.vue'
import UserAvatar from '@/components/UserAvatar.vue'

const { getUser, users } = usersStore()

const props = defineProps({
  leadId: {
    type: String,
    required: true,
  },
})

const lead = createResource({
  url: 'crm.crm.doctype.crm_lead.api.get_lead',
  params: { name: props.leadId },
  auto: true,
})

const breadcrumbs = computed(() => {
  let items = [{ label: 'Leads', route: { name: 'Leads' } }]
  items.push({
    label: lead.data.lead_name,
    route: { name: 'Lead', params: { leadId: lead.data.name } },
  })
  return items
})

const tabs = computed(() => {
  return [
    {
      label: 'Activity',
      icon: ActivityIcon,
      content: lead.data.activities,
      activityTitle: 'Activity log',
    },
    {
      label: 'Emails',
      icon: EmailIcon,
      content: lead.data.activities.filter(
        (activity) => activity.activity_type === 'communication'
      ),
      activityTitle: 'Emails',
    },
    {
      label: 'Calls',
      icon: PhoneIcon,
      content: lead.data.activities.filter(
        (activity) => activity.activity_type === 'call'
      ),
      activityTitle: 'Calls',
    },
    {
      label: 'Tasks',
      icon: TaskIcon,
      activityTitle: 'Tasks',
    },
    {
      label: 'Notes',
      icon: NoteIcon,
      activityTitle: 'Notes',
    },
  ]
})

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
      lead.data.status = 'New'
    },
  },
  {
    label: 'Contact made',
    icon: () => h(IndicatorIcon, { class: 'text-orange-600' }),
    onClick: () => {
      lead.data.status = 'Contact made'
    },
  },
  {
    label: 'Proposal made',
    icon: () => h(IndicatorIcon, { class: '!text-blue-600' }),
    onClick: () => {
      lead.data.status = 'Proposal made'
    },
  },
  {
    label: 'Negotiation',
    icon: () => h(IndicatorIcon, { class: 'text-red-600' }),
    onClick: () => {
      lead.data.status = 'Negotiation'
    },
  },
  {
    label: 'Converted',
    icon: () => h(IndicatorIcon, { class: 'text-green-600' }),
    onClick: () => {
      lead.data.status = 'Converted'
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
          type: 'select',
          name: 'status',
          options: statusDropdownOptions,
        },
        {
          label: 'Lead Owner',
          type: 'link',
          name: 'lead_owner',
        },
        {
          label: 'Organization',
          type: 'data',
          name: 'organization_name',
        },
        {
          label: 'Website',
          type: 'data',
          name: 'website',
        },
      ],
    },
    {
      label: 'Person',
      opened: true,
      fields: [
        {
          label: 'Name',
          type: 'data',
          name: 'lead_name',
        },
        {
          label: 'Email',
          type: 'email',
          name: 'email',
        },
        {
          label: 'Mobile No.',
          type: 'phone',
          name: 'mobile_no',
        },
      ],
    },
  ]
})

const activeAgents = computed(() => {
  const nonAgents = ['Administrator', 'Guest']
  return users.data
    .filter((user) => !nonAgents.includes(user.name))
    .sort((a, b) => a.full_name - b.full_name)
    .map((user) => {
      return {
        label: user.full_name,
        value: user.email,
        ...user,
      }
    })
})
</script>
