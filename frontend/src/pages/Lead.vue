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
      <Dropdown :options="statusDropdownOptions(lead.data)">
        <template #default="{ open }">
          <Button
            :label="lead.data.status"
            :class="leadStatuses[lead.data.status].bgColor"
          >
            <template #prefix>
              <IndicatorIcon :class="leadStatuses[lead.data.status].color" />
            </template>
            <template #suffix
              ><FeatherIcon
                :name="open ? 'chevron-up' : 'chevron-down'"
                class="h-4"
            /></template>
          </Button>
        </template>
      </Dropdown>
      <Button label="Save" variant="solid" @click="updateLead()" />
      <Button
        label="Convert to deal"
        variant="solid"
        @click="convertToDeal()"
      />
    </template>
  </LayoutHeader>
  <TabGroup v-slot="{ selectedIndex }" v-if="lead.data" @change="onTabChange">
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
              @makeCall="makeCall(lead.data.mobile_no)"
              @makeNote="(e) => showNote(e)"
              @deleteNote="(e) => deleteNote(e)"
              @setFocusOnEmail="() => $refs.sendEmailRef.el.click()"
            />
          </TabPanel>
        </TabPanels>
        <CommunicationArea
          ref="sendEmailRef"
          v-if="[0, 1].includes(selectedIndex)"
          v-model="lead"
        />
      </div>
      <div class="flex flex-col justify-between border-l w-[370px]">
        <FileUploader @success="changeLeadImage" :validateFile="validateFile">
          <template #default="{ openFileSelector, error }">
            <div
              class="flex flex-col gap-3 pb-4 p-5 items-center justify-center border-b"
            >
              <Avatar
                size="3xl"
                :label="lead.data.first_name"
                :image="lead.data.image"
              />
              <ErrorMessage :message="error" />
              <div class="font-medium text-2xl">{{ lead.data.lead_name }}</div>
              <div class="flex gap-3">
                <Tooltip text="Make a call...">
                  <Button
                    class="rounded-full h-8 w-8"
                    @click="() => makeCall(lead.data.mobile_no)"
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
                    @click="openWebsite(lead.data.website)"
                    class="rounded-full h-8 w-8"
                  />
                </Tooltip>
                <Dropdown
                  :options="[
                    {
                      icon: 'upload',
                      label: lead.data.image ? 'Change photo' : 'Upload photo',
                      onClick: openFileSelector,
                    },
                  ]"
                >
                  <Button icon="more-horizontal" class="rounded-full h-8 w-8" />
                </Dropdown>
              </div>
            </div>
          </template>
        </FileUploader>
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
                          v-model="lead.data[field.name]"
                          class="form-control cursor-pointer [&_select]:cursor-pointer"
                        >
                          <template #prefix>
                            <IndicatorIcon
                              :class="leadStatuses[lead.data[field.name]].color"
                            />
                          </template>
                        </FormControl>
                        <FormControl
                          v-else-if="field.type === 'email'"
                          type="email"
                          class="form-control"
                          v-model="lead.data[field.name]"
                        />
                        <Autocomplete
                          v-else-if="field.type === 'link'"
                          :value="lead.data[field.name]"
                          :options="field.options"
                          @change="(e) => field.change(e)"
                          :placeholder="field.placeholder"
                          class="form-control"
                        />
                        <Autocomplete
                          v-else-if="field.type === 'user'"
                          :options="activeAgents"
                          :value="getUser(lead.data[field.name]).full_name"
                          @change="
                            (option) => (lead.data[field.name] = option.email)
                          "
                          class="form-control"
                          placeholder="Lead owner"
                        >
                          <template #target="{ togglePopover }">
                            <Button
                              variant="ghost"
                              @click="togglePopover()"
                              :label="getUser(lead.data[field.name]).full_name"
                              class="!justify-start w-full"
                            >
                              <template #prefix>
                                <UserAvatar
                                  :user="lead.data[field.name]"
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
                          :options="statusDropdownOptions(lead.data)"
                          class="w-full flex-1"
                        >
                          <template #default="{ open }">
                            <Button
                              :label="lead.data[field.name]"
                              class="justify-between w-full"
                            >
                              <template #prefix>
                                <IndicatorIcon
                                  :class="
                                    leadStatuses[lead.data[field.name]].color
                                  "
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
  leadStatuses,
  statusDropdownOptions,
  openWebsite,
  secondsToDuration,
} from '@/utils'
import { usersStore } from '@/stores/users'
import { contactsStore } from '@/stores/contacts'
import {
  createResource,
  createDocumentResource,
  createListResource,
  FileUploader,
  ErrorMessage,
  FeatherIcon,
  Autocomplete,
  FormControl,
  Dropdown,
  Tooltip,
  Avatar,
  call,
} from 'frappe-ui'
import { ref, computed, inject } from 'vue'
import { useRouter } from 'vue-router'

