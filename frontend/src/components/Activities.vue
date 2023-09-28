<template>
  <div class="flex items-center justify-between px-10 py-5 text-lg font-medium">
    <div class="flex h-7 items-center text-xl font-semibold text-gray-800">
      {{ title }}
    </div>
    <Button
      v-if="title == 'Calls'"
      variant="solid"
      @click="makeCall(lead.data.mobile_no)"
    >
      <PhoneIcon class="h-4 w-4" />
    </Button>
    <Button v-else-if="title == 'Notes'" variant="solid" @click="showNote">
      <FeatherIcon name="plus" class="h-4 w-4" />
    </Button>
  </div>
  <div v-if="activities?.length" class="flex-1 overflow-y-auto">
    <div v-if="title == 'Notes'" class="grid grid-cols-3 gap-4 px-10 py-5 pt-0">
      <div
        v-for="note in activities"
        class="group flex h-48 cursor-pointer flex-col justify-between gap-2 rounded-md bg-gray-50 px-4 py-3 hover:bg-gray-100"
        @click="showNote(note)"
      >
        <div class="flex items-center justify-between">
          <div class="truncate text-lg font-medium">
            {{ note.title }}
          </div>
          <Dropdown
            :options="[
              {
                icon: 'trash-2',
                label: 'Delete',
                onClick: () => deleteNote(note.name),
              },
            ]"
            @click.stop
            class="h-6 w-6"
          >
            <Button
              icon="more-horizontal"
              variant="ghosted"
              class="!h-6 !w-6 hover:bg-gray-100"
            />
          </Dropdown>
        </div>
        <TextEditor
          v-if="note.content"
          :content="note.content"
          :editable="false"
          editor-class="!prose-sm max-w-none !text-sm text-gray-600 focus:outline-none"
          class="flex-1 overflow-hidden"
        />
        <div class="mt-1 flex items-center justify-between gap-2">
          <div class="flex items-center gap-2">
            <UserAvatar :user="note.owner" size="xs" />
            <div class="text-sm text-gray-800">
              {{ getUser(note.owner).full_name }}
            </div>
          </div>
          <Tooltip :text="dateFormat(note.modified, dateTooltipFormat)">
            <div class="text-sm text-gray-700">
              {{ timeAgo(note.modified) }}
            </div>
          </Tooltip>
        </div>
      </div>
    </div>
    <div v-else-if="title == 'Calls'">
      <div v-for="(call, i) in activities">
        <div class="grid grid-cols-[30px_minmax(auto,_1fr)] gap-4 px-10">
          <div
            class="relative flex justify-center after:absolute after:left-[50%] after:top-0 after:-z-10 after:border-l after:border-gray-200"
            :class="i != activities.length - 1 ? 'after:h-full' : 'after:h-4'"
          >
            <div
              class="z-10 mt-[15px] flex h-7 w-7 items-center justify-center rounded-full bg-gray-100"
            >
              <component
                :is="
                  call.type == 'Incoming' ? InboundCallIcon : OutboundCallIcon
                "
                class="text-gray-800"
              />
            </div>
          </div>
          <div
            class="mb-3 flex max-w-[70%] flex-col gap-3 rounded-md bg-gray-50 p-4"
          >
            <div class="flex items-center justify-between">
              <div>
                {{ call.type == 'Incoming' ? 'Inbound' : 'Outbound' }} call
              </div>
              <div>
                <Tooltip
                  class="text-sm text-gray-600"
                  :text="dateFormat(call.creation, dateTooltipFormat)"
                >
                  {{ timeAgo(call.creation) }}
                </Tooltip>
              </div>
            </div>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-1">
                <DurationIcon class="h-4 w-4 text-gray-600" />
                <div class="text-sm text-gray-600">Duration</div>
                <div class="text-sm">
                  {{ call.duration }}
                </div>
              </div>
              <div
                class="flex cursor-pointer select-none items-center gap-1"
                @click="call.show_recording = !call.show_recording"
              >
                <PlayIcon class="h-4 w-4 text-gray-600" />
                <div class="text-sm text-gray-600">
                  {{
                    call.show_recording ? 'Hide recording' : 'Listen to call'
                  }}
                </div>
              </div>
            </div>
            <div
              v-if="call.show_recording"
              class="flex items-center justify-between rounded border"
            >
              <audio
                class="audio-control"
                controls
                :src="call.recording_url"
              ></audio>
            </div>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-1">
                <Avatar
                  :image="call.caller.image"
                  :label="call.caller.label"
                  size="xl"
                />
                <div class="ml-1 flex flex-col gap-1">
                  <div class="text-base font-medium">
                    {{ call.caller.label }}
                  </div>
                  <div class="text-xs text-gray-600">
                    {{ call.from }}
                  </div>
                </div>
                <FeatherIcon
                  name="arrow-right"
                  class="mx-2 h-5 w-5 text-gray-600"
                />
                <Avatar
                  :image="call.receiver.image"
                  :label="call.receiver.label"
                  size="xl"
                />
                <div class="ml-1 flex flex-col gap-1">
                  <div class="text-base font-medium">
                    {{ call.receiver.label }}
                  </div>
                  <div class="text-xs text-gray-600">
                    {{ call.to }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-else v-for="(activity, i) in activities">
      <div class="grid grid-cols-[30px_minmax(auto,_1fr)] gap-4 px-10">
        <div
          class="relative flex justify-center before:absolute before:left-[50%] before:top-0 before:-z-10 before:border-l before:border-gray-200"
          :class="[
            i != activities.length - 1 ? 'before:h-full' : 'before:h-4',
            activity.other_versions
              ? 'after:translate-y-[calc(-50% - 4px)] after:absolute after:bottom-9 after:left-[50%] after:top-0 after:-z-10 after:w-8 after:rounded-bl-xl after:border-b after:border-l after:border-gray-200'
              : '',
          ]"
        >
          <div
            class="z-10 flex h-7 w-7 items-center justify-center rounded-full bg-gray-100"
            :class="{
              'mt-3': [
                'communication',
                'incoming_call',
                'outgoing_call',
              ].includes(activity.activity_type),
              'bg-white': ['added', 'removed', 'changed'].includes(
                activity.activity_type
              ),
            }"
          >
            <component
              :is="activity.icon"
              :class="
                ['added', 'removed', 'changed'].includes(activity.activity_type)
                  ? 'text-gray-600'
                  : 'text-gray-800'
              "
            />
          </div>
        </div>
        <div v-if="activity.activity_type == 'communication'" class="pb-6">
          <div
            class="cursor-pointer rounded-md bg-gray-50 p-3 text-base leading-6 transition-all duration-300 ease-in-out"
          >
            <div class="mb-3 flex items-center justify-between gap-2">
              <div class="flex items-center gap-2">
                <UserAvatar :user="activity.data.sender" size="md" />
                <span>{{ activity.data.sender_full_name }}</span>
                <span>&middot;</span>
                <Tooltip
                  class="text-sm text-gray-600"
                  :text="dateFormat(activity.creation, dateTooltipFormat)"
                >
                  {{ timeAgo(activity.creation) }}
                </Tooltip>
              </div>
              <div>
                <Button
                  variant="ghost"
                  icon="more-horizontal"
                  class="text-gray-600"
                />
              </div>
            </div>
            <div class="px-1" v-html="activity.data.content" />
          </div>
        </div>
        <div
          v-else-if="
            activity.activity_type == 'incoming_call' ||
            activity.activity_type == 'outgoing_call'
          "
          class="mb-3 flex max-w-[70%] flex-col gap-3 rounded-md bg-gray-50 p-4"
        >
          <div class="flex items-center justify-between">
            <div>
              {{ activity.type == 'Incoming' ? 'Inbound' : 'Outbound' }} call
            </div>
            <div>
              <Tooltip
                class="text-sm text-gray-600"
                :text="dateFormat(activity.creation, dateTooltipFormat)"
              >
                {{ timeAgo(activity.creation) }}
              </Tooltip>
            </div>
          </div>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-1">
              <DurationIcon class="h-4 w-4 text-gray-600" />
              <div class="text-sm text-gray-600">Duration</div>
              <div class="text-sm">
                {{ activity.duration }}
              </div>
            </div>
            <div
              class="flex cursor-pointer select-none items-center gap-1"
              @click="activity.show_recording = !activity.show_recording"
            >
              <PlayIcon class="h-4 w-4 text-gray-600" />
              <div class="text-sm text-gray-600">
                {{
                  activity.show_recording ? 'Hide recording' : 'Listen to call'
                }}
              </div>
            </div>
          </div>
          <div
            v-if="activity.show_recording"
            class="flex items-center justify-between rounded border"
          >
            <audio
              class="audio-control"
              controls
              :src="activity.recording_url"
            ></audio>
          </div>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-1">
              <Avatar
                :image="activity.caller.image"
                :label="activity.caller.label"
                size="xl"
              />
              <div class="ml-1 flex flex-col gap-1">
                <div class="text-base font-medium">
                  {{ activity.caller.label }}
                </div>
                <div class="text-xs text-gray-600">
                  {{ activity.from }}
                </div>
              </div>
              <FeatherIcon
                name="arrow-right"
                class="mx-2 h-5 w-5 text-gray-600"
              />
              <Avatar
                :image="activity.receiver.image"
                :label="activity.receiver.label"
                size="xl"
              />
              <div class="ml-1 flex flex-col gap-1">
                <div class="text-base font-medium">
                  {{ activity.receiver.label }}
                </div>
                <div class="text-xs text-gray-600">
                  {{ activity.to }}
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="mb-4 flex flex-col gap-5 py-1.5">
          <div class="flex items-start justify-stretch gap-2 text-base">
            <div class="inline-flex flex-wrap gap-1 text-gray-600">
              <span class="font-medium text-gray-800">{{
                activity.owner_name
              }}</span>
              <span v-if="activity.type">{{ activity.type }}</span>
              <span
                v-if="activity.data.field_label"
                class="max-w-xs truncate font-medium text-gray-800"
              >
                {{ activity.data.field_label }}
              </span>
              <span v-if="activity.value">{{ activity.value }}</span>
              <span
                v-if="activity.data.old_value"
                class="max-w-xs font-medium text-gray-800"
              >
                <div
                  class="flex items-center gap-1"
                  v-if="activity.options == 'User'"
                >
                  <UserAvatar :user="activity.data.old_value" size="xs" />
                  {{ getUser(activity.data.old_value).full_name }}
                </div>
                <div class="truncate" v-else>
                  {{ activity.data.old_value }}
                </div>
              </span>
              <span v-if="activity.to">to</span>
              <span
                v-if="activity.data.value"
                class="max-w-xs font-medium text-gray-800"
              >
                <div
                  class="flex items-center gap-1"
                  v-if="activity.options == 'User'"
                >
                  <UserAvatar :user="activity.data.value" size="xs" />
                  {{ getUser(activity.data.value).full_name }}
                </div>
                <div class="truncate" v-else>
                  {{ activity.data.value }}
                </div>
              </span>
            </div>

            <div class="ml-auto whitespace-nowrap">
              <Tooltip
                :text="dateFormat(activity.creation, dateTooltipFormat)"
                class="text-gray-600"
              >
                {{ timeAgo(activity.creation) }}
              </Tooltip>
            </div>
          </div>
          <div
            v-if="activity.other_versions && activity.show_others"
            v-for="activity in activity.other_versions"
            class="flex items-start justify-stretch gap-2 text-base"
          >
            <div class="flex items-start gap-1 text-gray-600">
              <div class="flex flex-1 items-center gap-1">
                <span
                  v-if="activity.data.field_label"
                  class="max-w-xs truncate text-gray-600"
                >
                  {{ activity.data.field_label }}
                </span>
                <FeatherIcon
                  name="arrow-right"
                  class="mx-1 h-4 w-4 text-gray-600"
                />
              </div>
              <div class="flex flex-wrap items-center gap-1">
                <span v-if="activity.type">{{ startCase(activity.type) }}</span>
                <span
                  v-if="activity.data.old_value"
                  class="max-w-xs font-medium text-gray-800"
                >
                  <div
                    class="flex items-center gap-1"
                    v-if="activity.options == 'User'"
                  >
                    <UserAvatar :user="activity.data.old_value" size="xs" />
                    {{ getUser(activity.data.old_value).full_name }}
                  </div>
                  <div class="truncate" v-else>
                    {{ activity.data.old_value }}
                  </div>
                </span>
                <span v-if="activity.to">to</span>
                <span
                  v-if="activity.data.value"
                  class="max-w-xs font-medium text-gray-800"
                >
                  <div
                    class="flex items-center gap-1"
                    v-if="activity.options == 'User'"
                  >
                    <UserAvatar :user="activity.data.value" size="xs" />
                    {{ getUser(activity.data.value).full_name }}
                  </div>
                  <div class="truncate" v-else>
                    {{ activity.data.value }}
                  </div>
                </span>
              </div>
            </div>

            <div class="ml-auto whitespace-nowrap">
              <Tooltip
                :text="dateFormat(activity.creation, dateTooltipFormat)"
                class="text-gray-600"
              >
                {{ timeAgo(activity.creation) }}
              </Tooltip>
            </div>
          </div>
          <div v-if="activity.other_versions">
            <Button
              :label="
                activity.show_others ? 'Hide all changes' : 'Show all changes'
              "
              variant="outline"
              @click="activity.show_others = !activity.show_others"
            >
              <template #suffix>
                <FeatherIcon
                  :name="activity.show_others ? 'chevron-up' : 'chevron-down'"
                  class="h-4 text-gray-600"
                />
              </template>
            </Button>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div
    v-else
    class="flex flex-1 flex-col items-center justify-center gap-3 text-xl font-medium text-gray-500"
  >
    <component :is="emptyTextIcon" class="h-10 w-10" />
    <span>{{ emptyText }}</span>
    <Button
      v-if="title == 'Calls'"
      variant="solid"
      label="Make a call"
      @click="makeCall(lead.data.mobile_no)"
    />
    <Button
      v-else-if="title == 'Notes'"
      variant="solid"
      label="Create note"
      @click="showNote"
    />
    <Button
      v-else-if="title == 'Emails'"
      variant="solid"
      label="Send email"
      @click="$refs.emailBox.show = true"
    />
    <Button v-else-if="title == 'Tasks'" variant="solid" label="Create task" />
  </div>
  <CommunicationArea
    ref="emailBox"
    v-if="['Emails', 'Activity'].includes(title)"
    v-model="lead"
    v-model:reload="reload_email"
  />
  <NoteModal v-model="showNoteModal" :note="note" @updateNote="updateNote" />
