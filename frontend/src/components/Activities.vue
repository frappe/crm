<template>
  <div class="p-5 flex items-center justify-between font-medium text-lg">
    <div>{{ title }}</div>
    <Button v-if="title == 'Calls'" variant="solid" @click="emit('makeCall')">
      <PhoneIcon class="w-4 h-4" />
    </Button>
    <Button
      v-else-if="title == 'Notes'"
      variant="solid"
      @click="emit('makeNote')"
    >
      <FeatherIcon name="plus" class="w-4 h-4" />
    </Button>
  </div>
  <div v-if="activities.length" class="overflow-y-auto">
    <div v-if="title == 'Notes'" class="grid grid-cols-3 gap-4 p-5 pt-0">
      <div
        v-for="note in activities"
        class="group flex flex-col justify-between gap-2 px-4 py-3 border rounded-lg h-48 shadow-sm hover:bg-gray-50 cursor-pointer"
        @click="emit('makeNote', note)"
      >
        <div class="flex items-center justify-between">
          <div class="text-lg font-medium truncate">
            {{ note.title }}
          </div>
          <Dropdown
            :options="[
              {
                icon: 'trash-2',
                label: 'Delete',
                onClick: () => emit('deleteNote', note.name),
              },
            ]"
            @click.stop
            class="h-6 w-6"
          >
            <Button
              icon="more-horizontal"
              variant="ghosted"
              class="hover:bg-white !h-6 !w-6"
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
        <div class="flex items-center justify-between mt-1 gap-2">
          <div class="flex items-center gap-2">
            <UserAvatar :user="note.owner" size="xs" />
            <div class="text-sm text-gray-800">
              {{ note.owner }}
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
        <div class="grid grid-cols-[30px_minmax(auto,_1fr)] gap-4 px-5">
          <div
            class="relative flex justify-center after:absolute after:border-l after:border-gray-300 after:top-0 after:left-[50%] after:-z-10"
            :class="i != activities.length - 1 ? 'after:h-full' : 'after:h-4'"
          >
            <div
              class="flex items-center justify-center rounded-full outline outline-4 outline-white w-6 h-6 bg-gray-200 mt-[15px] z-10"
            >
              <FeatherIcon
                :name="
                  call.type == 'Incoming' ? 'phone-incoming' : 'phone-outgoing'
                "
                class="w-3.5 h-3.5 text-gray-600"
              />
            </div>
          </div>
          <div class="flex flex-col gap-3 border rounded-lg p-4 mb-3 shadow-sm max-w-[60%]">
            <div class="flex items-center justify-between">
              <div>
                {{ call.type == 'Incoming' ? 'Inbound' : 'Outbound' }} call
              </div>
              <div>
                <Tooltip
                  class="text-gray-600 text-sm"
                  :text="dateFormat(call.modified, dateTooltipFormat)"
                >
                  {{ timeAgo(call.modified) }}
                </Tooltip>
              </div>
            </div>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-1">
                <DurationIcon class="w-4 h-4 text-gray-600" />
                <div class="text-sm text-gray-600">Duration</div>
                <div class="text-sm">{{ call.duration }}s</div>
              </div>
              <div
                class="flex items-center gap-1 cursor-pointer select-none"
                @click="call.show_recording = !call.show_recording"
              >
                <PlayIcon class="w-4 h-4 text-gray-600" />
                <div class="text-sm text-gray-600">
                  {{
                    call.show_recording ? 'Hide recording' : 'Listen to call'
                  }}
                </div>
              </div>
            </div>
            <div
              v-if="call.show_recording"
              class="flex items-center justify-between border rounded"
            >
              <audio
                class="audio-control"
                controls
                :src="call.recording_url"
              ></audio>
            </div>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-1">
                <div class="text-sm">{{ call.from }}</div>
                <FeatherIcon name="arrow-right" class="w-4 h-4 text-gray-600" />
                <div class="text-sm">{{ call.to }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-else v-for="(activity, i) in activities">
      <div class="grid grid-cols-[30px_minmax(auto,_1fr)] gap-4 px-5">
        <div
          class="relative flex justify-center after:absolute after:border-l after:border-gray-300 after:top-0 after:left-[50%] after:-z-10"
          :class="i != activities.length - 1 ? 'after:h-full' : 'after:h-4'"
        >
          <div
            class="flex items-center justify-center rounded-full outline outline-4 outline-white w-6 h-6 bg-gray-200 z-10"
            :class="{ 'mt-[15px]': activity.activity_type == 'communication' }"
          >
            <FeatherIcon
              :name="activity.icon"
              class="w-3.5 h-3.5 text-gray-600"
            />
          </div>
        </div>
        <div v-if="activity.activity_type == 'communication'" class="pb-6">
          <div
            class="shadow-sm border max-w-[80%] rounded-xl p-3 text-base cursor-pointer leading-6 transition-all duration-300 ease-in-out"
          >
            <div class="flex items-center justify-between gap-2 mb-3">
              <div class="flex items-center gap-2">
                <UserAvatar :user="activity.data.sender" size="md" />
                <span>{{ activity.data.sender_full_name }}</span>
                <span>&middot;</span>
                <Tooltip
                  class="text-gray-600 text-sm"
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
        <div v-else class="flex flex-col gap-3 pb-6">
          <div
            class="flex items-start justify-stretch gap-2 text-base leading-6"
          >
            <UserAvatar :user="activity.owner" size="md" />

            <div class="inline-flex flex-wrap gap-1 text-gray-600">
              <span class="text-gray-900">{{ activity.owner_name }}</span>
              <span v-if="activity.type">{{ activity.type }}</span>
              <span
                v-if="activity.data.field_label"
                class="text-gray-900 truncate max-w-xs"
              >
                {{ activity.data.field_label }}
              </span>
              <span v-if="activity.value">{{ activity.value }}</span>
              <span
                v-if="activity.data.old_value"
                class="text-gray-900 truncate max-w-xs"
              >
                {{ activity.data.old_value }}
              </span>
              <span v-if="activity.to">to</span>
              <span
                v-if="activity.data.value"
                class="text-gray-900 truncate max-w-xs"
              >
                {{ activity.data.value }}
              </span>
            </div>

            <div class="ml-auto whitespace-nowrap">
              <Tooltip
                :text="dateFormat(activity.creation, dateTooltipFormat)"
                class="text-sm text-gray-600 leading-6"
              >
                {{ timeAgo(activity.creation) }}
              </Tooltip>
            </div>
          </div>
          <div
            v-if="activity.activity_type == 'comment'"
            class="py-3 px-4 rounded-xl shadow-sm border max-w-[80%] text-base cursor-pointer leading-6 transition-all duration-300 ease-in-out"
            v-html="activity.data"
          />
        </div>
      </div>
    </div>
  </div>
  <div
    v-else
    class="flex-1 flex flex-col gap-3 items-center justify-center font-medium text-xl text-gray-500"
  >
    <component :is="emptyTextIcon" class="w-10 h-10" />
    <span>{{ emptyText }}</span>
    <Button
      v-if="title == 'Calls'"
      variant="solid"
      label="Make a call"
      @click="emit('makeCall')"
    />
    <Button
      v-else-if="title == 'Notes'"
      variant="solid"
      label="Create note"
      @click="emit('makeNote')"
    />
  </div>
</template>
<script setup>
import UserAvatar from '@/components/UserAvatar.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import DurationIcon from '@/components/Icons/DurationIcon.vue'
import PlayIcon from '@/components/Icons/PlayIcon.vue'
import { timeAgo, dateFormat, dateTooltipFormat } from '@/utils'
import { usersStore } from '@/stores/users'
import { Button, FeatherIcon, Tooltip, Dropdown, TextEditor } from 'frappe-ui'
import { computed, h } from 'vue'

const { getUser } = usersStore()

const props = defineProps({
  title: {
    type: String,
    default: 'Activity',
  },
  activities: {
    type: Array,
    default: [],
  },
})

const emit = defineEmits(['makeCall', 'makeNote', 'deleteNote'])

const activities = computed(() => {
  if (props.title == 'Calls') {
    props.activities.forEach((activity) => {
      activity.show_recording = false
    })
    return props.activities
  }
  props.activities.forEach((activity) => {
    activity.owner_name = getUser(activity.owner).full_name
    activity.icon = timelineIcon(activity.activity_type)
    activity.type = ''
    activity.value = ''
    activity.to = ''

    if (activity.activity_type == 'creation') {
      activity.type = activity.data
    } else if (activity.activity_type == 'comment') {
      activity.type = 'added a comment'
    } else if (activity.activity_type == 'added') {
      activity.type = 'added'
      activity.value = 'value as'
    } else if (activity.activity_type == 'removed') {
      activity.type = 'removed'
      activity.value = 'value'
    } else if (activity.activity_type == 'changed') {
      activity.type = 'changed'
      activity.value = 'value from'
      activity.to = 'to'
    }
  })
  return props.activities
})

const emptyText = computed(() => {
  let text = 'No emails communications'
  if (props.title == 'Calls') {
    text = 'No call logs'
  } else if (props.title == 'Notes') {
    text = 'No notes'
  }
  return text
})

const emptyTextIcon = computed(() => {
  let icon = EmailIcon
  if (props.title == 'Calls') {
    icon = PhoneIcon
  } else if (props.title == 'Notes') {
    icon = NoteIcon
  }
  return h(icon, { class: 'text-gray-500' })
})

function timelineIcon(activity_type) {
  if (activity_type == 'creation') {
    return 'plus'
  } else if (activity_type == 'removed') {
    return 'trash-2'
  } else if (activity_type == 'communication') {
    return 'at-sign'
  } else if (activity_type == 'comment') {
    return 'file-text'
  }
  return 'edit'
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
