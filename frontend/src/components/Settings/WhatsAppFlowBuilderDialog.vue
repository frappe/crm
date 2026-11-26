<template>
  <!-- Over the settings dialog, as the automation builder is. The builder closes itself
       from its back breadcrumb or Escape, after saving what is pending. -->
  <Dialog
    :open="Boolean(flow)"
    size="6xl"
    bare
    :dismissible="false"
    @update:open="(open) => !open && close()"
  >
    <template #default>
      <div class="h-[calc(100vh_-_6rem)]">
        <WhatsAppFlowBuilder
          v-if="flow"
          :key="flow"
          :name="flow"
          :chrome="chrome"
          @close="close"
          @copied="openCopy"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { disableSettingModalOutsideClick } from '@/composables/settings'
import { Dialog } from 'frappe-ui'
import { onUnmounted, watch } from 'vue'
import WhatsAppFlowBuilder from './WhatsAppFlowBuilder.vue'
import { flowBuilderChrome } from './whatsappFlowBuilderChrome'

const props = defineProps({
  // Names where the back breadcrumb returns to; the Flows list by default.
  backLabel: { type: String, default: '' },
})
const flow = defineModel('flow', { type: String, default: '' })
// After a close or a copy, for the host to reload what lists Flows.
const emit = defineEmits(['changed'])

const chrome = {
  ...flowBuilderChrome(),
  ...(props.backLabel && { flowsCrumb: props.backLabel }),
}

watch(flow, (name) => (disableSettingModalOutsideClick.value = Boolean(name)))
onUnmounted(() => (disableSettingModalOutsideClick.value = false))

function close() {
  flow.value = ''
  emit('changed')
}

function openCopy(name) {
  flow.value = name
  emit('changed')
}
</script>
