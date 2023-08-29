<template>
  <LayoutHeader v-if="deal.data">
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <Autocomplete
        :options="activeAgents"
        :value="getUser(deal.data.lead_owner).full_name"
        @change="(option) => (deal.data.lead_owner = option.email)"
        placeholder="Deal owner"
      >
        <template #prefix>
          <UserAvatar class="mr-2" :user="deal.data.lead_owner" size="sm" />
        </template>
        <template #item-prefix="{ option }">
          <UserAvatar class="mr-2" :user="option.email" size="sm" />
        </template>
      </Autocomplete>
      <Dropdown :options="statusDropdownOptions(deal.data, 'deal')">
        <template #default="{ open }">
          <Button
            :label="deal.data.deal_status"
            :class="dealStatuses[deal.data.deal_status].bgColor"
          >
            <template #prefix>
              <IndicatorIcon
                :class="dealStatuses[deal.data.deal_status].color"
              />
            </template>
            <template #suffix
              ><FeatherIcon
                :name="open ? 'chevron-up' : 'chevron-down'"
                class="h-4"
            /></template>
          </Button>
        </template>
      </Dropdown>
      <Button label="Save" variant="solid" @click="() => updateDeal()" />
    </template>
  </LayoutHeader>
  <TabGroup v-slot="{ selectedIndex }" v-if="deal.data" @change="onTabChange">
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
    <div class="flex h-full overflow-hidden">
      <div class="flex-1 flex flex-col">
        <TabPanels class="flex flex-1 overflow-hidden">
          <TabPanel
            class="flex-1 flex flex-col overflow-y-auto"
            v-for="tab in tabs"
            :key="tab.label"
          >
            <Activities
              :title="tab.activityTitle"
              :activities="tab.content"
              @makeCall="makeCall(deal.data.mobile_no)"
              @makeNote="(e) => showNote(e)"
              @deleteNote="(e) => deleteNote(e)"
            />
          </TabPanel>
        </TabPanels>
        <CommunicationArea
          v-if="[0, 1].includes(selectedIndex)"
          v-model="deal"
        />
      </div>
      <div class="flex flex-col justify-between border-l w-[370px]">
        <div
          class="flex flex-col gap-3 pb-4 p-5 items-center justify-center border-b"
        >
          <Avatar
            size="3xl"
            shape="square"
            :label="deal.data.organization_name"
            :image="deal.data.organization_logo"
          />
          <div class="font-medium text-2xl">
            {{ deal.data.organization_name }}
          </div>
          <div class="flex gap-3">
            <Tooltip text="Make a call...">
              <Button
                class="rounded-full h-8 w-8"
                @click="() => makeCall(deal.data.mobile_no)"
              >
                <PhoneIcon class="h-4 w-4" />
              </Button>
            </Tooltip>
            <Button class="rounded-full h-8 w-8">
              <EmailIcon class="h-4 w-4" />
            </Button>
            <Tooltip text="Go to website...">
              <Button
                icon="link"
                @click="openWebsite(deal.data.website)"
                class="rounded-full h-8 w-8"
              />
            </Tooltip>
            <Button icon="more-horizontal" class="rounded-full h-8 w-8" />
          </div>
        </div>
        <div class="flex-1 flex flex-col justify-between overflow-hidden">
          <div class="flex flex-col gap-6 p-3 overflow-y-auto">
            <div
              v-for="section in detailSections"
              :key="section.label"
              class="flex flex-col"
            >
              <Toggler :is-opened="section.opened" v-slot="{ opened, toggle }">
                <div
                  class="flex items-center gap-2 text-base font-semibold leading-5 pl-2 pr-3 cursor-pointer max-w-fit"
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
                  <div v-if="opened" class="flex flex-col gap-1.5">
                    <div
                      v-for="field in section.fields"
                      :key="field.label"
                      class="flex items-center px-3 gap-2 text-base leading-5 first:mt-3"
                    >
                      <div class="text-gray-600 w-[106px]">
                        {{ field.label }}
                      </div>
                      <div class="flex-1">
                        <FormControl
                          v-if="field.type === 'select'"
                          type="select"
                          :options="field.options"
                          v-model="deal.data[field.name]"
                          class="form-control cursor-pointer [&_select]:cursor-pointer"
                        >
                          <template #prefix>
                            <IndicatorIcon
                              :class="dealStatuses[deal.data[field.name]].color"
                            />
                          </template>
                        </FormControl>
                        <FormControl
                          v-else-if="field.type === 'email'"
                          type="email"
                          class="form-control"
                          v-model="deal.data[field.name]"
                        />
                        <Autocomplete
                          v-else-if="field.type === 'link'"
                          :options="activeAgents"
                          :value="getUser(deal.data[field.name]).full_name"
                          @change="
                            (option) => (deal.data[field.name] = option.email)
                          "
                          class="form-control"
                          placeholder="Deal owner"
                        >
                          <template #target="{ togglePopover }">
                            <Button
                              variant="ghost"
                              @click="togglePopover()"
                              :label="getUser(deal.data[field.name]).full_name"
                              class="!justify-start w-full"
                            >
                              <template #prefix>
                                <UserAvatar
                                  :user="deal.data[field.name]"
                                  size="sm"
                                />
                              </template>
                            </Button>
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
                          :options="statusDropdownOptions(deal.data, 'deal')"
                          class="w-full flex-1"
                        >
                          <template #default="{ open }">
                            <Button
                              :label="deal.data[field.name]"
                              class="justify-between w-full"
                            >
                              <template #prefix>
                                <IndicatorIcon
                                  :class="
                                    dealStatuses[deal.data[field.name]].color
                                  "
                                />
                              </template>
                              <template #default>{{
                                deal.data[field.name]
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
                          v-else-if="field.type === 'date'"
                          type="date"
                          v-model="deal.data[field.name]"
                          class="form-control"
                        />
                        <FormControl
                          v-else-if="field.type === 'number'"
                          type="number"
                          v-model="deal.data[field.name]"
                          class="form-control"
                        />
                        <FormControl
                          v-else-if="field.type === 'tel'"
                          type="tel"
                          v-model="deal.data[field.name]"
                          class="form-control"
                        />
                        <FormControl
                          v-else
                          type="text"
                          v-model="deal.data[field.name]"
                          class="form-control"
                        />
                      </div>
                    </div>
                  </div>
                </transition>
              </Toggler>
            </div>
          </div>
        </div>
        <div
          class="flex items-center gap-1 text-sm px-6 p-3 leading-5 cursor-pointer"
        >
          <span class="text-gray-600">Created </span>
          <Tooltip :text="dateFormat(deal.data.creation, dateTooltipFormat)">
            {{ timeAgo(deal.data.creation) }}
          </Tooltip>
          <span>&nbsp;&middot;&nbsp;</span>
          <span class="text-gray-600">Updated </span>
          <Tooltip :text="dateFormat(deal.data.modified, dateTooltipFormat)">
            {{ timeAgo(deal.data.modified) }}
          </Tooltip>
        </div>
      </div>
    </div>
  </TabGroup>
  <NoteModal v-model="showNoteModal" :note="note" @updateNote="updateNote" />
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
import Breadcrumbs from '@/components/Breadcrumbs.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import CommunicationArea from '@/components/CommunicationArea.vue'
import NoteModal from '@/components/NoteModal.vue'
import { TabGroup, TabList, Tab, TabPanels, TabPanel } from '@headlessui/vue'
import { TransitionPresets, useTransition } from '@vueuse/core'
import {
  dateFormat,
  timeAgo,
  dateTooltipFormat,
  dealStatuses,
  statusDropdownOptions,
  openWebsite,
} from '@/utils'
import { usersStore } from '@/stores/users'
import {
  createResource,
  createDocumentResource,
  createListResource,
  FeatherIcon,
  Autocomplete,
  FormControl,
  Dropdown,
  Tooltip,
  Avatar,
  call,
} from 'frappe-ui'
import { ref, computed, inject } from 'vue'

