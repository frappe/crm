<template>
  <div v-if="flows">
    <FlowList
      :controller="flows"
      :can-write="canWrite"
      :chrome="chrome"
      hide-header
      @new="creating = true"
      @open="(name) => (openFlow = name)"
    />
    <NewFlowDialog
      v-if="canWrite"
      v-model:open="creating"
      :controller="flows"
      :account="account"
      :chrome="chrome"
      @created="(name) => (openFlow = name)"
    />
    <WhatsAppFlowBuilderDialog
      v-model:flow="openFlow"
      @changed="flows.load()"
    />
  </div>
</template>

<script setup>
import { flowPermissions } from '@/composables/whatsapp'
import { FlowList, NewFlowDialog, useFlowList } from '@whatsapp/ui'
import { createResource } from 'frappe-ui'
import { computed, ref, shallowRef } from 'vue'
import WhatsAppFlowBuilderDialog from './WhatsAppFlowBuilderDialog.vue'
import { flowBuilderChrome } from './whatsappFlowBuilderChrome'

const chrome = flowBuilderChrome()
// WA Settings' default account: its business's Flows are listed, synced and created in.
const account = ref('')
const flows = shallowRef(null)
const creating = ref(false)
const openFlow = ref('')

const canWrite = computed(() => flowPermissions.write && Boolean(account.value))

createResource({
  url: 'frappe.client.get_single_value',
  params: { doctype: 'WA Settings', field: 'default_account' },
  auto: true,
  onSuccess: (defaultAccount) => start(defaultAccount),
  onError: () => start(''),
})

function start(defaultAccount) {
  account.value = defaultAccount || ''
  flows.value = useFlowList({ account: account.value || undefined })
}

defineExpose({
  canWrite,
  newFlow: () => (creating.value = true),
  sync: () => flows.value?.sync(),
  syncing: computed(() => Boolean(flows.value?.syncing)),
})
</script>
