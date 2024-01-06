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
  const _actions = props.actions.filter((action) => action.group)
  const groupedActions = {}

  for (const action of _actions) {
    if (!groupedActions[action.group]) {
      groupedActions[action.group] = []
    }

    groupedActions[action.group].push(action)
  }

  let _groupedActions = [
    ...Object.keys(groupedActions).map((group) => ({
      group,
      items: groupedActions[group],
    })),
  ]
  return _groupedActions
})

const normalActions = computed(() => {
  return props.actions.filter((action) => !action.group)
})
</script>
