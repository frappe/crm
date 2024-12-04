<template>
  <div>
    <div class="mb-1 flex items-center justify-stretch gap-2 py-1 text-base">
      <div class="inline-flex items-center flex-wrap gap-1 text-ink-gray-5">
        <Avatar
          :image="activity.caller.image"
          :label="activity.caller.label"
          size="md"
        />
        <span class="font-medium text-ink-gray-8 ml-1">
          {{ activity.caller.label }}
        </span>
        <span>{{
          activity.type == 'Incoming'
            ? __('has reached out')
            : __('has made a call')
        }}</span>
      </div>
      <div class="ml-auto whitespace-nowrap">
        <Tooltip :text="formatDate(activity.creation)">
          <div class="text-sm text-ink-gray-5">
            {{ __(timeAgo(activity.creation)) }}
          </div>
        </Tooltip>
      </div>
    </div>
    <div
      class="flex flex-col gap-2 border border-outline-gray-modals rounded-md bg-surface-cards px-3 py-2.5 text-ink-gray-9"
    >
      <div class="flex items-center justify-between">
        <div class="inline-flex gap-2 items-center text-base font-medium">
          <div>
            {{
              activity.type == 'Incoming'
                ? __('Inbound Call')
                : __('Outbound Call')
            }}
          </div>
        </div>
        <div>
          <MultipleAvatar
            :avatars="[
              {
                image: activity.caller.image,
                label: activity.caller.label,
                name: activity.caller.label,
              },
              {
                image: activity.receiver.image,
                label: activity.receiver.label,
                name: activity.receiver.label,
              },
            ]"
            size="sm"
          />
        </div>
      </div>
      <div class="flex items-center flex-wrap gap-2">
        <Badge :label="formatDate(activity.creation, 'MMM D, dddd')">
          <template #prefix>
            <CalendarIcon class="size-3" />
          </template>
        </Badge>
        <Badge v-if="activity.status == 'Completed'" :label="activity.duration">
          <template #prefix>
            <DurationIcon class="size-3" />
          </template>
        </Badge>
        <Badge
          v-if="activity.recording_url"
          :label="activity.show_recording ? __('Hide Recording') : __('Listen')"
          class="cursor-pointer"
          @click="activity.show_recording = !activity.show_recording"
        >
          <template #prefix>
            <PlayIcon class="size-3" />
          </template>
        </Badge>
        <Badge
          :label="statusLabelMap[activity.status]"
          :theme="statusColorMap[activity.status]"
        />
      </div>
      <div
        v-if="activity.show_recording && activity.recording_url"
        class="flex flex-col items-center justify-between"
      >
        <AudioPlayer :src="activity.recording_url" />
      </div>
    </div>
  </div>
</template>
<script setup>
import PlayIcon from '@/components/Icons/PlayIcon.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import DurationIcon from '@/components/Icons/DurationIcon.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import AudioPlayer from '@/components/Activities/AudioPlayer.vue'
import { statusLabelMap, statusColorMap } from '@/utils/callLog.js'
import { formatDate, timeAgo } from '@/utils'
import { Avatar, Badge, Tooltip } from 'frappe-ui'

const props = defineProps({
  activity: Object,
})
</script>
