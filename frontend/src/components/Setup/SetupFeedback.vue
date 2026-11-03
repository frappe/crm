<template>
  <Dialog
    v-model:open="open"
    size="md"
    :title="__('You\'re all set')"
    :message="__('Before you dive in, tell us how setup went.')"
  >
    <template #default>
      <div class="flex flex-col gap-5">
        <div class="flex items-center justify-center gap-3">
          <span class="text-sm text-ink-gray-5">{{ __('Difficult') }}</span>
          <Rating v-model="rating" size="lg" :aria-label="__('Setup rating')" />
          <span class="text-sm text-ink-gray-5">{{ __('Easy') }}</span>
        </div>
        <FormControl
          v-model="comment"
          type="textarea"
          :rows="3"
          :label="__('Anything we could do better? (optional)')"
          :placeholder="__('Share what was confusing or missing')"
        />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button variant="ghost" :label="__('Not now')" @click="open = false" />
        <Button
          variant="solid"
          :label="__('Send feedback')"
          :disabled="!rating"
          @click="submit"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { setupFeedback } from '@/composables/modals'
import { Button, Dialog, FormControl, Rating } from 'frappe-ui'
import { useTelemetry } from '@framework/ui/telemetry'
import { computed, ref } from 'vue'

const { capture } = useTelemetry()

const rating = ref(0)
const comment = ref('')

const open = computed({
  get: () => Boolean(setupFeedback.value),
  set: (value) => !value && (setupFeedback.value = null),
})

function submit() {
  if (!rating.value) return
  capture('onboarding_feedback', {
    ...setupFeedback.value,
    rating: rating.value,
    comment: comment.value.trim() || null,
  })
  open.value = false
}
</script>
