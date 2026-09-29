<template>
  <Dialog v-model:open="show" :title="__('Share your feedback')">
    <template #default>
      <div class="flex flex-col gap-4">
        <p class="text-p-sm text-ink-gray-6">
          {{
            __(
              'Tell us what you love or what we can improve — every bit helps.',
            )
          }}
        </p>
        <div class="flex items-center gap-1.5">
          <button
            v-for="n in 5"
            :key="n"
            type="button"
            class="lucide-star size-6 transition"
            :class="
              n <= rating
                ? 'text-ink-amber-3'
                : 'text-ink-gray-3 hover:text-ink-gray-5'
            "
            :aria-label="__('Rate {0} out of 5', [n])"
            @click="rating = n"
          />
        </div>
        <FormControl
          v-model="message"
          type="textarea"
          :rows="4"
          :placeholder="__('Your feedback...')"
        />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end">
        <Button
          variant="solid"
          :label="__('Send feedback')"
          :disabled="!message.trim() && !rating"
          @click="submitFeedback"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref } from 'vue'
import { Dialog, FormControl, toast } from 'frappe-ui'
import { useTelemetry } from 'frappe-ui/frappe'

const show = defineModel({ type: Boolean, default: false })

const { capture } = useTelemetry()

const rating = ref(0)
const message = ref('')

function submitFeedback() {
  capture('feedback_submitted', {
    rating: rating.value,
    message: message.value,
  })
  toast.success(__('Thanks for your feedback!'))
  rating.value = 0
  message.value = ''
  show.value = false
}
</script>
