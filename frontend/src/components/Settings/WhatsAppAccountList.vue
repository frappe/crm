<template>
  <div class="flex h-full flex-col">
    <div
      v-if="accounts.loading && !accounts.data"
      class="flex items-center justify-center mt-12"
    >
      <LoadingIndicator class="w-4" />
    </div>
    <EmptyState
      v-else-if="!accounts.data?.length"
      name="WhatsApp Accounts"
      :title="__('No WhatsApp accounts yet')"
      :description="__('Add one to start messaging.')"
      :icon="WhatsAppIcon"
    />
    <div v-else class="w-full">
      <template v-for="(account, i) in accounts.data" :key="account.name">
        <div
          class="flex w-full items-center justify-between rounded px-2 py-3 hover:bg-surface-gray-2"
        >
          <div
            class="min-w-0 cursor-pointer"
            @click="emit('edit', account.name)"
          >
            <div class="truncate text-base-medium text-ink-gray-7">
              {{ account.account_name }}
            </div>
            <div class="mt-0.5 truncate text-p-base text-ink-gray-5">
              {{ __('Phone ID: {0}', [account.phone_id || '-']) }}
            </div>
          </div>
          <div class="flex items-center gap-2">
            <!-- With one account there is nothing to choose between, so the
                 default is implicit and not worth naming. -->
            <Badge
              v-if="hasMultipleAccounts && isDefault(account)"
              variant="subtle"
              theme="blue"
              :label="__('Default')"
            />
            <Dropdown placement="right" :options="rowOptions(account)">
              <Button
                icon="lucide-more-horizontal"
                variant="ghost"
                @click="confirmDelete = false"
              />
            </Dropdown>
          </div>
        </div>
        <hr v-if="accounts.data.length !== i + 1" class="mx-2" />
      </template>
    </div>

    <!-- Frappe refuses to delete an account other records still link to. Say so,
         with the counts, instead of surfacing the raw link-exists error. -->
    <Dialog
      v-model="showBlockedDialog"
      :options="{ title: blockedTitle, actions: blockedActions }"
    >
      <template #body-content>
        <p class="text-p-base text-ink-gray-7">
          {{
            __(
              "Accounts with history can't be deleted. Set it to Inactive instead to stop using it.",
            )
          }}
        </p>
        <div class="mt-4 flex flex-col gap-2">
          <div
            v-for="row in blockedUsage"
            :key="row.label"
            class="flex items-center justify-between text-p-sm"
          >
            <span class="text-ink-gray-5">{{ row.label }}</span>
            <span class="text-ink-gray-8">{{ row.count }}</span>
          </div>
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import { ConfirmDelete } from '@/utils'
// Badge and Dialog are registered globally in main.js (like Button), so they're
// used directly in the template. Only the non-global helpers are imported here.
import {
  createListResource,
  createResource,
  call,
  Dropdown,
  FeatherIcon,
  LoadingIndicator,
  Tooltip,
  toast,
} from 'frappe-ui'
import { computed, h, onMounted, ref } from 'vue'

const emit = defineEmits(['edit'])

const confirmDelete = ref(false)
const defaultAccount = ref('')

const blockedAccount = ref(null)
const blockedUsage = ref([])
const showBlockedDialog = ref(false)
const settingInactive = ref(false)

// Labels for the doctypes crm.api.whatsapp.get_account_usage counts.
const USAGE_LABELS = {
  'WhatsApp Message': () => __('Messages'),
  'WhatsApp Profile': () => __('Contacts'),
  'WhatsApp Template': () => __('Templates'),
  'WhatsApp Log': () => __('Logs'),
}

const accounts = createListResource({
  doctype: 'WhatsApp Account',
  cache: 'WhatsApp Accounts',
  fields: ['name', 'account_name', 'status', 'phone_id'],
  pageLength: 99,
  auto: true,
})

// The default account lives on the WhatsApp Settings Single, and the server
// maintains it: the first account created becomes the default, and deleting the
// last one clears it. Refetch whenever the list changes underneath us.
const defaultAccountResource = createResource({
  url: 'frappe.client.get_value',
  params: { doctype: 'WhatsApp Settings', fieldname: 'default_account' },
  auto: true,
  onSuccess: (data) => {
    defaultAccount.value = data?.default_account || ''
  },
})

