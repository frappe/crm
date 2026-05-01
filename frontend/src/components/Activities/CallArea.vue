<template>
  <div>
    <div class="mb-1 flex items-center justify-stretch gap-2 py-1 text-base">
      <div class="inline-flex items-center flex-wrap gap-1 text-ink-gray-5">
        <Avatar
          :image="call._caller.image"
          :label="call._caller.label"
          size="md"
        />
        <span class="font-medium text-ink-gray-8 ml-1">
          {{ call._caller.label }}
        </span>
        <span>{{
          call.type == 'Incoming'
            ? __('has reached out')
            : __('has made a call')
        }}</span>
      </div>
      <div class="ml-auto whitespace-nowrap">
        <Tooltip :text="formatDate(call.creation)">
          <div class="text-sm text-ink-gray-5">
            {{ __(timeAgo(call.creation)) }}
          </div>
        </Tooltip>
      </div>
    </div>
    <div
      class="flex flex-col gap-2 border cursor-pointer border-outline-gray-modals rounded-md bg-surface-cards px-3 py-2.5 text-ink-gray-9"
      @click="showCallLogDetailModal = true"
    >
      <div class="flex items-center justify-between">
        <div class="inline-flex gap-2 items-center text-base font-medium">
          <div>
            {{
              call.type == 'Incoming' ? __('Inbound Call') : __('Outbound Call')
            }}
          </div>
        </div>
        <div>
          <MultipleAvatar
            :avatars="[
              {
                image: call._caller.image,
                label: call._caller.label,
                name: call._caller.label,
              },
              {
                image: call._receiver.image,
                label: call._receiver.label,
                name: call._receiver.label,
              },
            ]"
            size="sm"
          />
        </div>
      </div>
      <div class="flex items-center flex-wrap gap-2">
        <Badge :label="formatDate(call.creation, 'MMM D, dddd')">
          <template #prefix>
            <CalendarIcon class="size-3" />
          </template>
        </Badge>
        <Badge v-if="call.status == 'Completed'" :label="call._duration">
          <template #prefix>
            <DurationIcon class="size-3" />
          </template>
        </Badge>
        <Badge
          v-if="call.recording_url"
          :label="call.show_recording ? __('Hide Recording') : __('Listen')"
          class="cursor-pointer"
          @click.stop="call.show_recording = !call.show_recording"
        >
          <template #prefix>
            <PlayIcon class="size-3" />
          </template>
        </Badge>
        <Badge
          :label="statusLabelMap[call.status]"
          :theme="statusColorMap[call.status]"
        />
      </div>
      <div
        v-if="
          call.show_recording &&
          call.recording_url &&
          callLog?.data?.recording_url_path
        "
        class="flex flex-col items-center justify-between"
        @click.stop
      >
        <AudioPlayer :src="callLog.data.recording_url_path" />
      </div>
    </div>
    <CallLogDetailModal
      v-model="showCallLogDetailModal"
      v-model:callLog="callLog"
    />
  </div>
</template>
<script setup>
import PlayIcon from '@/components/Icons/PlayIcon.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import DurationIcon from '@/components/Icons/DurationIcon.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import AudioPlayer from '@/components/Activities/AudioPlayer.vue'
import CallLogDetailModal from '@/components/Modals/CallLogDetailModal.vue'
import { statusLabelMap, statusColorMap } from '@/utils/callLog.js'
import { formatDate, timeAgo } from '@/utils'
import { Avatar, Badge, Tooltip, createResource } from 'frappe-ui'
import { reactive, ref } from 'vue'

const props = defineProps({
  activity: { type: Object, default: () => ({}) },
})

const call = reactive(props.activity)

const callLog = createResource({
  url: 'crm.fcrm.doctype.crm_call_log.crm_call_log.get_call_log',
  params: { name: call.name },
  cache: ['call_log', call.name],
  auto: true,
})
const showCallLogDetailModal = ref(false)
</script>
