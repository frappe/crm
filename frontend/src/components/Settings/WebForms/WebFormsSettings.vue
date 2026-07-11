<template>
  <WebFormsList v-if="screen === 'list'" ref="listRef" @open="openBuilder" />
  <WebFormBuilderPanel
    v-else
    :key="activeName"
    :name="activeName"
    @back="backToList"
    @saved="() => listRef?.reload?.()"
  />
</template>

<script setup>
import { ref, nextTick } from 'vue'
import WebFormsList from './WebFormsList.vue'
import WebFormBuilderPanel from './WebFormBuilderPanel.vue'

const screen = ref('list')
const activeName = ref(null)
const listRef = ref(null)

function openBuilder(name) {
  activeName.value = name
  screen.value = 'builder'
}
async function backToList() {
  screen.value = 'list'
  await nextTick()
  listRef.value?.reload?.()
}
</script>
