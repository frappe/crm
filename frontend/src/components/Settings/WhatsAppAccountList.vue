<template>
  <div class="flex flex-col">
    <!-- header -->
    <div class="flex justify-between text-ink-gray-8">
      <div class="flex flex-col gap-1 w-9/12">
        <h2 class="flex gap-2 text-xl font-semibold leading-none h-5">
          {{ __('WhatsApp Accounts') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Connect one or more WhatsApp Business accounts. Set one as the default used to send and receive messages in CRM.',
            )
          }}
        </p>
      </div>
      <div class="flex item-center space-x-2 w-3/12 justify-end">
        <Button
          :label="__('Add Account')"
          theme="gray"
          variant="solid"
          icon-left="plus"
          @click="showAddDialog = true"
        />
      </div>
    </div>

    <!-- list -->
    <div
      v-if="!accounts.loading && Boolean(accounts.data?.length)"
      class="mt-4"
    >
      <div v-for="(account, i) in accounts.data" :key="account.name">
        <div
          class="flex items-center justify-between px-2 py-3 cursor-pointer rounded hover:bg-surface-menu-bar"
          @click="emit('edit', account.name)"
        >
          <div class="flex flex-col gap-0.5">
            <div class="flex items-center gap-2 text-p-base text-ink-gray-8">
              {{ account.account_name }}
              <Badge
                v-if="account.name === defaultAccount"
                variant="subtle"
                theme="blue"
                :label="__('Default')"
              />
            </div>
            <div class="text-p-sm text-ink-gray-5">
              {{
                account.phone_id
                  ? __('Phone ID: {0}', [account.phone_id])
                  : __('No phone number ID set')
              }}
            </div>
          </div>
          <div class="flex items-center gap-2" @click.stop>
            <Badge
              variant="subtle"
              :theme="account.status === 'Active' ? 'green' : 'gray'"
              :label="__(account.status || 'Inactive')"
            />
            <Dropdown :options="getDropdownOptions(account)">
              <Button variant="ghost" icon="more-horizontal" />
            </Dropdown>
          </div>
        </div>
        <div
          v-if="accounts.data.length !== i + 1"
          class="h-px border-t mx-2 border-outline-gray-modals"
        />
      </div>
    </div>
    <!-- fallback when no accounts -->
    <EmptyState
      v-else
      name="WhatsApp Accounts"
      :description="__('Add one to start messaging.')"
      :icon="WhatsAppIcon"
    />

    <!-- add account dialog -->
    <Dialog
      v-model="showAddDialog"
      :options="{
        title: __('Add WhatsApp Account'),
        actions: [
          {
            label: __('Create'),
            variant: 'solid',
            loading: accounts.insert.loading,
            onClick: createAccount,
          },
        ],
      }"
    >
      <template #body-content>
        <FormControl
          v-model="newAccountName"
          :label="__('Account Name')"
          :placeholder="__('e.g. Sales Line')"
          autocomplete="off"
          @keydown.enter="createAccount"
        />
        <p class="mt-2 text-p-sm text-ink-gray-5">
          {{
            __(
              'A unique name to identify this account. You can add the API credentials on the next screen.',
            )
          }}
        </p>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import { ConfirmDelete } from '@/utils'
// Badge, Dialog and FormControl are registered globally in main.js (like Button),
// so they're used directly in the template without importing. Only the non-global
// helpers are imported here.
import {
  createListResource,
  createResource,
  call,
  Dropdown,
  toast,
} from 'frappe-ui'
import { ref } from 'vue'

const emit = defineEmits(['edit'])

const showAddDialog = ref(false)
const newAccountName = ref('')
const confirmDelete = ref(false)
const defaultAccount = ref('')

const accounts = createListResource({
  doctype: 'WhatsApp Account',
  cache: 'WhatsApp Accounts',
  fields: ['name', 'account_name', 'status', 'phone_id'],
  pageLength: 99,
  auto: true,
})

// The default account lives on the WhatsApp Settings Single.
createResource({
  url: 'frappe.client.get_value',
  params: { doctype: 'WhatsApp Settings', fieldname: 'default_account' },
  auto: true,
  onSuccess: (data) => {
    defaultAccount.value = data?.default_account || ''
  },
})

function createAccount() {
  const name = newAccountName.value?.trim()
  if (!name) {
    toast.error(__('Account name is required'))
    return
  }
  accounts.insert.submit(
    { account_name: name },
    {
      onSuccess: (doc) => {
        showAddDialog.value = false
        newAccountName.value = ''
        emit('edit', doc.name)
      },
      onError: (error) => {
        toast.error(error.messages?.[0] || __('Failed to create account'))
      },
    },
  )
}

function setDefault(account) {
  call('frappe.client.set_value', {
    doctype: 'WhatsApp Settings',
    name: 'WhatsApp Settings',
    fieldname: 'default_account',
    value: account.name,
  })
    .then(() => {
      defaultAccount.value = account.name
      toast.success(__('{0} set as default account', [account.account_name]))
    })
    .catch((error) => {
      toast.error(error.messages?.[0] || __('Failed to set default account'))
    })
}

function deleteAccount(account) {
  confirmDelete.value = false
  accounts.delete.submit(account.name, {
    onSuccess: () => {
      toast.success(__('Account deleted'))
      if (defaultAccount.value === account.name) defaultAccount.value = ''
    },
    onError: (error) => {
      toast.error(error.messages?.[0] || __('Failed to delete account'))
    },
  })
}

function getDropdownOptions(account) {
  const options = []
  if (account.name !== defaultAccount.value) {
    options.push({
      label: __('Set as default'),
      icon: 'check-circle',
      onClick: () => setDefault(account),
    })
  }
  options.push(
    ...ConfirmDelete({
      onConfirmDelete: () => deleteAccount(account),
      isConfirmingDelete: confirmDelete,
    }),
  )
  return options
}
</script>
