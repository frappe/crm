<template>
  <ListView
    class="px-5"
    v-if="rows"
    :columns="columns"
    :rows="rows"
    row-key="name"
  />
</template>
<script setup>
import { ListView } from 'frappe-ui'

const props = defineProps({
  rows: {
    type: Array,
    required: true,
  },
  columns: {
    type: Array,
    required: true,
  },
})
</script>
