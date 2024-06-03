<template>
  <Dialog v-model="show">
    <template #body-title>
      <div class="flex items-center gap-3">
        <h3 class="text-2xl font-semibold leading-6 text-gray-900">
          {{ __('Call Details') }}
        </h3>
      </div>
    </template>
    <template #body-content>
      <div class="flex flex-col gap-3.5">
        <div
          v-for="field in detailFields"
          :key="field.name"
          class="flex gap-2 text-base text-gray-800"
        >
          <div class="grid size-7 place-content-center">
            <component :is="field.icon" />
          </div>
          <div class="flex min-h-7 w-full items-center gap-2">
            <div
              v-if="field.name == 'receiver'"
              class="flex items-center gap-1"
            >
              <Avatar
                :image="field.value.caller.image"
                :label="field.value.caller.label"
                size="sm"
              />
              <div class="ml-1 flex flex-col gap-1">
                {{ field.value.caller.label }}
              </div>
              <FeatherIcon
                name="arrow-right"
                class="mx-1 h-4 w-4 text-gray-600"
              />
              <Avatar
                :image="field.value.receiver.image"
                :label="field.value.receiver.label"
                size="sm"
              />
              <div class="ml-1 flex flex-col gap-1">
                {{ field.value.receiver.label }}
              </div>
            </div>
            <Tooltip v-else-if="field.tooltip" :text="field.tooltip">
              {{ field.value }}
            </Tooltip>
            <div class="w-full" v-else-if="field.name == 'recording_url'">
              <audio
                class="audio-control w-full"
                controls
                :src="field.value"
              ></audio>
            </div>
            <div
              class="w-full cursor-pointer rounded border px-2 pt-1.5 text-base text-gray-700"
              v-else-if="field.name == 'note'"
              @click="() => (showNoteModal = true)"
            >
              <FadedScrollableDiv class="max-h-24 min-h-16 overflow-y-auto">
                <div
                  v-if="field.value?.title"
                  :class="[field.value?.content ? 'mb-1 font-bold' : '']"
                  v-html="field.value?.title"
                />
                <div
                  v-if="field.value?.content"
                  v-html="field.value?.content"
                />
              </FadedScrollableDiv>
            </div>
            <div v-else :class="field.color ? `text-${field.color}-600` : ''">
              {{ field.value }}
            </div>
            <div v-if="field.link">
              <ArrowUpRightIcon
                class="h-4 w-4 shrink-0 cursor-pointer text-gray-600 hover:text-gray-800"
                @click="() => field.link()"
              />
            </div>
          </div>
        </div>
      </div>
    </template>
    <template
      v-if="
        callLog.doc?.type.label == 'Incoming' && !callLog.doc?.reference_docname
      "
      #actions
    >
      <Button
        class="w-full"
        variant="solid"
        :label="__('Create lead')"
        @click="createLead"
      />
    </template>
  </Dialog>
  <NoteModal v-model="showNoteModal" :note="callNoteDoc?.doc" />
</template>

<script setup>
import ArrowUpRightIcon from '@/components/Icons/ArrowUpRightIcon.vue'
import DurationIcon from '@/components/Icons/DurationIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import Dealsicon from '@/components/Icons/DealsIcon.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import CheckCircleIcon from '@/components/Icons/CheckCircleIcon.vue'
import NoteModal from '@/components/Modals/NoteModal.vue'
import FadedScrollableDiv from '@/components/FadedScrollableDiv.vue'
import {
  FeatherIcon,
  Avatar,
  Tooltip,
  createDocumentResource,
  call,
} from 'frappe-ui'
import { getCallLogDetail } from '@/utils/callLog'
import { ref, computed, h, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  name: {
    type: String,
    default: {},
  },
})

const show = defineModel()
const showNoteModal = ref(false)
const router = useRouter()
const callNoteDoc = ref(null)
const callLog = ref({})

const detailFields = computed(() => {
  if (!callLog.value.doc) return []
  let details = [
    {
      icon: h(FeatherIcon, {
        name: callLog.value.doc.type.icon,
        class: 'h-3.5 w-3.5',
      }),
      name: 'type',
      value: callLog.value.doc.type.label + ' Call',
    },
    {
      icon: ContactsIcon,
      name: 'receiver',
      value: {
        receiver: callLog.value.doc.receiver,
        caller: callLog.value.doc.caller,
      },
    },
    {
      icon:
        callLog.value.doc.reference_doctype == 'CRM Lead'
          ? LeadsIcon
          : Dealsicon,
      name: 'reference_doctype',
      value:
        callLog.value.doc.reference_doctype == 'CRM Lead' ? 'Lead' : 'Deal',
      link: () => {
        if (callLog.value.doc.reference_doctype == 'CRM Lead') {
          router.push({
            name: 'Lead',
            params: { leadId: callLog.value.doc.reference_docname },
          })
        } else {
          router.push({
            name: 'Deal',
            params: { dealId: callLog.value.doc.reference_docname },
          })
        }
      },
      condition: () => callLog.value.doc.reference_docname,
    },
    {
      icon: CalendarIcon,
      name: 'creation',
      value: callLog.value.doc.creation.label,
      tooltip: callLog.value.doc.creation.label,
    },
    {
      icon: DurationIcon,
      name: 'duration',
      value: callLog.value.doc.duration.label,
    },
    {
      icon: CheckCircleIcon,
      name: 'status',
      value: callLog.value.doc.status.label,
      color: callLog.value.doc.status.color,
    },
    {
      icon: h(FeatherIcon, {
        name: 'play-circle',
        class: 'h-4 w-4 mt-2',
      }),
      name: 'recording_url',
      value: callLog.value.doc.recording_url,
    },
    {
      icon: NoteIcon,
      name: 'note',
      value: callNoteDoc.value?.doc,
    },
  ]

  return details
    .filter((detail) => detail.value)
    .filter((detail) => (detail.condition ? detail.condition() : true))
})

function createLead() {
  call('crm.fcrm.doctype.crm_call_log.crm_call_log.create_lead_from_call_log', {
    call_log: callLog.value.doc,
  }).then((d) => {
    if (d) {
      router.push({ name: 'Lead', params: { leadId: d } })
    }
  })
}

watch(show, (val) => {
  if (val) {
    callLog.value = createDocumentResource({
      doctype: 'CRM Call Log',
      name: props.name,
      fields: [
        'name',
        'caller',
        'receiver',
        'duration',
        'type',
        'status',
        'from',
        'to',
        'note',
        'recording_url',
        'reference_doctype',
        'reference_docname',
        'creation',
      ],
      cache: ['call_log', props.name],
      auto: true,
      transform: (doc) => {
        for (const key in doc) {
          doc[key] = getCallLogDetail(key, doc)
        }
        return doc
      },
      onSuccess: (doc) => {
        if (!doc.note) {
          callNoteDoc.value = null
          return
        }
        callNoteDoc.value = createDocumentResource({
          doctype: 'FCRM Note',
          name: doc.note,
          fields: ['title', 'content'],
          cache: ['note', doc.note],
          auto: true,
        })
      },
    })
  }
})
</script>

<style scoped>
.audio-control {
  height: 36px;
  outline: none;
  border-radius: 10px;
  cursor: pointer;
  background-color: rgb(237, 237, 237);
}

audio::-webkit-media-controls-panel {
  background-color: rgb(237, 237, 237) !important;
}

.audio-control::-webkit-media-controls-panel {
  background-color: white;
}
</style>
