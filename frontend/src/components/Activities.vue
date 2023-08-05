<template>
  <div class="p-5 flex items-center justify-between font-medium text-lg">
    <div>{{ title }}</div>
  </div>
  <div>
    <div v-for="(activity, i) in activities">
      <div class="grid grid-cols-[30px_minmax(auto,_1fr)] gap-4 px-5">
        <div
          class="relative flex justify-center"
          :class="{
            'after:absolute after:border-l after:border-gray-300 after:top-0 after:left-[50%] after:h-full after:-z-10':
              i != activities.length - 1,
          }"
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
                <Button variant="ghost" icon="more-horizontal" class="text-gray-600" />
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
</template>
<script setup>
import { Button, FeatherIcon, Tooltip } from 'frappe-ui'
import { timeAgo, dateFormat, dateTooltipFormat } from '@/utils'
import { usersStore } from '@/stores/users'
import { computed } from 'vue'
import UserAvatar from './UserAvatar.vue'

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

const activities = computed(() => {
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
