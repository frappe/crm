<template>
  <FormsList v-if="screen === 'list'" ref="listRef" @open="openBuilder" />
  <FormBuilderPanel
    v-else
    :key="activeName"
    :name="activeName"
    @back="backToList"
    @saved="() => listRef?.reload?.()"
  />
</template>

<script setup>
import { ref, nextTick } from 'vue'
import FormsList from './FormsList.vue'
import FormBuilderPanel from './FormBuilderPanel.vue'

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
