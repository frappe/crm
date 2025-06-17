<template>
  <Dialog v-model="show" :options="{ title: __('Change Password') }">
    <template #body-content>
      <Password
        v-model="newPassword"
        :label="__('New Password')"
        class="mb-4"
      />
      <Password v-model="confirmPassword" :label="__('Confirm Password')" />
    </template>
    <template #actions>
      <div class="flex justify-between items-center">
        <div>
          <ErrorMessage :message="error" />
        </div>
        <Button
          variant="solid"
          :label="__('Update')"
          :disabled="
            !newPassword || !confirmPassword || newPassword !== confirmPassword
          "
          :loading="updatePassword.loading"
          @click="updatePassword.submit()"
        />
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import Password from '@/components/Controls/Password.vue'
import { usersStore } from '@/stores/users'
import { Dialog, toast, createResource } from 'frappe-ui'
import { useOnboarding } from 'frappe-ui/frappe'
import { ref } from 'vue'

const show = defineModel()

const { getUser } = usersStore()
const { updateOnboardingStep } = useOnboarding('frappecrm')

const newPassword = ref('')
const confirmPassword = ref('')

const error = ref('')

const updatePassword = createResource({
  url: 'frappe.client.set_value',
  makeParams() {
    return {
      doctype: 'User',
      name: getUser().name,
      fieldname: 'new_password',
      value: newPassword.value,
    }
  },
  onSuccess: () => {
    updateOnboardingStep('setup_your_password')
    toast.success(__('Password updated successfully'))
    show.value = false
    newPassword.value = ''
    confirmPassword.value = ''
    error.value = ''
  },
  onError: (err) => {
    error.value = err.messages[0] || __('Failed to update password')
  },
})
</script>
