<template>
  <div v-if="hasData" class="flex items-center gap-3 p-4 border border-outline-gray-1 rounded-xl mb-6">
    <WalletIcon class="w-5 h-5" :class="balance.remaining > 0 ? 'text-ink-gray-5' : 'text-ink-red-5'" />
    <div class="flex-1">
      <div class="text-p-sm text-ink-gray-5">{{ __('Active Abonement') }}</div>
      <div class="text-p-base font-medium" :class="balance.remaining > 0 ? 'text-ink-gray-8' : 'text-ink-red-5'">
        {{ balance.remaining }} / {{ balance.total || '?' }} {{ __('classes remaining') }}
      </div>
    </div>
    <div class="text-right">
      <div class="text-p-xs text-ink-gray-5">{{ __('Type') }}: {{ balance.abonement_type || '-' }}</div>
      <div class="text-p-xs text-ink-gray-5">{{ __('Valid until') }}: {{ balance.end_date || '-' }}</div>
    </div>
  </div>
</template>

<script setup>
import WalletIcon from '~icons/lucide/wallet'
import { call } from 'frappe-ui'
import { ref, onMounted, computed } from 'vue'

const props = defineProps({
  student: { type: String, required: true },
})

const balance = ref(null)
const hasData = computed(() => balance.value && balance.value.available)
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    balance.value = await call('crm.api.abonement.check_abonement_balance', { student: props.student })
  } catch (e) {
    balance.value = null
  } finally {
    loading.value = false
  }
})
</script>
