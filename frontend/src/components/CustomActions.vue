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
    <Button icon="more-horizontal" />
  </Dropdown>
</template>

<script setup>
import { computed, h } from 'vue'
import { Dropdown } from 'frappe-ui'
import { isMobileView } from '@/stores/settings'

const props = defineProps({
  actions: {
    type: Object,
    required: true,
  },
})

const groupedActions = computed(() => {
  let _actions = []
  let _normalActions = props.actions.filter((action) => !action.group)
  if (isMobileView.value && _normalActions.length) {
    _actions.push({
      group: __('Actions'),
      hideLabel: true,
      items: _normalActions.map((action) => ({
        label: action.label,
        onClick: action.onClick,
        icon: action.icon,
      })),
    })
  }
  _actions = _actions.concat(
    props.actions.filter((action) => action.group)
  )
  return _actions
})

const normalActions = computed(() => {
  let _actions = props.actions.filter((action) => !action.group)
  if (isMobileView.value && _actions.length) {
    return []
  }
  return _actions
})
</script>
