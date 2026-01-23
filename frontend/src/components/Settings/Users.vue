<template>
  <div class="flex h-full flex-col gap-6 p-6 text-ink-gray-8">
    <!-- Header -->
    <div class="flex justify-between px-2 pt-2">
      <div class="flex flex-col gap-1 w-9/12">
        <h2 class="flex gap-2 text-xl font-semibold leading-none h-5">
          {{ __('Users') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Manage CRM users by adding or inviting them, and assign roles to control their access and permissions',
            )
          }}
        </p>
      </div>
      <div class="flex item-center space-x-2 w-3/12 justify-end">
        <Dropdown
          :options="[
            {
              label: __('Add existing user'),
              onClick: () => (showAddExistingModal = true),
            },
            {
              label: __('Invite new user'),
              onClick: () => (activeSettingsPage = 'Invite User'),
            },
          ]"
          :button="{
            label: __('New'),
            iconLeft: 'plus',
            variant: 'solid',
          }"
          placement="right"
        />
      </div>
    </div>

    <!-- loading state -->
    <div v-if="users.loading" class="flex mt-28 justify-between w-full h-full">
      <Button
        :loading="users.loading"
        variant="ghost"
        class="w-full"
        size="2xl"
      />
    </div>

    <!-- Empty State -->
    <EmptyState
      v-if="!users.loading && users.data?.crmUsers?.length == 1"
      name="users"
      description="Add one to get started."
      icon="user"
    />

    <!-- Users List -->
    <div
      class="flex flex-col overflow-hidden"
      v-if="!users.loading && users.data?.crmUsers?.length > 1"
    >
      <div
        v-if="users.data?.crmUsers?.length > 10"
        class="flex items-center justify-between mb-4 px-2 pt-0.5"
      >
        <TextInput
          ref="searchRef"
          v-model="search"
          :placeholder="__('Search user')"
          class="w-1/3"
          :debounce="300"
        >
          <template #prefix>
            <FeatherIcon name="search" class="h-4 w-4 text-ink-gray-6" />
          </template>
        </TextInput>
        <FormControl
          type="select"
          v-model="currentRole"
          :options="[
            { label: __('All'), value: 'All' },
            { label: __('Admin'), value: 'System Manager' },
            { label: __('Manager'), value: 'Sales Manager' },
            { label: __('Sales user'), value: 'Sales User' },
          ]"
        />
      </div>
      <ul class="divide-y divide-outline-gray-modals overflow-y-auto px-2">
        <template v-for="user in usersList" :key="user.name">
          <li class="flex items-center justify-between py-2">
            <div class="flex items-center">
              <Avatar
                :image="user.user_image"
                :label="user.full_name"
                size="xl"
              />
              <div class="flex flex-col ml-3">
                <div class="flex items-center text-p-base text-ink-gray-8">
                  {{ user.full_name }}
                </div>
                <div class="text-p-sm text-ink-gray-5">
                  {{ user.name }}
                </div>
              </div>
            </div>
            <div class="flex gap-2 items-center flex-row-reverse">
              <Dropdown
                :options="getMoreOptions(user)"
                :button="{
                  icon: 'more-horizontal',
                  onblur: (e) => {
                    e.stopPropagation()
                    confirmRemove = false
                  },
                }"
                placement="right"
              />
              <Tooltip
                v-if="isManager() && user.role == 'System Manager'"
                :text="__('Cannot change role of user with Admin access')"
              >
                <Button :label="__('Admin')" icon-left="shield" />
              </Tooltip>
              <Dropdown
                v-else
                :options="getDropdownOptions(user)"
                :button="{
                  label: roleMap[user.role],
                  iconRight: 'chevron-down',
                  iconLeft:
                    user.role === 'System Manager'
                      ? 'shield'
                      : user.role === 'Sales Manager'
                        ? 'briefcase'
                        : 'user-check',
                }"
                placement="right"
              />
            </div>
          </li>
        </template>
        <!-- Load More Button -->
        <div
          v-if="!users.loading && users.hasNextPage"
          class="flex justify-center"
        >
          <Button
            class="mt-3.5 p-2"
            @click="() => users.next()"
            :loading="users.loading"
            :label="__('Load more')"
            icon-left="refresh-cw"
          />
        </div>
      </ul>
    </div>
  </div>
  <AddExistingUserModal
    v-if="showAddExistingModal"
    v-model="showAddExistingModal"
  />