const { getUser, users } = usersStore()

const makeCall = inject('makeOutgoingCall')

const props = defineProps({
  dealId: {
    type: String,
    required: true,
  },
})

const deal = createResource({
  url: 'crm.crm.doctype.crm_lead.api.get_lead',
  params: { name: props.dealId },
  cache: ['deal', props.dealId],
  auto: true,
})

const uDeal = createDocumentResource({
  doctype: 'CRM Lead',
  name: props.dealId,
  setValue: {
    onSuccess: () => {
      deal.reload()
    },
  },
})

function updateDeal() {
  let dealCopy = { ...deal.data }
  delete dealCopy.activities
  uDeal.setValue.submit({ ...dealCopy })
}

const breadcrumbs = computed(() => {
  let items = [{ label: 'Deals', route: { name: 'Deals' } }]
  items.push({
    label: deal.data.organization_name,
    route: { name: 'Deal', params: { dealId: deal.data.name } },
  })
  return items
})

const tabs = computed(() => {
  return [
    {
      label: 'Activity',
      icon: ActivityIcon,
      content: deal.data.activities,
      activityTitle: 'Activity log',
    },
    {
      label: 'Emails',
      icon: EmailIcon,
      content: deal.data.activities.filter(
        (activity) => activity.activity_type === 'communication'
      ),
      activityTitle: 'Emails',
    },
    {
      label: 'Calls',
      icon: PhoneIcon,
      content: calls.data,
      activityTitle: 'Calls',
    },
    // {
    //   label: 'Tasks',
    //   icon: TaskIcon,
    //   activityTitle: 'Tasks',
    // },
    {
      label: 'Notes',
      icon: NoteIcon,
      activityTitle: 'Notes',
      content: notes.data,
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

const detailSections = computed(() => {
  return [
    {
      label: 'Organization',
      opened: true,
      fields: [
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
        {
          label: 'Amount',
          type: 'number',
          name: 'annual_revenue',
        },
        {
          label: 'Close date',
          type: 'date',
          name: 'close_date',
        },
        {
          label: 'Probability',
          type: 'data',
          name: 'probability',
        },
        {
          label: 'Next step',
          type: 'data',
          name: 'next_step',
        },
      ],
    },
    {
      label: 'Contacts',
      opened: true,
      fields: [
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
          type: 'email',
          name: 'email',
        },
        {
          label: 'Mobile no.',
          type: 'tel',
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

const showNoteModal = ref(false)
const note = ref({
  title: '',
  content: '',
})

const notes = createListResource({
  type: 'list',
  doctype: 'CRM Note',
  cache: ['Notes', props.dealId],
  fields: ['name', 'title', 'content', 'owner', 'modified'],
  filters: { lead: props.dealId },
  orderBy: 'modified desc',
  pageLength: 999,
  auto: true,
})

function showNote(n) {
  note.value = n || {
    title: '',
    content: '',
  }
  showNoteModal.value = true
}

async function deleteNote(name) {
  await call('frappe.client.delete', {
    doctype: 'CRM Note',
    name,
  })
  notes.reload()
}

async function updateNote(note) {
  if (note.name) {
    let d = await call('frappe.client.set_value', {
      doctype: 'CRM Note',
      name: note.name,
      fieldname: note,
    })
    if (d.name) {
      notes.reload()
    }
  } else {
    let d = await call('frappe.client.insert', {
      doc: {
        doctype: 'CRM Note',
        title: note.title,
        content: note.content,
        lead: props.dealId,
      },
    })
    if (d.name) {
      notes.reload()
    }
  }
}

const calls = createListResource({
  type: 'list',
  doctype: 'CRM Call Log',
  cache: ['Call Logs', props.dealId],
  fields: [
    'name',
    'from',
    'to',
    'duration',
    'start_time',
    'end_time',
    'status',
    'type',
    'recording_url',
    'modified',
    'note',
  ],
  filters: { lead: props.dealId },
  orderBy: 'modified desc',
  pageLength: 999,
  auto: true,
})
</script>

<style scoped>
:deep(.form-control input),
:deep(.form-control select),
:deep(.form-control button) {
  border-color: transparent;
  background: white;
}
</style>
