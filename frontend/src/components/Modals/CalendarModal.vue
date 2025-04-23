<template>
  <Dialog v-model="show" :options="{ size: '2xl' }">
    <template #body> Hello </template>
  </Dialog>
</template>

<script setup>
import { ref, nextTick, watch, computed } from 'vue'

const show = defineModel()
const event = defineModel('event')

const loading = ref(false)
const error = ref(null)
const title = ref(null)
const editMode = ref(false)

let _event = ref({})

watch(
  () => show.value,
  (value) => {
    if (!value) return
    editMode.value = false
    nextTick(() => {
      title.value.el.focus()
      _event.value = { ...event.value }

      if (_event.value.name) {
        editMode.value = true
      }
    })
  },
)
</script>
