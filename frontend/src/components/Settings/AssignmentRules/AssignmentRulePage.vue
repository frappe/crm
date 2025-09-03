<template>
  <AssignmentRules v-if="step.screen === 'list'" />
  <AssignmentRuleView v-else-if="step.screen === 'view'" />
</template>

<script setup>
import { ref, provide } from 'vue'
import AssignmentRules from './AssignmentRules.vue'
import AssignmentRuleView from './AssignmentRuleView.vue'

const step = ref({ screen: 'list', data: null })

provide('step', step)
provide('updateStep', updateStep)

function updateStep(newStep, data) {
  step.value = { screen: newStep, data }
}
</script>
