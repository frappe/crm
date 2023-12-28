<template>
  <Button
    v-for="action in actions"
    :label="action.label"
    @click="action.onClick()"
  />
</template>

<script setup>
const props = defineProps({
  actions: {
    type: Object,
    required: true,
  },
})
</script>
