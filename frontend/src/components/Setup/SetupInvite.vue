<template>
  <div class="flex flex-col">
    <h1 class="text-2xl-semibold text-ink-gray-9">
      {{ __('Invite your team') }}
    </h1>
    <p class="mt-2 text-p-base text-ink-gray-6">
      {{ __('The CRM works best when your whole sales team is in it.') }}
    </p>

    <div class="mt-8 flex flex-col gap-2">
      <div
        v-for="(row, index) in rows"
        :key="index"
        class="flex flex-col gap-1"
      >
        <div class="flex items-center gap-2">
          <div class="min-w-0 flex-1">
            <FormControl
              v-model="row.email"
              type="email"
              placeholder="name@company.com"
              :aria-label="__('Teammate email {0}', [index + 1])"
              :aria-invalid="isInvalid(row)"
            />
          </div>
          <div class="w-40 shrink-0">
            <FormControl
              v-model="row.role"
              type="select"
              :options="roleOptions"
              :aria-label="__('Role for teammate {0}', [index + 1])"
            />
          </div>
        </div>
        <ErrorMessage
          v-if="isInvalid(row)"
          :message="__('Enter a valid email address')"
        />
      </div>
      <Button
        variant="ghost"
        class="self-start"
        :label="__('Add more')"
        icon-left="lucide-user-plus"
        @click="addRow"
      />
    </div>

    <ErrorMessage v-if="error" class="mt-3" :message="error" />

    <div class="mt-auto flex flex-col gap-2 pt-8">
      <Button
        variant="solid"
        size="md"
        :label="__('Send invites')"
        :loading="sending"
        :disabled="!canSend"
        @click="sendInvites"
      />
      <Button
        variant="ghost"
        :label="__('Skip for now')"
        :disabled="sending"
        @click="emit('skip')"
      />
    </div>
  </div>
</template>

<script setup>
import { useCrmOnboarding } from '@/composables/onboarding'
import { usersStore } from '@/stores/users'
import { validateEmail } from '@/utils'
import { groupInvitesByRole } from '@/utils/setup'
import { Button, ErrorMessage, FormControl, call } from 'frappe-ui'
import { useTelemetry } from 'frappe-ui/frappe'
import { computed, ref } from 'vue'

const emit = defineEmits(['done', 'skip'])

const { isAdmin } = usersStore()
const { completeStep } = useCrmOnboarding()
const { capture } = useTelemetry()

const rows = ref([newRow(), newRow()])
const sending = ref(false)
const error = ref('')

const roleOptions = computed(() => [
  { value: 'Sales User', label: __('Sales User') },
  ...(isAdmin()
    ? [
        { value: 'Sales Manager', label: __('Manager') },
        { value: 'System Manager', label: __('Admin') },
      ]
    : []),
])

const filledRows = computed(() => rows.value.filter((r) => r.email.trim()))

const canSend = computed(
  () => filledRows.value.length && !filledRows.value.some(isInvalid),
)

function newRow() {
  return { email: '', role: 'Sales User' }
}

function addRow() {
  rows.value.push(newRow())
}

function isInvalid(row) {
  const email = row.email.trim()
  return Boolean(email) && !validateEmail(email)
}

async function sendInvites() {
  sending.value = true
  error.value = ''
  try {
    const groups = groupInvitesByRole(filledRows.value)
    for (const [role, emails] of Object.entries(groups)) {
      await call('crm.api.invite_by_email', { emails: emails.join(','), role })
    }
    completeStep('invite_your_team')
    capture('user_invited')
    emit('done', { invited: filledRows.value.length })
  } catch (e) {
    error.value = e.messages?.[0] || __('Could not send invites')
  } finally {
    sending.value = false
  }
}
</script>