// The list resource is cached, and this panel is unmounted whenever the tab
// changes, so refresh on the way back in to pick up accounts added since.
onMounted(() => {
  if (accounts.data) accounts.reload()
})

const hasMultipleAccounts = computed(() => (accounts.data?.length || 0) > 1)

const blockedTitle = computed(() =>
  __("Can't delete {0}", [blockedAccount.value?.account_name || '']),
)

const blockedActions = computed(() => {
  if (blockedAccount.value?.status === 'Inactive') return []
  return [
    {
      label: __('Set Inactive'),
      variant: 'solid',
      loading: settingInactive.value,
      onClick: setInactive,
    },
  ]
})

function isDefault(account) {
  return account.name === defaultAccount.value
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

async function confirmDeleteAccount(account) {
  let usage = {}
  try {
    usage = await call('crm.api.whatsapp.get_account_usage', {
      account: account.name,
    })
  } catch (error) {
    toast.error(error.messages?.[0] || __('Failed to delete account'))
    return
  }

  const linked = Object.entries(usage || {})
    .filter(([, count]) => count > 0)
    .map(([doctype, count]) => ({
      label: USAGE_LABELS[doctype]?.() || __(doctype),
      count,
    }))

  if (linked.length) {
    blockedAccount.value = account
    blockedUsage.value = linked
    showBlockedDialog.value = true
    return
  }

  deleteAccount(account)
}

function deleteAccount(account) {
  accounts.delete.submit(account.name, {
    onSuccess: () => {
      toast.success(__('Account deleted'))
      // Deleting the last account clears the default server-side.
      defaultAccountResource.reload()
    },
    onError: (error) => {
      toast.error(error.messages?.[0] || __('Failed to delete account'))
    },
  })
}

function setInactive() {
  const account = blockedAccount.value
  settingInactive.value = true
  call('frappe.client.set_value', {
    doctype: 'WhatsApp Account',
    name: account.name,
    fieldname: 'status',
    value: 'Inactive',
  })
    .then(() => {
      showBlockedDialog.value = false
      toast.success(__('{0} set to Inactive', [account.account_name]))
      accounts.reload()
    })
    .catch((error) => {
      toast.error(error.messages?.[0] || __('Failed to update account'))
    })
    .finally(() => {
      settingInactive.value = false
    })
}

// A disabled Dropdown item gets `pointer-events-none`, which would swallow the
// hover a Tooltip needs. Render an inert item instead so the reason is reachable.
function blockedDeleteOption(reason) {
  return {
    label: __('Delete'),
    component: () =>
      h(Tooltip, { text: reason, placement: 'left' }, () =>
        h(
          'div',
          {
            class:
              'flex w-full gap-2 items-center rounded-md px-2 py-2 text-base text-ink-gray-4 cursor-not-allowed',
          },
          [
            h(FeatherIcon, { name: 'trash-2', class: 'h-4 w-4 shrink-0' }),
            h('span', { class: 'whitespace-nowrap' }, __('Delete')),
          ],
        ),
      ),
  }
}

function rowOptions(account) {
  const options = [
    {
      label: __('Edit'),
      icon: 'edit-2',
      onClick: () => emit('edit', account.name),
    },
  ]

  if (hasMultipleAccounts.value && !isDefault(account)) {
    options.push({
      label: __('Set as default'),
      icon: 'check-circle',
      onClick: () => setDefault(account),
    })
  }

  // The default can't be deleted while other accounts exist — something has to
  // stay selected. WhatsAppAccount.on_trash enforces this server-side too.
  if (hasMultipleAccounts.value && isDefault(account)) {
    options.push(
      blockedDeleteOption(
        __('Set another account as the default before deleting it.'),
      ),
    )
  } else {
    options.push(
      ...ConfirmDelete({
        onConfirmDelete: () => confirmDeleteAccount(account),
        isConfirmingDelete: confirmDelete,
      }),
    )
  }

  return options
}
</script>
