<template>
  <div class="flex h-full flex-col gap-6 p-6">
    <div class="flex justify-between">
      <div class="flex w-9/12 items-center gap-1">
        <Button
          variant="ghost"
          icon-left="lucide-chevron-left"
          :label="name || __('New Account')"
          size="md"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 text-2xl-semibold hover:opacity-70 !pr-0 !max-w-96 !justify-start"
          @click="emit('back')"
        />
        <Badge
          v-if="account.isDirty"
          :label="__('Not Saved')"
          variant="subtle"
          theme="amber"
        />
      </div>
      <div class="flex w-3/12 justify-end">
        <Button
          v-if="account.isDirty || account.isNew"
          :loading="account.saving"
          :label="account.isNew ? __('Create') : __('Save')"
          variant="solid"
          @click="save"
        />
      </div>
    </div>
    <div v-if="account.loading" class="flex flex-1 items-center justify-center">
      <LoadingIndicator class="size-8" />
    </div>
    <!-- p-1/-m-1 leaves the scroll box a little slack beyond the content, so a
         focused control's ring isn't clipped by the edge it sits flush against. -->
    <div v-else class="-m-1 flex-1 overflow-y-auto p-1">
      <AccountForm :controller="account" :show-append-actions="false">
        <template #settings>
          <div class="flex items-center justify-between gap-4">
            <div class="flex min-w-0 flex-1 flex-col gap-1">
              <span class="text-base-medium text-ink-gray-8">
                {{ __('Create from a new number') }}
              </span>
              <span class="text-p-sm text-ink-gray-6">
                {{
                  __(
                    'Messages from numbers already in CRM always go to their lead or deal.',
                  )
                }}
              </span>
            </div>
            <div class="w-40 shrink-0">
              <FormControl
                v-model="newSenders"
                type="select"
                :aria-label="__('Create from a new number')"
                :options="newSenderOptions"
              />
            </div>
          </div>
        </template>
      </AccountForm>
    </div>
  </div>
</template>

<script setup>
import { AccountForm, useAccount, useAppendToggle } from '@whatsapp/ui'
import { FormControl, LoadingIndicator, toast } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  // Empty renders a blank account that the first save creates.
  name: { type: String, default: '' },
})

const emit = defineEmits(['back', 'created'])

const account = useAccount({ name: () => props.name })

const createsLeads = useAppendToggle(account, {
  append_to: 'CRM Lead',
  trigger_on: 'Incoming',
})
const createsDeals = useAppendToggle(account, {
  append_to: 'CRM Deal',
  trigger_on: 'Incoming',
})

const newSenderOptions = [
  { label: __('Nothing'), value: 'none' },
  { label: __('Lead'), value: 'lead' },
  { label: __('Deal'), value: 'deal' },
]

// the two rows are exclusive (crm.api.whatsapp.validate_account), so one choice sets both
const newSenders = computed({
  get: () =>
    createsDeals.value ? 'deal' : createsLeads.value ? 'lead' : 'none',
  set: (choice) => {
    createsLeads.value = choice === 'lead'
    createsDeals.value = choice === 'deal'
  },
})

// The form shows a failed save under itself, so only success needs a toast.
async function save() {
  const wasNew = account.isNew
  const saved = await account.save()
  if (!saved) return
  if (wasNew) {
    toast.success(__('Account created'))
    emit('created', saved)
  } else {
    toast.success(__('Account updated'))
  }
}
</script>
