<template>
  <div class="flex flex-col">
    <h1 class="text-2xl-semibold text-ink-gray-9">
      {{ __('Set your password') }}
    </h1>
    <p class="mt-2 text-p-base text-ink-gray-6">
      {{
        __(
          'You are signed in, but have no password yet. Set one so you can sign in again from any device.',
        )
      }}
    </p>

    <PasswordStep
      class="mt-8"
      :labels="labels"
      @input="showLengthInPreview"
      @ready="showReadyInPreview"
      @done="savePassword"
    />
  </div>
</template>

<script setup>
import { PasswordStep } from '@framework/ui/components/SetupFlow'
import { inject } from 'vue'

const emit = defineEmits(['done', 'skip'])

const labels = {
  label: __('Password'),
  placeholder: __('Password'),
  hint: __(
    'At least 8 characters. Mixing in numbers and symbols makes it stronger.',
  ),
  show: __('Show password'),
  hide: __('Hide password'),
  save: __('Save and continue'),
  failed: __('Could not set your password'),
  confirmLabel: __('Confirm password'),
  confirmPlaceholder: __('Confirm password'),
  mismatch: __('Passwords do not match'),
  strength: __('Strength:'),
  levels: [__('Poor'), __('Poor'), __('Average'), __('Good'), __('Great')],
}

// The preview mirrors the password as dots; the step reports only its length.
const preview = inject('setupPreview', null)
function showLengthInPreview(length) {
  if (preview) preview.passwordLength = length
}
function showReadyInPreview(ready) {
  if (preview) preview.passwordReady = ready
}

function savePassword() {
  window.needs_password_setup = false
  emit('done')
}
</script>
