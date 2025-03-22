<template>
  <div class="flex h-full flex-col gap-8 p-8 text-ink-gray-9">
    <h2 class="flex gap-2 text-xl font-semibold leading-none h-5">
      {{ __('Send Invites To') }}
    </h2>
    <div class="flex-1 flex flex-col gap-8 overflow-y-auto">
      <div>
        <label class="block text-xs text-ink-gray-5 mb-1.5">
          {{ __('Invite by email') }}
        </label>
        <div
          class="p-2 group bg-surface-gray-2 hover:bg-surface-gray-3 rounded"
        >
          <MultiSelectEmailInput
            class="flex-1"
            inputClass="!bg-surface-gray-2 hover:!bg-surface-gray-3 group-hover:!bg-surface-gray-3"
            :placeholder="__('john@doe.com')"
            v-model="invitees"
            :validate="validateEmail"
            :error-message="
              (value) => __('{0} is an invalid email address', [value])
            "
          />
        </div>
        <FormControl
          type="select"
          class="mt-4"
          v-model="role"
          :label="__('Invite as')"
          :options="[
            { label: __('Regular Access'), value: 'Sales User' },
            { label: __('Manager Access'), value: 'Sales Manager' },
          ]"
          :description="description"
        />
      </div>
      <template v-if="pendingInvitations.data?.length && !invitees.length">
        <div class="flex flex-col gap-4">
          <div
            class="flex items-center justify-between text-base font-semibold"
          >
            <div>{{ __('Pending Invites') }}</div>
          </div>
          <ul class="flex flex-col gap-1">
            <li
              class="flex items-center justify-between px-2 py-1 rounded-lg bg-surface-gray-2"
              v-for="user in pendingInvitations.data"
              :key="user.name"
            >
              <div class="text-base">
                <span class="text-ink-gray-9">
                  {{ user.email }}
                </span>
                <span class="text-ink-gray-5">
                  ({{ roleMap[user.role] }})
                </span>
              </div>
              <div>
                <Tooltip text="Delete Invitation">
                  <div>
                    <Button
                      icon="x"
                      variant="ghost"
                      :loading="
                        pendingInvitations.delete.loading &&
                        pendingInvitations.delete.params.name === user.name
                      "
                      @click="pendingInvitations.delete.submit(user.name)"
                    />
                  </div>
                </Tooltip>
              </div>
            </li>
          </ul>
        </div>
      </template>
    </div>
    <div class="flex justify-between items-center gap-2">
      <div><ErrorMessage v-if="error" :message="error" /></div>
      <Button
        :label="__('Send Invites')"
        variant="solid"
        :disabled="!invitees.length"
        @click="inviteByEmail.submit()"
        :loading="inviteByEmail.loading"
      />
    </div>
  </div>
</template>
<script setup>
import MultiSelectEmailInput from '@/components/Controls/MultiSelectEmailInput.vue'
import { validateEmail, convertArrayToString } from '@/utils'
import {
  createListResource,
  createResource,
  FormControl,
  Tooltip,
} from 'frappe-ui'
import { useOnboarding } from 'frappe-ui/frappe'
import { ref, computed } from 'vue'

const { updateOnboardingStep } = useOnboarding('frappecrm')

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
    updateOnboardingStep('invite_your_team')
  },
  onError(err) {
    error.value = err?.messages?.[0]
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
