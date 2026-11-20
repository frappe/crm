<template>
  <form class="flex flex-col" @submit.prevent="savePassword">
    <h1 class="text-2xl-semibold text-ink-gray-9">
      {{ __('Set your password') }}
    </h1>
    <p class="mt-2 text-p-base text-ink-gray-6">
      {{ __('You will use it with {0} to sign in to the CRM.', [email]) }}
    </p>

    <div class="mt-8 flex flex-col gap-3">
      <Password
        v-model="password"
        :placeholder="__('Password')"
        :label="__('Password')"
      />
      <Password
        v-model="confirmPassword"
        :placeholder="__('Confirm password')"
        :label="__('Confirm password')"
      />
      <ErrorMessage v-if="message" :message="message" />
    </div>

    <div class="mt-auto pt-8">
      <Button
        type="submit"
        class="w-full"
        variant="solid"
        :label="__('Continue')"
        :loading="saving"
        :disabled="!canSave"
      />
    </div>
  </form>
</template>

<script setup>
import { sessionStore } from '@/stores/session'
import { Button, ErrorMessage, Password, call } from 'frappe-ui'
import { computed, inject, ref, watch } from 'vue'

const emit = defineEmits(['done', 'skip'])

const { user: email } = sessionStore()

const password = ref('')
const confirmPassword = ref('')
const saving = ref(false)
const error = ref('')

const preview = inject('setupPreview', null)
watch(password, (value) => preview && (preview.passwordLength = value.length))

const mismatch = computed(
  () =>
    Boolean(confirmPassword.value) && password.value !== confirmPassword.value,
)
const message = computed(() =>
  mismatch.value ? __('Passwords do not match') : error.value,
)
const canSave = computed(
  () => Boolean(password.value) && password.value === confirmPassword.value,
)

async function savePassword() {
  if (!canSave.value) return
  saving.value = true
  error.value = ''
  try {
    await call('crm.api.user.set_password', { new_password: password.value })
    window.needs_password_setup = false
    emit('done')
  } catch (e) {
    error.value = e.messages?.[0] || __('Could not set your password')
  } finally {
    saving.value = false
  }
}
</script>