</template>
<script setup>
import UserAvatar from '@/components/UserAvatar.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import DurationIcon from '@/components/Icons/DurationIcon.vue'
import PlayIcon from '@/components/Icons/PlayIcon.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import DotIcon from '@/components/Icons/DotIcon.vue'
import EmailAtIcon from '@/components/Icons/EmailAtIcon.vue'
import InboundCallIcon from '@/components/Icons/InboundCallIcon.vue'
import OutboundCallIcon from '@/components/Icons/OutboundCallIcon.vue'
import CommunicationArea from '@/components/CommunicationArea.vue'
import NoteModal from '@/components/NoteModal.vue'
import {
  timeAgo,
  dateFormat,
  dateTooltipFormat,
  secondsToDuration,
  startCase,
} from '@/utils'
import { usersStore } from '@/stores/users'
import { contactsStore } from '@/stores/contacts'
import {
  Button,
  FeatherIcon,
  Tooltip,
  Dropdown,
  TextEditor,
  Avatar,
  createResource,
  createListResource,
  call,
} from 'frappe-ui'
import { ref, computed, h, defineModel, markRaw, watch } from 'vue'

const { getUser } = usersStore()
const { getContact } = contactsStore()

const props = defineProps({
  title: {
    type: String,
    default: 'Activity',
  },
})

