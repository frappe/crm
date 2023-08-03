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
          >
            <FeatherIcon
              :name="timelineIcon(activity.activity_type)"
              class="w-3.5 h-3.5 text-gray-600"
            />
          </div>
        </div>
        <div class="flex flex-col gap-3 pb-6">
          <div
            class="flex items-start justify-stretch gap-2 text-base leading-6"
          >
            <Avatar
              :image="getUser(activity.owner).user_image"
              :label="getUser(activity.owner).full_name"
              size="md"
            />

            <div class="flex items-center gap-1">
              <div>{{ getUser(activity.owner).full_name }}</div>
              <div
                v-if="activity.activity_type == 'creation'"
                class="text-gray-600"
              >
                {{ activity.data }}
              </div>
              <div
                v-else-if="activity.activity_type == 'added'"
                class="inline-flex gap-1 text-gray-600"
              >
                <span>added</span>
                <span class="text-gray-900 truncate max-w-xs">
                  {{ activity.data.field }}
                </span>
                <span>value as</span>
                <span class="text-gray-900 truncate max-w-xs">
                  {{ activity.data.value }}
                </span>
              </div>
              <div
                v-else-if="activity.activity_type == 'removed'"
                class="inline-flex gap-1 text-gray-600"
              >
                <span>removed</span>
                <span class="text-gray-900 truncate max-w-xs">
                  {{ activity.data.field }}
                </span>
                <span>value</span>
                <span class="text-gray-900 truncate max-w-xs">
                  {{ activity.data.value }}
                </span>
              </div>
              <div
                v-else-if="activity.activity_type == 'changed'"
                class="inline-flex gap-1 text-gray-600"
              >
                <span>changed</span>
                <span class="text-gray-900 truncate max-w-xs">
                  {{ activity.data.field }}
                </span>
                <span>value from</span>
                <span class="text-gray-900 truncate max-w-xs">
                  {{ activity.data.old_value }}
                </span>
                <span>to</span>
                <span class="text-gray-900 truncate max-w-xs">
                  {{ activity.data.value }}
                </span>
              </div>
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
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { Avatar, FeatherIcon, Tooltip, Button } from 'frappe-ui'
import { timeAgo, dateFormat, dateTooltipFormat } from '@/utils'
import { usersStore } from '@/stores/users'

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

function timelineIcon(activity_type) {
  if (activity_type == 'creation') {
    return 'plus'
  } else if (activity_type == 'removed') {
    return 'trash-2'
  }
  return 'edit'
}
</script>
