<template>
  <Button
    v-for="action in normalActions"
    :label="action.label"
    @click="action.onClick()"
  >
    <template v-if="action.icon" #prefix>
      <FeatherIcon :name="action.icon" class="h-4 w-4" />
    </template>
  </Button>
  <Dropdown v-if="groupedActions.length" :options="groupedActions">
    <Button>
      <template #icon>
        <FeatherIcon name="more-horizontal" class="h-4 w-4" />
      </template>
    </Button>
  </Dropdown>
</template>

<script setup>
import { computed } from 'vue'
import { Dropdown } from 'frappe-ui'

const props = defineProps({
  actions: {
    type: Object,
    required: true,
  },
})

const groupedActions = computed(() => {
  return props.actions.filter((action) => action.group)
})

const normalActions = computed(() => {
  return props.actions.filter((action) => !action.group)
})
</script>
