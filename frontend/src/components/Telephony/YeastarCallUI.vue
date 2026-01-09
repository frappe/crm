<template>
  <div>
    <div
      v-show="showCallPopup"
      class="ml-2 flex cursor-pointer select-none items-center justify-between gap-1 rounded-full bg-surface-gray-7 px-2 py-[7px] text-base text-ink-gray-2"
    >
      
    </div>
  </div>
</template>
<script setup>
import { createResource } from 'frappe-ui'
import { ref } from 'vue'

const showCallPopup = ref(true)

function makeOutgoingCall(number) {
  console.log('Initiating Yeastar call to:', number)
  createResource({
    url: 'crm.integrations.yeastar.api.make_call',
    params: { callee: number },
    auto: true,
    onSuccess(response) {
      console.log('Call initiated successfully:', response)
    },
    onError(error) {
      console.error('Error initiating call:', error)
    },
  })
}

defineExpose({ makeOutgoingCall })
</script>
