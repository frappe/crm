<template>
  <todo-app></todo-app>
</template>

<script setup>

import {onMounted, ref} from 'vue'

const loading = ref(true)

onMounted(async () => {
  try {
    const moduleUrl = `${window.location.origin}/assets/cn_todo_manager/todoapp/index.js`
    await import(moduleUrl)

    loading.value = false
  } catch (err) {
    console.error({err})
    loading.value = false
  }
})

</script>
