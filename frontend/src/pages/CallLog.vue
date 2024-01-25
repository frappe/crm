<template>
  <LayoutHeader v-if="callLog.data">
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <Button
        v-if="callLog.data.type == 'Incoming' && !callLog.data.lead"
        variant="solid"
        label="Create lead"
        @click="createLead"
      >
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </template>
  </LayoutHeader>
  <div class="border-b"></div>
  <div v-if="callLog.data" class="max-w-lg p-6">
    <div class="pb-3 text-base font-medium">Call details</div>
    <div class="mb-3 flex flex-col gap-4 rounded-lg border p-4 shadow-sm">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <FeatherIcon
            :name="
              callLog.data.type == 'Incoming'
                ? 'phone-incoming'
                : 'phone-outgoing'
            "
            class="h-4 w-4 text-gray-600"
          />
          <div class="font-medium">
            {{ callLog.data.type == 'Incoming' ? 'Inbound' : 'Outbound' }} call
          </div>
        </div>
        <div>
          <Badge
            :variant="'subtle'"
            :theme="statusColorMap[callLog.data.status]"
            size="md"
            :label="statusLabelMap[callLog.data.status]"
          />
        </div>
      </div>
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-1">
          <Avatar
            :image="callLog.data.caller.image"
            :label="callLog.data.caller.label"
            size="xl"
          />
          <div class="ml-1 flex flex-col gap-1">
            <div class="text-base font-medium">
              {{ callLog.data.caller.label }}
            </div>
            <div class="text-xs text-gray-600">
              {{ callLog.data.from }}
            </div>
          </div>
          <FeatherIcon name="arrow-right" class="mx-2 h-5 w-5 text-gray-600" />
          <Avatar
            :image="callLog.data.receiver.image"
            :label="callLog.data.receiver.label"
            size="xl"
          />
          <div class="ml-1 flex flex-col gap-1">
            <div class="text-base font-medium">
              {{ callLog.data.receiver.label }}
            </div>
            <div class="text-xs text-gray-600">
              {{ callLog.data.to }}
            </div>
          </div>
        </div>
      </div>
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-1">
          <DurationIcon class="h-4 w-4 text-gray-600" />
          <div class="text-sm text-gray-600">Duration</div>
          <div class="text-sm">{{ callLog.data.duration }}</div>
        </div>
        <div>
          <Tooltip
            class="text-sm text-gray-600"
            :text="dateFormat(callLog.data.creation, dateTooltipFormat)"
          >
            {{ timeAgo(callLog.data.creation) }}
          </Tooltip>
        </div>
      </div>
    </div>

    <div v-if="callLog.data.recording_url" class="mt-6">
      <div class="mb-3 text-base font-medium">Call recording</div>
      <div class="flex items-center justify-between rounded border shadow-sm">
        <audio
          class="audio-control"
          controls
          :src="callLog.data.recording_url"
        ></audio>
      </div>
    </div>

    <div v-if="callLog.data.note" class="mt-6">
      <div class="mb-3 text-base font-medium">Call note</div>
      <div
        class="flex h-56 cursor-pointer flex-col gap-3 rounded border p-4 shadow-sm"
        @click="showNoteModal = true"
      >
        <div class="truncate text-lg font-medium">
          {{ callLog.data.note_doc.title }}
        </div>
        <TextEditor
          v-if="callLog.data.note_doc.content"
          :content="callLog.data.note_doc.content"
          :editable="false"
          editor-class="!prose-sm max-w-none !text-sm text-gray-600 focus:outline-none"
          class="flex-1 overflow-hidden"
        />
      </div>
    </div>

    <div v-if="callLog.data.lead" class="mt-6">
      <div class="mb-3 text-base font-medium">Lead</div>

      <Button
        variant="outline"
        :route="{ name: 'Lead', params: { leadId: callLog.data.lead } }"
        :label="callLog.data.lead_name"
        class="p-4"
      >
        <template #prefix><Avatar :label="callLog.data.lead_name" /></template>
      </Button>
    </div>
  </div>
  <NoteModal
    v-model="showNoteModal"
    :note="callLog.data?.note_doc"
    @after="updateNote"
  />
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import DurationIcon from '@/components/Icons/DurationIcon.vue'
import NoteModal from '@/components/Modals/NoteModal.vue'
import {
  dateFormat,
  timeAgo,
  dateTooltipFormat,
  secondsToDuration,
} from '@/utils'
import {
  TextEditor,
  Avatar,
  call,
  Tooltip,
  createResource,
  Breadcrumbs,
} from 'frappe-ui'
import { usersStore } from '@/stores/users'
import { contactsStore } from '@/stores/contacts'
import { viewsStore } from '@/stores/views'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const { getUser } = usersStore()
const { contacts, getContact, getLeadContact } = contactsStore()
const { getDefaultView } = viewsStore()

const props = defineProps({
  callLogId: {
    type: String,
    required: true,
  },
})

const showNoteModal = ref(false)

const callLog = createResource({
  url: 'crm.fcrm.doctype.crm_call_log.crm_call_log.get_call_log',
  auto: true,
  cache: ['callLog', props.callLogId],
  params: {
    name: props.callLogId,
  },
  transform: (doc) => {
    doc.duration = secondsToDuration(doc.duration)
    if (doc.type === 'Incoming') {
      doc.caller = {
        label:
          getContact(doc.from)?.full_name ||
          getLeadContact(doc.from)?.full_name ||
          'Unknown',
        image: getContact(doc.from)?.image || getLeadContact(doc.from)?.image,
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
        label:
          getContact(doc.to)?.full_name ||
          getLeadContact(doc.to)?.full_name ||
          'Unknown',
        image: getContact(doc.to)?.image || getLeadContact(doc.to)?.image,
      }
    }
    return doc
  },
})

async function updateNote(_note) {
  if (_note.title || _note.content) {
    let d = await call('frappe.client.set_value', {
      doctype: 'CRM Note',
      name: callLog.data?.note,
      fieldname: _note,
    })
    if (d.name) {
      callLog.reload()
    }
  }
}

function createLead() {
  call('crm.fcrm.doctype.crm_call_log.crm_call_log.create_lead_from_call_log', {
    call_log: callLog.data,
  }).then((d) => {
    if (d) {
      callLog.reload()
      contacts.reload()
      router.push({ name: 'Lead', params: { leadId: d } })
    }
  })
}

const breadcrumbs = computed(() => {
  let defaultView = getDefaultView()
  let route = { name: 'Call Logs' }
  if (defaultView?.route_name == 'Call Logs' && defaultView?.is_view) {
    route = { name: 'Call Logs', query: { view: defaultView.name } }
  }
  let items = [{ label: 'Call Logs', route: route }]
  items.push({
    label: callLog.data?.caller.label,
    route: { name: 'Call Log', params: { callLogId: props.callLogId } },
  })
  return items
})

const statusLabelMap = {
  Completed: 'Completed',
  Initiated: 'Initiated',
  Busy: 'Declined',
  Failed: 'Failed',
  Queued: 'Queued',
  Cancelled: 'Cancelled',
  Ringing: 'Ringing',
  'No Answer': 'Missed Call',
  'In Progress': 'In Progress',
}

const statusColorMap = {
  Completed: 'green',
  Busy: 'orange',
  Failed: 'red',
  Initiated: 'gray',
  Queued: 'gray',
  Cancelled: 'gray',
  Ringing: 'gray',
  'No Answer': 'red',
  'In Progress': 'blue',
}
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
