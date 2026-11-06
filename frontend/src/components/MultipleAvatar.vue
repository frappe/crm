<template>
  <div
    v-if="avatars?.length"
    class="mr-1.5 flex cursor-pointer items-center"
    :class="[
      avatars?.length > 1 ? 'flex-row-reverse' : 'truncate [&>div]:truncate',
    ]"
  >
    <Tooltip v-if="avatars?.length == 1" :text="avatars[0].name">
      <div class="flex items-center gap-2 text-base">
        <span class="relative inline-flex shrink-0">
          <Avatar
            shape="circle"
            :image="avatars[0].image"
            :label="avatars[0].label"
            :size="size"
          />
          <AvailabilityDot
            v-if="!hideStatus"
            :user="avatars[0].name"
            class="absolute bottom-0 right-0 ring-2 ring-[--surface-base]"
          />
        </span>
        <div class="truncate" :class="labelClass">{{ avatars[0].label }}</div>
      </div>
    </Tooltip>
    <Tooltip
      v-for="avatar in reverseAvatars"
      v-else
      :key="avatar.name"
      :text="avatar.name"
    >
      <span
        class="user-avatar relative -mr-1.5 inline-flex transform transition hover:z-10 hover:scale-110"
        :data-name="avatar.name"
      >
        <Avatar
          class="ring-2 ring-outline-base"
          shape="circle"
          :image="avatar.image"
          :label="avatar.label"
          :size="size"
        />
        <AvailabilityDot
          v-if="!hideStatus"
          :user="avatar.name"
          class="absolute bottom-0 right-0 ring-2 ring-[--surface-base]"
        />
      </span>
    </Tooltip>
  </div>
</template>
<script setup>
import AvailabilityDot from '@/components/AvailabilityDot.vue'
import { Avatar, Tooltip } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  avatars: { type: Array, default: () => [] },
  size: { type: String, default: 'md' },
  labelClass: { type: String, default: '' },
  hideStatus: { type: Boolean, default: false },
})
const reverseAvatars = computed(() => [...props.avatars].reverse())
</script>