</template>

<script setup>
import AddExistingUserModal from '@/components/Modals/AddExistingUserModal.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import { activeSettingsPage } from '@/composables/settings'
import { usersStore } from '@/stores/users'
import { DropdownOption } from '@/utils'
import {
  Dropdown,
  Avatar,
  TextInput,
  toast,
  call,
  FeatherIcon,
  Tooltip,
} from 'frappe-ui'
import { ref, computed, onMounted } from 'vue'

const { users, isAdmin, isManager } = usersStore()

const showAddExistingModal = ref(false)
const searchRef = ref(null)
const search = ref('')
const currentRole = ref('All')

const roleMap = {
  'System Manager': __('Admin'),
  'Sales Manager': __('Manager'),
  'Sales User': __('Sales user'),
}

const usersList = computed(() => {
  let filteredUsers =
    users.data?.crmUsers?.filter((user) => user.name !== 'Administrator') || []

  return filteredUsers
    .filter(
      (user) =>
        user.name?.includes(search.value) ||
        user.full_name?.includes(search.value),
    )
    .filter((user) => {
      if (currentRole.value === 'All') return true
      return user.role === currentRole.value
    })
})

const confirmRemove = ref(false)

function getMoreOptions(user) {
  let options = [
    {
      label: __('Remove'),
      icon: 'trash-2',
      onClick: (e) => {
        e.preventDefault()
        e.stopPropagation()
        confirmRemove.value = true
      },
      condition: () => !confirmRemove.value,
    },
    {
      label: __('Confirm remove'),
      icon: 'trash-2',
      theme: 'red',
      onClick: () => removeUser(user, true),
      condition: () => confirmRemove.value,
    },
  ]

  return options.filter((option) => option.condition?.() || true)
}

function getDropdownOptions(user) {
  let options = [
    {
      label: __('Admin'),
      component: () =>
        DropdownOption({
          option: __('Admin'),
          icon: 'shield',
          selected: user.role === 'System Manager',
        }),
      onClick: () => updateRole(user, 'System Manager'),
      condition: () => isAdmin(),
    },
    {
      label: __('Manager'),
      component: () =>
        DropdownOption({
          option: __('Manager'),
          icon: 'briefcase',
          selected: user.role === 'Sales Manager',
        }),
      onClick: () => updateRole(user, 'Sales Manager'),
      condition: () => isManager(),
    },
    {
      label: __('Sales user'),
      component: () =>
        DropdownOption({
          option: __('Sales user'),
          icon: 'user-check',
          selected: user.role === 'Sales User',
        }),
      onClick: () => updateRole(user, 'Sales User'),
    },
  ]

  return options.filter((option) => option.condition?.() || true)
}

function updateRole(user, newRole) {
  if (user.role === newRole) return

  call('crm.api.user.update_user_role', {
    user: user.name,
    new_role: newRole,
  }).then(() => {
    toast.success(
      __('{0} has been granted {1} access', [user.full_name, roleMap[newRole]]),
    )
    users.reload()
  })
}

function removeUser(user) {
  call('crm.api.user.remove_user', {
    user: user.name,
  })
    .then(() => {
      toast.success(__('User {0} has been removed', [user.full_name]))
      users.reload()
    })
    .catch((e) => {
      toast.error(e?.messages?.[0] || __('Something went wrong'))
    })
}

onMounted(() => {
  if (searchRef.value) {
    searchRef.value.el.focus()
  }
})
</script>
