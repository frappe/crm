<template>
  <div
    v-if="avatars?.length"
    class="mr-1.5 flex cursor-pointer items-center"
    :class="[avatars?.length > 1 ? 'flex-row-reverse' : 'truncate [&>div]:truncate']"
  >
    <Tooltip
      v-if="avatars?.length == 1"
      :text="avatars[0].name"
      class="flex items-center gap-2 text-base"
    >
      <Avatar
        shape="circle"
        :image="avatars[0].image"
        :label="avatars[0].label"
        size="sm"
      />
      <div class="truncate">{{ avatars[0].label }}</div>
    </Tooltip>
    <Tooltip
      v-else
      :text="avatar.name"
      v-for="avatar in reverseAvatars"
      :key="avatar.name"
    >
      <Avatar
        class="-mr-1.5 transform ring-2 ring-white transition hover:z-10 hover:scale-110"
        shape="circle"
        :image="avatar.image"
        :label="avatar.label"
        :size="size"
      />
    </Tooltip>
  </div>
</template>
<script setup>
import { Avatar, Tooltip } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  avatars: {
    type: Array,
    default: [],
  },
  size: {
    type: String,
    default: 'md',
  },
})
const reverseAvatars = computed(() => props.avatars.reverse())
</script>
