<template>
  <Dialog v-model="show" :options="{ title: __('Change Password') }">
    <template #body-content>
      <div class="flex flex-col gap-4">
        <div>
          <Password
            v-model="currentPassword"
            :placeholder="__('Current Password')"
            maxLength="50"
          >
            <template #prefix>
              <LockKeyhole class="size-4 text-ink-gray-4" />
            </template>
          </Password>
        </div>
        <div>
          <Password
            v-model="newPassword"
            :placeholder="__('New Password')"
            maxLength="50"
          >
            <template #prefix>
              <LockKeyhole class="size-4 text-ink-gray-4" />
            </template>
          </Password>
        </div>
        <div>
          <Password
            v-model="confirmPassword"
            :placeholder="__('Confirm Password')"
            maxLength="50"
          >
            <template #prefix>
              <LockKeyhole class="size-4 text-ink-gray-4" />
            </template>
          </Password>
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-between items-center">
        <div>
          <p
            v-if="confirmPasswordMessage"
            class="text-sm text-ink-gray-5"
            :class="
              confirmPasswordMessage === __('Passwords match')
                ? 'text-ink-green-3'
                : 'text-ink-red-3'
            "
          >
            {{ confirmPasswordMessage }}
          </p>
        </div>

        <Button
          variant="solid"
          :label="__('Update')"
          :disabled="
            !currentPassword ||
            !newPassword ||
            !confirmPassword ||
            newPassword !== confirmPassword ||
            !isStrongPassword(newPassword)
          "
          :loading="updatePassword.loading"
          @click="updatePassword.submit()"
        />
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import LockKeyhole from '~icons/lucide/lock-keyhole'
import { Dialog, toast, createResource, Password } from 'frappe-ui'
import { useOnboarding } from 'frappe-ui/frappe'
import { ref, watch } from 'vue'

const show = defineModel({ type: Boolean })

const { updateOnboardingStep } = useOnboarding('frappecrm')

const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const confirmPasswordMessage = ref('')

const updatePassword = createResource({
  url: 'crm.api.user.change_password',
  makeParams() {
    return {
      old_password: currentPassword.value,
      new_password: newPassword.value,
    }
  },
  onSuccess: () => {
    updateOnboardingStep('setup_your_password')
    toast.success(__('Password updated successfully'))
    show.value = false
    currentPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
    confirmPasswordMessage.value = ''
  },
  onError: (err) => {
    toast.error(err.messages?.[0] || __('Failed to update password'))
  },
})

function isStrongPassword(password) {
  const regex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d\s]).{8,}$/
  return regex.test(password)
}

watch([currentPassword, newPassword, confirmPassword], () => {
  confirmPasswordMessage.value = ''

  if (
    currentPassword.value &&
    newPassword.value &&
    currentPassword.value === newPassword.value
  ) {
    confirmPasswordMessage.value = __(
      'New password cannot be the same as current password',
    )
    return
  }

  if (newPassword.value && newPassword.value.length < 8) {
    confirmPasswordMessage.value = __('Password must be at least 8 characters')
    return
  } else if (newPassword.value && !isStrongPassword(newPassword.value)) {
    confirmPasswordMessage.value = __(
      'Password must contain lowercase, uppercase, number, and symbol',
    )
    return
  }

  if (
    confirmPassword.value.length &&
    newPassword.value !== confirmPassword.value
  ) {
    confirmPasswordMessage.value = __('Passwords do not match')
  } else if (
    newPassword.value === confirmPassword.value &&
    newPassword.value.length &&
    confirmPassword.value.length
  ) {
    confirmPasswordMessage.value = __('Passwords match')
  }
})
</script>
