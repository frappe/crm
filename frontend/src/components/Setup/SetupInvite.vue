<template>
  <div class="flex flex-col">
    <h1 class="text-2xl-semibold text-ink-gray-9">
      {{ __('Invite your team') }}
    </h1>
    <p class="mt-2 text-p-base text-ink-gray-6">
      {{ __('The CRM works best when your whole sales team is in it.') }}
    </p>

    <p class="mt-3 text-p-sm text-ink-gray-6">
      <strong class="font-semibold text-ink-gray-9">{{
        __('No per-user pricing.')
      }}</strong>
      {{ __('Invite your whole team.') }}
    </p>

    <InviteStep
      class="mt-8"
      :roles="roleOptions"
      default-role="Sales User"
      :send="send"
      :labels="labels"
      @invitees="showInPreview"
      @done="finish"
      @skip="emit('skip')"
    >
      <template v-if="noMailbox" #error>
        <p class="text-sm text-ink-red-7" role="alert">
          {{ __('Invites go out by email, and no email account is set up.') }}
          <button
            type="button"
            class="font-medium underline underline-offset-2"
            @click="emit('connectEmail')"
          >
            {{ __('Connect email') }}
          </button>
        </p>
      </template>
    </InviteStep>
  </div>
</template>

<script setup>
import { useCrmOnboarding } from '@/composables/onboarding'
import { usersStore } from '@/stores/users'
import { call } from 'frappe-ui'
import { InviteStep } from '@framework/ui/components/SetupFlow'
import { useTelemetry } from '@framework/ui/telemetry'
import { computed, inject, onActivated, ref } from 'vue'

const emit = defineEmits(['done', 'skip', 'connectEmail'])
const noMailbox = ref(false)
onActivated(() => (noMailbox.value = false))

const { isAdmin } = usersStore()
const { completeStep } = useCrmOnboarding()
const { capture } = useTelemetry()

const roleOptions = computed(() => [
  { value: 'Sales User', label: __('Sales User') },
  ...(isAdmin()
    ? [
        { value: 'Sales Manager', label: __('Manager') },
        { value: 'System Manager', label: __('Admin') },
      ]
    : []),
])

const labels = {
  placeholder: 'name@company.com',
  email: (row) => __('Teammate email {0}', [row]),
  role: (row) => __('Role for teammate {0}', [row]),
  remove: (row) => __('Remove teammate {0}', [row]),
  add: __('Add another'),
  send: __('Send invites'),
  skip: __('Skip this step'),
  invalid: __('Enter a valid email address'),
  duplicate: __('This email is already in the list'),
  failed: __('Could not send invites'),
}

const preview = inject('setupPreview', null)
function showInPreview(invitees) {
  if (preview) preview.invites = invitees
}

// CRM invites through its own CRM Invitation, which adds the roles below the one picked
// and the Flow role when the person joins.
async function send(role, emails) {
  noMailbox.value = false
  try {
    const result = await call('crm.api.invite_by_email', {
      emails: emails.join(','),
      role,
    })
    return result?.to_invite?.length ?? 0
  } catch (e) {
    noMailbox.value = e?.exc_type === 'OutgoingEmailError'
    throw e
  }
}

function finish(result) {
  completeStep('invite_your_team')
  capture('user_invited')
  emit('done', result)
}
</script>
