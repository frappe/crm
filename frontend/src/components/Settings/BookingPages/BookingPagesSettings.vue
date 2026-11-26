<template>
  <BookingPagesList v-if="!activeName" ref="listRef" @open="open" />
  <BookingPageEditor v-else :key="activeName" :name="activeName" @back="back" />
</template>

<script setup lang="ts">
import { nextTick, ref } from 'vue'
import BookingPagesList from './BookingPagesList.vue'
import BookingPageEditor from './BookingPageEditor.vue'

const activeName = ref<string | null>(null)
const listRef = ref<InstanceType<typeof BookingPagesList> | null>(null)

function open(name: string) {
  activeName.value = name
}

async function back() {
  activeName.value = null
  await nextTick()
  listRef.value?.reload()
}
</script>
