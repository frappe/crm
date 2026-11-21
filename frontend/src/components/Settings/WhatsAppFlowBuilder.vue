<template>
  <FlowBuilder
    :controller="builder"
    :chrome="chrome"
    @close="emit('close')"
    @copied="(name) => emit('copied', name)"
  />
</template>

<script setup>
import { flowPermissions } from '@/composables/whatsapp'
import { FlowBuilder, useFlowBuilder } from '@whatsapp/ui'

const props = defineProps({
  name: { type: String, required: true },
  chrome: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['close', 'copied'])

const builder = useFlowBuilder({
  name: props.name,
  canWrite: flowPermissions.write,
})
</script>
