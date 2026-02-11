<template>
  <Dialog
    v-model="show"
    :options="{ title: __('Add existing user') }"
    @close="show = false"
  >
    <template #body-content>
      <div class="flex gap-1 border rounded mb-4 p-2 text-ink-gray-5">
        <FeatherIcon name="info" class="size-3.5 mt-0.5" />
        <p class="text-p-sm">
          {{
            __(
              'Add existing system users to this CRM. Assign them a role to grant access with their current credentials.',
            )
          }}
        </p>
      </div>

      <label class="block text-xs text-ink-gray-5 mb-1.5">
        {{ __('Users') }}
      </label>

      <div class="p-2 group bg-surface-gray-2 hover:bg-surface-gray-3 rounded">
        <EmailMultiSelect
          v-if="users?.data?.crmUsers?.length"
          class="flex-1"
          inputClass="!bg-surface-gray-2 hover:!bg-surface-gray-3 group-hover:!bg-surface-gray-3"
          :placeholder="__('john@doe.com')"
          v-model="newUsers"
          :validate="validateEmail"
          :fetchUsers="true"
          :existingEmails="[
            ...users.data.crmUsers.map((user) => user.name),
            'admin@example.com',
          ]"
          :error-message="
            (value) => __('{0} is an invalid email address', [value])
          "
          :emptyPlaceholder="__('No users found')"
        />
      </div>
      <FormControl
        type="select"
        class="mt-4"
        v-model="role"
        :label="__('Role')"
        :options="roleOptions"
        :description="description"
      />
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button
          variant="solid"
          :label="__('Add')"
          :disabled="!newUsers.length"
          @click="addNewUser.submit()"
          :loading="addNewUser.loading"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import EmailMultiSelect from '@/components/Controls/EmailMultiSelect.vue'
import { validateEmail } from '@/utils'
import { usersStore } from '@/stores/users'
import { createResource, toast } from 'frappe-ui'
import { ref, computed } from 'vue'

const { users, isAdmin, isManager } = usersStore()

const show = defineModel()

const newUsers = ref([])
const role = ref('Sales User')

const description = computed(() => {
  return {
    'System Manager':
      'Can manage all aspects of the CRM, including user management, customizations and settings.',
    'Sales Manager':
      'Can manage and invite new users, and create public & private views (reports).',
    'Sales User':
      'Can work with leads and deals and create private views (reports).',
  }[role.value]
})

const roleOptions = computed(() => {
  return [
    { value: 'Sales User', label: __('Sales user') },
    ...(isManager() ? [{ value: 'Sales Manager', label: __('Manager') }] : []),
    ...(isAdmin() ? [{ value: 'System Manager', label: __('Admin') }] : []),
  ]
})

const addNewUser = createResource({
  url: 'crm.api.user.add_existing_users',
  makeParams: () => ({
    users: JSON.stringify(newUsers.value),
    role: role.value,
  }),
  onSuccess: () => {
    toast.success(__('Users added successfully'))
    newUsers.value = []
    show.value = false
    users.reload()
  },
  onError: (error) => {
    toast.error(error.messages[0] || __('Failed to add users'))
  },
})
</script>
