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
<<<<<<< HEAD
        <Avatar
          shape="circle"
          :image="avatars[0].image"
          :label="avatars[0].label"
          :size="size"
        />
=======
        <span class="relative inline-flex shrink-0">
          <Avatar
            shape="circle"
            :image="avatars[0].image"
            :label="avatars[0].label"
            :size="size"
          />
          <AvailabilityDot
            :user="avatars[0].name"
            class="absolute bottom-0 right-0 ring-2 ring-[--surface-base]"
          />
        </span>
>>>>>>> 19fa04a (fix: keep the availability dot inside the avatar so list cells don't clip it)
        <div class="truncate" :class="labelClass">{{ avatars[0].label }}</div>
      </div>
    </Tooltip>
    <Tooltip
      v-for="avatar in reverseAvatars"
      v-else
      :key="avatar.name"
      :text="avatar.name"
    >
      <Avatar
        class="user-avatar -mr-1.5 transform ring-2 ring-outline-base transition hover:z-10 hover:scale-110"
        shape="circle"
        :image="avatar.image"
        :label="avatar.label"
        :size="size"
        :data-name="avatar.name"
<<<<<<< HEAD
      />
=======
      >
        <Avatar
          class="ring-2 ring-outline-base"
          shape="circle"
          :image="avatar.image"
          :label="avatar.label"
          :size="size"
        />
        <AvailabilityDot
          :user="avatar.name"
          class="absolute bottom-0 right-0 ring-2 ring-[--surface-base]"
        />
      </span>
>>>>>>> 19fa04a (fix: keep the availability dot inside the avatar so list cells don't clip it)
    </Tooltip>
  </div>
</template>
<script setup>
import { Avatar, Tooltip } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  avatars: { type: Array, default: () => [] },
  size: { type: String, default: 'md' },
  labelClass: { type: String, default: '' },
})
const reverseAvatars = computed(() => [...props.avatars].reverse())
</script>
