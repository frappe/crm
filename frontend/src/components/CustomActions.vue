<template>
  <Button
    v-if="normalActions.length && !isMobileView"
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
  <div
    v-if="groupedWithLabelActions.length && !isMobileView"
    v-for="g in groupedWithLabelActions"
    :key="g.label"
  >
    <Dropdown :options="g.action" v-slot="{ open }">
      <Button :label="g.label">
        <template #suffix>
          <FeatherIcon
            :name="open ? 'chevron-up' : 'chevron-down'"
            class="h-4"
          />
        </template>
      </Button>
    </Dropdown>
  </div>
</template>

<script setup>
import { computed, h } from 'vue'
import { Dropdown } from 'frappe-ui'
import { isMobileView } from '@/composables/settings'

const props = defineProps({
  actions: {
    type: Object,
    required: true,
  },
})

const normalActions = computed(() => {
  return props.actions.filter((action) => !action.group)
})

const groupedWithLabelActions = computed(() => {
  let _actions = []

  props.actions
    .filter((action) => action.buttonLabel && action.group)
    .forEach((action) => {
      let groupIndex = _actions.findIndex((a) => a.label === action.buttonLabel)
      if (groupIndex > -1) {
        _actions[groupIndex].action.push(action)
      } else {
        _actions.push({
          label: action.buttonLabel,
          action: [action],
        })
      }
    })
  return _actions
})

const groupedActions = computed(() => {
  let _actions = []
  let _normalActions = normalActions.value
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
  if (isMobileView.value && groupedWithLabelActions.value.length) {
    groupedWithLabelActions.value.map((group) => {
      group.action.forEach((action) => _actions.push(action))
    })
  }
  _actions = _actions.concat(
    props.actions.filter((action) => action.group && !action.buttonLabel)
  )
  return _actions
})
</script>
