<template>
  <div
    v-if="avatars?.length"
    class="mr-1.5 flex cursor-pointer flex-row-reverse items-center"
  >
    <Tooltip
      :text="avatar.name"
      v-for="avatar in reverseAvatars"
      :key="avatar.name"
    >
      <Avatar
        class="-mr-1.5 transform border-2 border-white transition hover:z-10 hover:scale-110"
        shape="circle"
        :image="avatar.image"
        :label="avatar.label"
        size="lg"
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
})
const reverseAvatars = computed(() => props.avatars.reverse())
</script>