const { getUser, users } = usersStore()
const { getContact, contacts } = contactsStore()
const router = useRouter()

const makeCall = inject('makeOutgoingCall')

const props = defineProps({
  leadId: {
    type: String,
    required: true,
  },
})

const lead = createResource({
  url: 'crm.crm.doctype.crm_lead.api.get_lead',
  params: { name: props.leadId },
  cache: ['lead', props.leadId],
  auto: true,
})

const uLead = createDocumentResource({
  doctype: 'CRM Lead',
  name: props.leadId,
  setValue: {
    onSuccess: () => {
      lead.reload()
      contacts.reload()
    },
  },
})

function updateLead() {
  let leadCopy = { ...lead.data }
  delete leadCopy.activities
  uLead.setValue.submit({ ...leadCopy })
}

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
      content: all_activities(),
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

function all_activities() {
  if (!lead.data) return []
  if (!calls.data) return lead.data.activities
  console.log(lead.data.activities[0].creation)
  console.log(calls.data[0].creation)
  return [...lead.data.activities, ...calls.data].sort(
    (a, b) => new Date(b.creation) - new Date(a.creation)
  )
}

function changeLeadImage(file) {
  uLead.setValue.submit({ image: file.file_url })
}

function validateFile(file) {
  let extn = file.name.split('.').pop().toLowerCase()
  if (!['png', 'jpg', 'jpeg'].includes(extn)) {
    return 'Only PNG and JPG images are allowed'
  }
}

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
      label: 'About this lead',
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
          label: 'Job title',
          type: 'data',
          name: 'job_title',
        },
        {
          label: 'Source',
          type: 'link',
          name: 'source',
          placeholder: 'Select source...',
          options: [
            { label: 'Advertisement', value: 'Advertisement' },
            { label: 'Web', value: 'Web' },
            { label: 'Others', value: 'Others' },
          ],
          change: (data) => {
            lead.data.source = data.value
          },
        },
        {
          label: 'Industry',
          type: 'link',
          name: 'industry',
          placeholder: 'Select industry...',
          options: [
            { label: 'Advertising', value: 'Advertising' },
            { label: 'Agriculture', value: 'Agriculture' },
            { label: 'Banking', value: 'Banking' },
            { label: 'Others', value: 'Others' },
          ],
          change: (data) => {
            lead.data.industry = data.value
          },
        },
      ],
    },
    {
      label: 'Person',
      opened: true,
      fields: [
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
            lead.data.salutation = data.value
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
          type: 'email',
          name: 'email',
        },
        {
          label: 'Mobile no.',
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

function convertToDeal() {
  lead.data.status = 'Qualified'
  lead.data.is_deal = 1
  updateLead()
  router.push({ name: 'Deal', params: { dealId: lead.data.name } })
}

const showNoteModal = ref(false)
const note = ref({
  title: '',
  content: '',
})

const notes = createListResource({
  type: 'list',
  doctype: 'CRM Note',
  cache: ['Notes', props.leadId],
  fields: ['name', 'title', 'content', 'owner', 'modified'],
  filters: { lead: props.leadId },
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
        lead: props.leadId,
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
  cache: ['Call Logs', props.leadId],
  fields: [
    'name',
    'caller',
    'receiver',
    'from',
    'to',
    'duration',
    'start_time',
    'end_time',
    'status',
    'type',
    'recording_url',
    'creation',
    'note',
  ],
  filters: { lead: props.leadId },
  orderBy: 'creation desc',
  pageLength: 999,
  auto: true,
  transform: (docs) => {
    docs.forEach((doc) => {
      doc.activity_type =
        doc.type === 'Incoming' ? 'incoming_call' : 'outgoing_call'
      doc.duration = secondsToDuration(doc.duration)
      if (doc.type === 'Incoming') {
        doc.caller = {
          label: getContact(doc.from)?.full_name || 'Unknown',
          image: getContact(doc.from)?.image,
        }
        doc.receiver = {
          label: getUser(doc.receiver).full_name,
          image: getUser(doc.receiver).user_image,
        }
      } else {
        doc.caller = {
          label: getUser(doc.caller).full_name,
          image: getUser(doc.caller).user_image,
        }
        doc.receiver = {
          label: getContact(doc.to)?.full_name || 'Unknown',
          image: getContact(doc.to)?.image,
        }
      }
    })
    return docs
  },
})
</script>

<style scoped>
:deep(.form-control input),
:deep(.form-control select),
:deep(.form-control button) {
  border-color: transparent;
  background: white;
}

:deep(.form-control button svg) {
  color: white;
}
</style>
