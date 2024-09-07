<template>
  <div class="flex h-full flex-col gap-8 p-8">
    <h2 class="flex gap-2 text-xl font-semibold leading-none h-5">
      {{ __('Send Invites To') }}
    </h2>
    <div class="flex-1 overflow-y-auto">
      <label class="block text-xs text-gray-600 mb-1.5">
        {{ __('Invite by email') }}
      </label>
      <MultiValueInput
        v-model="invitees"
        :validate="validateEmail"
        :error-message="
          (value) => __('{0} is an invalid email address', [value])
        "
      />
      <FormControl
        type="select"
        class="mt-4"
        v-model="role"
        variant="outline"
        :label="__('Invite as')"
        :options="[
          { label: __('Regular Access'), value: 'Sales User' },
          { label: __('Manager Access'), value: 'Sales Manager' },
        ]"
        :description="description"
      />
      <ErrorMessage class="mt-2" v-if="error" :message="error" />
      <template v-if="pendingInvitations.data?.length && !invitees.length">
        <div
          class="mt-6 flex items-center justify-between py-4 text-base font-semibold"
        >
          <div>{{ __('Pending Invites') }}</div>
        </div>
        <ul class="flex flex-col gap-1">
          <li
            class="flex items-center justify-between px-2 py-1 rounded-lg bg-gray-50"
            v-for="user in pendingInvitations.data"
            :key="user.name"
          >
            <div class="text-base">
              <span class="text-gray-900">
                {{ user.email }}
              </span>
              <span class="text-gray-600"> ({{ roleMap[user.role] }}) </span>
            </div>
            <div>
              <Tooltip text="Delete Invitation">
                <Button
                  icon="x"
                  variant="ghost"
                  :loading="
                    pendingInvitations.delete.loading &&
                    pendingInvitations.delete.params.name === user.name
                  "
                  @click="pendingInvitations.delete.submit(user.name)"
                />
              </Tooltip>
            </div>
          </li>
        </ul>
      </template>
    </div>
    <div class="flex flex-row-reverse">
      <Button
        :label="__('Send Invites')"
        variant="solid"
        @click="inviteByEmail.submit()"
        :loading="inviteByEmail.loading"
      />
    </div>
  </div>
</template>
<script setup>
import MultiValueInput from '@/components/Controls/MultiValueInput.vue'
import { validateEmail, convertArrayToString } from '@/utils'
import {
  createListResource,
  createResource,
  FormControl,
  Tooltip,
} from 'frappe-ui'
import { ref, computed } from 'vue'

const invitees = ref([])
const role = ref('Sales User')
const error = ref(null)

const description = computed(() => {
  return {
    'Sales Manager':
      'Can manage and invite new members, and create public & private views (reports).',
    'Sales User':
      'Can work with leads and deals and create private views (reports).',
  }[role.value]
})

const roleMap = {
  'Sales User': __('Regular Access'),
  'Sales Manager': __('Manager Access'),
}

const inviteByEmail = createResource({
  url: 'crm.api.invite_by_email',
  makeParams() {
    return {
      emails: convertArrayToString(invitees.value),
      role: role.value,
    }
  },
  onSuccess() {
    invitees.value = []
    role.value = 'Sales User'
    error.value = null
    pendingInvitations.reload()
  },
  onError(error) {
    error.value = error
  },
})

const pendingInvitations = createListResource({
  type: 'list',
  doctype: 'CRM Invitation',
  filters: { status: 'Pending' },
  fields: ['name', 'email', 'role'],
  auto: true,
})
</script>
