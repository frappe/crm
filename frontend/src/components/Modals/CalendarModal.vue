<template>
  <Dialog v-model="show" :options="{ size: '2xl' }">
    <template #body>
      <div class="flex flex-col gap-5 m-6 mt-5">
        <div class="flex justify-between items-center">
          <div class="text-2xl font-semibold text-ink-gray-7">
            {{ __('Schedule an event') }}
          </div>
          <Button variant="ghost" class="w-7" @click="show = false">
            <FeatherIcon name="x" class="h-4 w-4" />
          </Button>
        </div>
        <div class="">
          <div class="flex flex-col w-full -ml-2">
            <TextInput
              ref="title"
              variant="ghost"
              v-model="_event.title"
              :placeholder="__('Add title')"
            />
            <TextEditor
              editor-class="!prose-sm overflow-auto min-h-[20px] max-h-80 px-2 rounded placeholder-ink-gray-4 focus:bg-surface-white focus:ring-0 text-ink-gray-8 transition-colors"
              :bubbleMenu="true"
              :content="_event.description"
              @change="(val) => (_event.description = val)"
              :placeholder="__('Add description')"
            />
          </div>
          <div class="border-t my-4" />
          <div class="flex justify-between items-center">
            <div class="flex items-center gap-x-2">
              <DurationIcon class="h-4 w-4 text-ink-gray-5" />
              <DatePicker
                class="max-w-28"
                v-model="_event.date"
                :formatter="(date) => getFormat(date, 'MMM D, YYYY')"
                :placeholder="__('Start Date')"
              />
              <TimePicker
                v-if="!_event.isFullDay"
                class="max-w-20"
                v-model="_event.from_time"
                :placeholder="__('Start Time')"
              />
              <div class="text-base text-ink-gray-6">-</div>
              <TimePicker
                v-if="!_event.isFullDay"
                class="max-w-20"
                v-model="_event.to_time"
                :placeholder="__('End Time')"
              />
              <DatePicker
                class="max-w-28"
                v-model="_event.date"
                :formatter="(date) => getFormat(date, 'MMM D, YYYY')"
                :placeholder="__('End Date')"
              />
            </div>
            <Switch
              v-model="_event.isFullDay"
              class="text-ink-gray-6"
              :label="__('All Day')"
            />
          </div>
          <div class="border-t mt-4" />
        </div>
        <div class="flex justify-between items-center">
          <div class="flex">
            <div class="flex items-center gap-x-2">
              <Button variant="ghost" @click="updateEventType">
                <FeatherIcon
                  :name="_event.eventType == 'Private' ? 'lock' : 'unlock'"
                  class="h-4 w-4"
                />
              </Button>
              <Button
                v-if="_event.id"
                variant="ghost"
                theme="red"
                @click="deleteEvent"
              >
                <FeatherIcon name="trash-2" class="h-4 w-4" />
              </Button>
            </div>
            <div v-if="error" class="flex items-center gap-x-2">
              <div class="h-full border-l mx-2" />
              <ErrorMessage :message="error" class="text-sm text-ink-red-3" />
            </div>
          </div>
          <Button :label="__('Save')" variant="solid" @click="saveEvent" />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import DurationIcon from '@/components/Icons/DurationIcon.vue'
import {
  Switch,
  ErrorMessage,
  TextInput,
  TextEditor,
  DatePicker,
  TimePicker,
} from 'frappe-ui'
import { getFormat } from '@/utils'
import { ref, nextTick, watch } from 'vue'

const emit = defineEmits(['save', 'delete'])

const show = defineModel()
const event = defineModel('event')

const error = ref(null)
const title = ref(null)

let _event = ref({})

function updateEventType() {
  if (_event.value.eventType == 'Private') {
    _event.value.eventType = 'Public'
  } else {
    _event.value.eventType = 'Private'
  }
}

function saveEvent() {
  error.value = null
  if (!_event.value.title) {
    error.value = __('Title is required')
    title.value.focus()
    return
  }
  emit('save', _event.value)
}

function deleteEvent() {
  emit('delete', _event.value.id)
}

watch(
  () => show.value,
  (value) => {
    if (!value) return
    nextTick(() => {
      title.value.el.focus()
      _event.value = { ...event.value }
    })
  },
)
</script>
