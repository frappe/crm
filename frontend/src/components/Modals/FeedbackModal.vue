<template>
  <Dialog v-model="show" :options="{ size: 'lg' }">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
            {{ __('Help & Feedback') }}
          </h3>
          <Button variant="ghost" class="w-7" icon="x" @click="show = false" />
        </div>
        <div class="flex flex-col gap-4">
          <FormControl
            v-model="feedbackType"
            type="select"
            :label="__('I want to...')"
            :options="feedbackTypeOptions"
          />
          <FormControl
            v-model="subject"
            type="text"
            :label="__('Subject')"
            :placeholder="__('Brief summary of your message')"
            required
          />
          <FormControl
            v-model="message"
            type="textarea"
            :label="__('Message')"
            :placeholder="__('Tell us more...')"
            :rows="5"
            required
          />
          <div>
            <FormControl
              v-model="email"
              type="email"
              :label="__('Email (optional)')"
              :placeholder="__('you@example.com')"
            />
            <p class="mt-1 text-p-sm text-ink-gray-5">
              {{ __('So we can follow up with you') }}
            </p>
          </div>
          <ErrorMessage v-if="error" :message="error" />
        </div>
      </div>
      <div class="flex items-center justify-end gap-2 border-t px-4 py-4 sm:px-6">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          variant="solid"
          :label="__('Submit')"
          :loading="submitFeedback.loading"
          @click="handleSubmit"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref } from 'vue'
import { createResource, toast } from 'frappe-ui'
import { useTelemetry } from 'frappe-ui/frappe'
import { validateEmail } from '@/utils'

const show = defineModel({ type: Boolean })

const { capture } = useTelemetry()

const feedbackType = ref('Feedback')
const subject = ref('')
const message = ref('')
const email = ref('')
const error = ref('')

const feedbackTypeOptions = [
  { label: __('Share Feedback'), value: 'Feedback' },
  { label: __('Ask a Question'), value: 'Question' },
  { label: __('Report a Bug'), value: 'Bug Report' },
  { label: __('Request a Feature'), value: 'Feature Request' },
]

const submitFeedback = createResource({
  url: 'crm.api.feedback.submit_feedback',
  onSuccess() {
    capture('feedback_submitted', { type: feedbackType.value })
    toast.success(__('Your feedback has been submitted. Thank you!'))
    resetForm()
    show.value = false
  },
  onError(err) {
    error.value = err.messages?.[0] || err.message || __('An error occurred. Please try again.')
  },
})

function handleSubmit() {
  error.value = ''

  if (!subject.value.trim()) {
    error.value = __('Subject is required')
    return
  }
  if (!message.value.trim()) {
    error.value = __('Message is required')
    return
  }
  if (email.value && !validateEmail(email.value)) {
    error.value = __('Please enter a valid email address')
    return
  }

  submitFeedback.submit({
    subject: subject.value,
    feedback_type: feedbackType.value,
    message: message.value,
    email: email.value || null,
  })
}

function resetForm() {
  feedbackType.value = 'Feedback'
  subject.value = ''
  message.value = ''
  email.value = ''
  error.value = ''
}
</script>
