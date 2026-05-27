<template>
  <Dialog
    v-model="show"
    :options="{
      title: __('Merge with another lead'),
      size: 'md',
    }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <p class="text-base text-ink-gray-7">
          {{
            __(
              'All activities of the selected lead will be moved to this lead.',
            )
          }}
        </p>

        <div class="flex flex-col gap-1.5">
          <span class="text-sm text-ink-gray-5">{{ __('Lead') }}</span>
          <Link
            v-model="selectedLead"
            doctype="CRM Lead"
            :filters="mergeLeadFilters"
            :placeholder="__('Select Lead')"
          />
        </div>

        <div
          class="flex items-center gap-2.5 rounded-lg border border-outline-gray-2 px-3.5 py-3"
        >
          <LucideAlertTriangle class="h-4 w-4 shrink-0 text-yellow-600" />
          <span class="text-sm text-ink-gray-7">
            {{ __('This merge can be undone later from the merge history.') }}
          </span>
        </div>

        <ErrorMessage v-if="error" :message="error" />
      </div>
    </template>

    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        size="md"
        :label="__('Merge Lead')"
        :loading="isMerging"
        :disabled="!selectedLead"
        @click="performMerge"
      />
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Dialog, Button, ErrorMessage, call, toast } from 'frappe-ui'
import Link from '@/components/Controls/Link.vue'
import LucideAlertTriangle from '~icons/lucide/alert-triangle'

const props = defineProps({
  leadId: { type: String, required: true },
})

const emit = defineEmits(['merged'])
const show = defineModel({ type: Boolean })
const router = useRouter()

const selectedLead = ref('')
const isMerging = ref(false)
const error = ref(null)

const mergeLeadFilters = computed(() => [
  ['is_duplicate', '=', 0],
  ['name', '!=', props.leadId],
])

async function performMerge() {
  isMerging.value = true
  error.value = null
  try {
    const result = await call('crm.api.lead.merge_leads', {
      target: props.leadId,
      source: selectedLead.value,
    })
    show.value = false
    emit('merged', result.target)
    toast.success(__('Lead merged successfully'), {
      action: {
        label: __('View'),
        onClick: () =>
          router.push({ name: 'Lead', params: { leadId: result.target } }),
      },
    })
    router.push({ name: 'Leads' })
  } catch (err) {
    error.value =
      err.messages?.[0] || err.message || __('Failed to merge leads')
  } finally {
    isMerging.value = false
  }
}
</script>
