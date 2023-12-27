<template>
  <div v-if="avatars?.length" class="mr-1.5 flex flex-row-reverse items-center cursor-pointer">
    <Tooltip :text="avatar.name" v-for="avatar in reverseAvatars" :key="avatar.name">
      <Avatar
        class="-mr-1.5 transform border-2 border-white transition hover:z-10 hover:scale-125"
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
import { computed, defineModel } from 'vue'

const avatars = defineModel()
const reverseAvatars = computed(() => avatars.value.reverse())
</script>
