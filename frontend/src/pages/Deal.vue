<template>
  <LayoutHeader v-if="deal.data">
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <Autocomplete
        :options="activeAgents"
        :value="getUser(deal.data.lead_owner).full_name"
        @change="(option) => updateAssignedAgent(option.email)"
        placeholder="Deal owner"
      >
        <template #prefix>
          <UserAvatar class="mr-2" :user="deal.data.lead_owner" size="sm" />
        </template>
        <template #item-prefix="{ option }">
          <UserAvatar class="mr-2" :user="option.email" size="sm" />
        </template>
      </Autocomplete>
      <Dropdown :options="statusDropdownOptions(deal.data, 'deal', updateDeal)">
        <template #default="{ open }">
          <Button :label="deal.data.deal_status">
            <template #prefix>
              <IndicatorIcon
                :class="dealStatuses[deal.data.deal_status].color"
              />
            </template>
            <template #suffix
              ><FeatherIcon
                :name="open ? 'chevron-up' : 'chevron-down'"
                class="h-4 text-gray-600"
            /></template>
          </Button>
        </template>
      </Dropdown>
    </template>
  </LayoutHeader>
  <div v-if="deal.data" class="flex h-full overflow-hidden">
    <TabGroup as="div" class="flex flex-col flex-1" @change="onTabChange">
      <TabList class="flex items-center gap-6 border-b pl-5 relative">
        <Tab
          ref="tabRef"
          as="template"
          v-for="tab in tabs"
          :key="tab.label"
          v-slot="{ selected }"
        >
          <button
            class="flex items-center gap-2 py-2.5 -mb-[1px] text-base text-gray-600 border-b border-transparent hover:text-gray-900 hover:border-gray-400 transition-all duration-300 ease-in-out"
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
      <TabPanels class="flex flex-1 overflow-hidden">
        <TabPanel
          class="flex-1 flex flex-col overflow-y-auto"
          v-for="tab in tabs"
          :key="tab.label"
        >
          <Activities
            :title="tab.activityTitle"
            :activities="tab.content"
            v-model="deal"
            @makeNote="(e) => showNote(e)"
            @deleteNote="(e) => deleteNote(e)"
          />
        </TabPanel>
      </TabPanels>
    </TabGroup>
    <div class="flex flex-col justify-between border-l w-[352px]">
      <div
        class="flex items-center border-b px-5 py-2.5 h-[41px] font-semibold text-lg"
      >
        About this deal
      </div>
      <FileUploader @success="changeDealImage" :validateFile="validateFile">
        <template #default="{ openFileSelector, error }">
          <div class="flex gap-5 items-center justify-start p-5 border-b">
            <div class="relative w-[88px] h-[88px] group">
              <Avatar
                size="3xl"
                class="w-[88px] h-[88px]"
                :label="deal.data.organization_name"
                :image="deal.data.organization_logo"
              />
              <Dropdown
                :options="[
                  {
                    icon: 'upload',
                    label: deal.data.organization_logo
                      ? 'Change image'
                      : 'Upload image',
                    onClick: openFileSelector,
                  },
                  {
                    icon: 'trash-2',
                    label: 'Remove image',
                    onClick: () => {
                      deal.data.organization_logo = ''
                      updateDeal('organization_logo', '')
                    },
                  },
                ]"
                class="!absolute bottom-0 left-0 right-0"
              >
                <div
                  class="absolute bottom-0 left-0 right-0 rounded-b-full z-1 h-11 flex items-center justify-center pt-3 bg-black bg-opacity-40 cursor-pointer opacity-0 group-hover:opacity-100 duration-300 ease-in-out"
                  style="
                    -webkit-clip-path: inset(12px 0 0 0);
                    clip-path: inset(12px 0 0 0);
                  "
                >
                  <CameraIcon class="h-6 w-6 text-white cursor-pointer" />
                </div>
              </Dropdown>
            </div>
            <div class="flex flex-col gap-2.5 truncate">
              <Tooltip :text="deal.data.organization_name">
                <div class="font-medium text-2xl truncate">
                  {{ deal.data.organization_name }}
                </div>
              </Tooltip>
              <div class="flex gap-1.5">
                <Tooltip text="Make a call...">
                  <Button
                    class="h-7 w-7"
                    @click="() => makeCall(deal.data.mobile_no)"
                  >
                    <PhoneIcon class="h-4 w-4" />
                  </Button>
                </Tooltip>
                <Button class="h-7 w-7">
                  <EmailIcon class="h-4 w-4" />
                </Button>
                <Tooltip text="Go to website...">
                  <Button class="h-7 w-7">
                    <LinkIcon
                      class="h-4 w-4"
                      @click="openWebsite(deal.data.website)"
                    />
                  </Button>
                </Tooltip>
              </div>
              <ErrorMessage :message="error" />
            </div>
          </div>
        </template>
      </FileUploader>
      <div class="flex-1 flex flex-col justify-between overflow-hidden">
        <div class="flex flex-col overflow-y-auto">
          <div
            v-for="(section, i) in detailSections"
            :key="section.label"
            class="flex flex-col p-3"
            :class="{ 'border-b': i !== detailSections.length - 1 }"
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
                        :value="deal.data[field.name]"
                        @change.stop="
                          updateDeal(field.name, $event.target.value)
                        "
                        :debounce="500"
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
                        :value="deal.data[field.name]"
                        @change.stop="
                          updateDeal(field.name, $event.target.value)
                        "
                        :debounce="500"
                      />
                      <Autocomplete
                        v-else-if="field.type === 'link'"
                        :value="deal.data[field.name]"
                        :options="field.options"
                        @change="(e) => field.change(e)"
                        :placeholder="field.placeholder"
                        class="form-control"
                      />
                      <Autocomplete
                        v-else-if="field.type === 'user'"
                        :options="activeAgents"
                        :value="getUser(deal.data[field.name]).full_name"
                        @change="(option) => updateAssignedAgent(option.email)"
                        class="form-control"
                        :placeholder="deal.placeholder"
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
                        :options="
                          statusDropdownOptions(deal.data, 'deal', updateDeal)
                        "
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
                                class="h-4 text-gray-600"
                              />
                            </template>
                          </Button>
                        </template>
                      </Dropdown>
                      <FormControl
                        v-else-if="field.type === 'date'"
                        type="date"
                        :value="deal.data[field.name]"
                        @change.stop="
                          updateDeal(field.name, $event.target.value)
                        "
                        :debounce="500"
                        class="form-control"
                      />
                      <FormControl
                        v-else-if="field.type === 'number'"
                        type="number"
                        :value="deal.data[field.name]"
                        @change.stop="
                          updateDeal(field.name, $event.target.value)
                        "
                        :debounce="500"
                        class="form-control"
                      />
                      <FormControl
                        v-else-if="field.type === 'tel'"
                        type="tel"
                        :value="deal.data[field.name]"
                        @change.stop="
                          updateDeal(field.name, $event.target.value)
                        "
                        :debounce="500"
                        class="form-control"
                      />
                      <FormControl
                        v-else
                        type="text"
                        :value="deal.data[field.name]"
                        @change.stop="
                          updateDeal(field.name, $event.target.value)
                        "
                        :debounce="500"
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
    </div>
  </div>
  <NoteModal v-model="showNoteModal" :note="note" @updateNote="updateNote" />