const lead = defineModel()
const reload = defineModel('reload')

const reload_email = ref(false)

const versions = createResource({
  url: 'crm.fcrm.doctype.crm_lead.api.get_activities',
  params: { name: lead.value.data.name },
  cache: ['activity', lead.value.data.name],
  auto: true,
})

const calls = createListResource({
  type: 'list',
  doctype: 'CRM Call Log',
  cache: ['Call Logs', lead.value.data.name],
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
  filters: { lead: lead.value.data.name },
  orderBy: 'creation desc',
  pageLength: 999,
  auto: true,
  transform: (docs) => {
    docs.forEach((doc) => {
      doc.show_recording = false
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

const notes = createListResource({
  type: 'list',
  doctype: 'CRM Note',
  cache: ['Notes', lead.value.data.name],
  fields: ['name', 'title', 'content', 'owner', 'modified'],
  filters: { lead: lead.value.data.name },
  orderBy: 'modified desc',
  pageLength: 999,
  auto: true,
})

function all_activities() {
  if (!versions.data) return []
  if (!calls.data) return versions.data
  return [...versions.data, ...calls.data].sort(
    (a, b) => new Date(b.creation) - new Date(a.creation)
  )
}

const activities = computed(() => {
  let activities = []
  if (props.title == 'Activity') {
    activities = all_activities()
  } else if (props.title == 'Emails') {
    activities = versions.data.filter(
      (activity) => activity.activity_type === 'communication'
    )
  } else if (props.title == 'Calls') {
    return calls.data
  } else if (props.title == 'Notes') {
    return notes.data
  }
  activities.forEach((activity) => {
    activity.icon = timelineIcon(activity.activity_type, activity.is_lead)

    if (
      activity.activity_type == 'incoming_call' ||
      activity.activity_type == 'outgoing_call' ||
      activity.activity_type == 'communication'
    )
      return

    update_activities_details(activity)

    if (activity.other_versions) {
      activity.show_others = false
      activity.other_versions.forEach((other_version) => {
        update_activities_details(other_version)
      })
    }
  })
  return activities
})

function update_activities_details(activity) {
  activity.owner_name = getUser(activity.owner).full_name
  activity.type = ''
  activity.value = ''
  activity.to = ''

  if (activity.activity_type == 'creation') {
    activity.type = activity.data
  } else if (activity.activity_type == 'deal') {
    activity.type = 'converted the lead to this deal'
    activity.data.field_label = ''
    activity.data.value = ''
  } else if (activity.activity_type == 'added') {
    activity.type = 'added'
    activity.value = 'as'
  } else if (activity.activity_type == 'removed') {
    activity.type = 'removed'
    activity.value = 'value'
  } else if (activity.activity_type == 'changed') {
    activity.type = 'changed'
    activity.value = 'from'
    activity.to = 'to'
  }
}

const emptyText = computed(() => {
  let text = 'No emails communications'
  if (props.title == 'Calls') {
    text = 'No call logs'
  } else if (props.title == 'Notes') {
    text = 'No notes'
  } else if (props.title == 'Tasks') {
    text = 'No tasks'
  }
  return text
})

const emptyTextIcon = computed(() => {
  let icon = EmailIcon
  if (props.title == 'Calls') {
    icon = PhoneIcon
  } else if (props.title == 'Notes') {
    icon = NoteIcon
  } else if (props.title == 'Tasks') {
    icon = TaskIcon
  }
  return h(icon, { class: 'text-gray-500' })
})

function timelineIcon(activity_type, is_lead) {
  let icon
  switch (activity_type) {
    case 'creation':
      icon = is_lead ? LeadsIcon : DealsIcon
      break
    case 'deal':
      icon = DealsIcon
      break
    case 'communication':
      icon = EmailAtIcon
      break
    case 'incoming_call':
      icon = InboundCallIcon
      break
    case 'outgoing_call':
      icon = OutboundCallIcon
      break
    default:
      icon = DotIcon
  }

  return markRaw(icon)
}

const showNoteModal = ref(false)
const note = ref({
  title: '',
  content: '',
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

watch([reload, reload_email], ([reload_value, reload_email_value]) => {
  if (reload_value || reload_email_value) {
    versions.reload()
    reload.value = false
    reload_email.value = false
  }
})
</script>

<style scoped>
.audio-control {
  width: 100%;
  height: 40px;
  outline: none;
  border: none;
  background: none;
  cursor: pointer;
}

.audio-control::-webkit-media-controls-panel {
  background-color: white;
}
</style>
