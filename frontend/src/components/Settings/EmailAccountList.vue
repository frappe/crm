<template>
  <div>
    <!-- header -->
    <div class="flex items-center justify-between text-ink-gray-9">
      <h2 class="flex gap-2 text-xl font-semibold leading-none h-5">
        {{ __('Email Accounts') }}
      </h2>
      <Button
        :label="__('Add Account')"
        theme="gray"
        variant="solid"
        @click="emit('update:step', 'email-add')"
        class="mr-8"
      >
        <template #prefix>
          <LucidePlus class="w-4 h-4" />
        </template>
      </Button>
    </div>
    <!-- list accounts -->
    <div
      v-if="!emailAccounts.loading && Boolean(emailAccounts.data?.length)"
      class="mt-4"
    >
      <div v-for="emailAccount in emailAccounts.data" :key="emailAccount.name">
        <EmailAccountCard
          :emailAccount="emailAccount"
          @click="emit('update:step', 'email-edit', emailAccount)"
        />
      </div>
    </div>
    <!-- fallback if no email accounts -->
    <div v-else class="flex items-center justify-center h-64 text-gray-500">
      {{ __('Please add an email account to continue.') }}
    </div>
  </div>
</template>

<script setup>
import { createListResource } from 'frappe-ui'
import EmailAccountCard from './EmailAccountCard.vue'

const emit = defineEmits(['update:step'])

const emailAccounts = createListResource({
  doctype: 'Email Account',
  cache: true,
  fields: ['*'],
  filters: {
    email_id: ['Not Like', '%example%'],
  },
  pageLength: 10,
  auto: true,
  onSuccess: (accounts) => {
    // convert 0 to false to handle boolean fields
    accounts.forEach((account) => {
      account.enable_incoming = Boolean(account.enable_incoming)
      account.enable_outgoing = Boolean(account.enable_outgoing)
      account.default_incoming = Boolean(account.default_incoming)
      account.default_outgoing = Boolean(account.default_outgoing)
    })
  },
})
</script>
