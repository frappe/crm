<template>
  <FieldLayoutDialog
    v-for="dialog in fieldLayoutDialogs"
    :key="dialog.key"
    v-bind="dialogProps(dialog)"
    @resolve="dialog.props.onResolve"
  />
</template>

<script setup>
import FieldLayoutDialog from '@/components/Modals/FieldLayoutDialog.vue'
import { fieldLayoutDialogs } from '@/utils/renderFieldLayoutDialog'

function dialogProps(dialog) {
  // Extract onResolve so it's only attached via @resolve, not doubled via v-bind
  const { onResolve, ...rest } = dialog.props
  return rest
}
</script>