</template>
<script setup>
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import LinkIcon from '@/components/Icons/LinkIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Toggler from '@/components/Toggler.vue'
import Activities from '@/components/Activities.vue'
import Breadcrumbs from '@/components/Breadcrumbs.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import NoteModal from '@/components/NoteModal.vue'
import { TabGroup, TabList, Tab, TabPanels, TabPanel } from '@headlessui/vue'
import { TransitionPresets, useTransition } from '@vueuse/core'
import {
  dealStatuses,
  statusDropdownOptions,
  openWebsite,
  secondsToDuration,
  createToast,
} from '@/utils'
import { usersStore } from '@/stores/users'
import { contactsStore } from '@/stores/contacts'
import {
  createResource,
  createListResource,
  FeatherIcon,
  FileUploader,
  ErrorMessage,
  Autocomplete,
  FormControl,
  Dropdown,
  Tooltip,
  Avatar,
  call,
} from 'frappe-ui'
import { ref, computed } from 'vue'

const { getUser, users } = usersStore()
const { getContact, contacts } = contactsStore()

const props = defineProps({
  dealId: {
    type: String,
    required: true,
  },
})

const deal = createResource({
  url: 'crm.fcrm.doctype.crm_lead.api.get_lead',
  params: { name: props.dealId },
  cache: ['deal', props.dealId],
  auto: true,
})

function updateDeal(fieldname, value) {
  createResource({
    url: 'frappe.client.set_value',
    params: {
      doctype: 'CRM Lead',
      name: props.dealId,
      fieldname,
      value,
    },
    auto: true,
    onSuccess: () => {
      deal.reload()
      contacts.reload()
      createToast({
        title: 'Deal updated',
        icon: 'check',
        iconClasses: 'text-green-600',
      })
    },
    onError: (err) => {
      createToast({
        title: 'Error updating deal',
        text: err.messages?.[0],
        icon: 'x',
        iconClasses: 'text-red-600',
      })
    },
  })
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
      content: all_activities(),
      activityTitle: 'Activity',
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

function all_activities() {
  if (!deal.data) return []
  if (!calls.data) return deal.data.activities
  return [...deal.data.activities, ...calls.data].sort(
    (a, b) => new Date(b.creation) - new Date(a.creation)
  )
}

function changeDealImage(file) {
  deal.data.organization_logo = file.file_url
  updateDeal('organization_logo', file.file_url)
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
            deal.data.salutation = data.value
            updateDeal('salutation', data.value)
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
  filters: { lead: props.dealId },
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

function updateAssignedAgent(email) {
  deal.data.lead_owner = email
  updateDeal('lead_owner', email)
}
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
