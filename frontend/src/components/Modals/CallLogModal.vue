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
          class="flex h-7 items-center gap-2 text-base text-gray-800"
        >
          <div class="grid w-7 place-content-center">
            <component :is="field.icon" />
          </div>
          <div v-if="field.name == 'receiver'" class="flex items-center gap-1">
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
          <div v-else-if="field.name == 'recording_url'">
            <audio class="audio-control" controls :src="field.value"></audio>
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
    </template>
  </Dialog>
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
// import NoteModal from '@/components/Modals/NoteModal.vue'
import { FeatherIcon, Avatar, Tooltip, createResource } from 'frappe-ui'
import { ref, computed, h } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  callLog: {
    type: Object,
    default: {},
  },
})

const show = defineModel()
const router = useRouter()

const detailFields = computed(() => {
  let details = [
    {
      icon: h(FeatherIcon, {
        name: props.callLog.type.icon,
        class: 'h-3.5 w-3.5',
      }),
      name: 'type',
      value: props.callLog.type.label + ' Call',
    },
    {
      icon: ContactsIcon,
      name: 'receiver',
      value: {
        receiver: props.callLog.receiver,
        caller: props.callLog.caller,
      },
    },
    {
      icon:
        props.callLog.reference_doctype == 'CRM Lead' ? LeadsIcon : Dealsicon,
      name: 'reference_doctype',
      value: props.callLog.reference_doctype == 'CRM Lead' ? 'Lead' : 'Deal',
      link: () => {
        if (props.callLog.reference_doctype == 'CRM Lead') {
          router.push({
            name: 'Lead',
            params: { leadId: props.callLog.reference_docname },
          })
        } else {
          router.push({
            name: 'Deal',
            params: { dealId: props.callLog.reference_docname },
          })
        }
      },
    },
    {
      icon: CalendarIcon,
      name: 'creation',
      value: props.callLog.creation.label,
      tooltip: props.callLog.creation.label,
    },
    {
      icon: DurationIcon,
      name: 'duration',
      value: props.callLog.duration.label,
    },
    {
      icon: CheckCircleIcon,
      name: 'status',
      value: props.callLog.status.label,
      color: props.callLog.status.color,
    },
    {
      icon: h(FeatherIcon, {
        name: 'play',
        class: 'h-3.5 w-3.5',
      }),
      name: 'recording_url',
      value: props.callLog.recording_url,
    },
    {
      icon: NoteIcon,
      name: 'note',
      value: props.callLog.note,
    },
  ]

  return details.filter((detail) => detail.value)
})

async function updateNote(_note) {
  if (_note.title || _note.content) {
    let d = await call('frappe.client.set_value', {
      doctype: 'CRM Note',
      name: _callLog.data?.note,
      fieldname: _note,
    })
    if (d.name) {
      _callLog.reload()
    }
  }
}
</script>

<style scoped>
.audio-control {
  height: 40px;
  outline: none;
  border-radius: 10px;
  border: 1px solid gray;
  cursor: pointer;
}

.audio-control::-webkit-media-controls-panel {
  background-color: white;
}
</style>
