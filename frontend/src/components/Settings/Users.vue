<template>
  <div
    class="flex h-full flex-col gap-6 p-6 text-ink-gray-8 max-sm:gap-0 max-sm:p-0"
  >
    <!-- Header -->
    <div class="flex justify-between px-2 pt-2 max-sm:hidden">
      <div class="flex flex-col gap-1 w-9/12">
        <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
          {{ __('Users') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Add or invite users and choose their role to control what they can see and do.',
            )
          }}
        </p>
      </div>
      <div class="flex item-center space-x-2 w-3/12 justify-end">
        <Teleport defer to="#settings-phone-actions" :disabled="!isPhone">
          <DropdownSheet
            :title="__('Invite')"
            :options="[
              {
                label: __('Add Existing User'),
                onClick: () => (showAddExistingModal = true),
              },
              {
                label: __('Invite New User'),
                onClick: () => (activeSettingsPage = 'Invite User'),
              },
            ]"
            :button="{
              label: __('New'),
              iconLeft: 'lucide-plus',
              variant: 'solid',
            }"
            align="end"
          >
            <template v-if="isPhone" #default>
              <Button
                :label="__('Invite')"
                icon-left="lucide-plus"
                variant="solid"
              />
            </template>
          </DropdownSheet>
        </Teleport>
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
      name="Users"
      :description="__('Add one to get started.')"
      icon="user"
    />

    <!-- Users List -->
    <div
      v-if="!users.loading && users.data?.crmUsers?.length > 1"
      class="flex flex-col overflow-hidden"
    >
      <div
        v-if="users.data?.crmUsers?.length > 10"
        class="flex items-center gap-2 mb-4 px-2 pt-0.5 max-sm:mb-0 max-sm:px-4 max-sm:py-3"
      >
        <TextInput
          ref="searchRef"
          v-model="search"
          :placeholder="__('Search User')"
          class="w-full"
          :debounce="300"
        >
          <template #prefix>
            <span
              class="lucide-search h-4 w-4 text-ink-gray-6"
              aria-hidden="true"
            />
          </template>
        </TextInput>
        <Select
          v-model="currentRole"
          class="shrink-0 max-sm:w-32"
          :options="[
            { label: __('All'), value: 'All' },
            { label: __('Admin'), value: 'System Manager' },
            { label: __('Manager'), value: 'Sales Manager' },
            { label: __('Sales User'), value: 'Sales User' },
          ]"
        />
      </div>
      <ul
        class="divide-y divide-outline-elevation-2 overflow-y-auto px-2 max-sm:divide-outline-gray-1 max-sm:border-b max-sm:border-outline-gray-1 max-sm:px-0"
      >
        <template v-for="user in usersList" :key="user.name">
          <li
            class="flex items-center justify-between py-2 max-sm:min-h-14 max-sm:gap-3 max-sm:px-4"
          >
            <div class="flex items-center max-sm:min-w-0 max-sm:flex-1">
              <div class="relative shrink-0">
                <Avatar
                  :image="user.user_image"
                  :label="user.full_name"
                  size="xl"
                />
                <div
                  class="absolute -bottom-0.5 -right-0.5 flex rounded-full bg-surface-elevation-2 p-0.5"
                >
                  <AvailabilityDot :user="user.name" class="!size-2.5" />
                </div>
              </div>
              <div class="flex flex-col ml-3 max-sm:min-w-0">
                <div
                  class="flex items-center text-p-base text-ink-gray-8 max-sm:block max-sm:truncate max-sm:text-base-medium max-sm:text-ink-gray-9"
                >
                  {{ user.full_name }}
                </div>
                <div
                  class="text-p-sm text-ink-gray-5 max-sm:truncate max-sm:text-sm"
                >
                  {{ user.name }}
                </div>
              </div>
            </div>
            <div class="flex gap-2 items-center flex-row-reverse shrink-0">
              <DropdownSheet
                :title="user.full_name"
                :options="getMoreOptions(user)"
                :button="{
                  icon: 'lucide-more-horizontal',
                  onblur: (e) => {
                    e.stopPropagation()
                    confirmRemoveFor = null
                  },
                }"
                align="end"
                @update:open="(open) => open && (confirmRemoveFor = null)"
              >
                <template v-if="isPhone" #default>
                  <Button
                    variant="ghost"
                    icon="lucide-more-horizontal"
                    :aria-label="__('More options')"
                  />
                </template>
              </DropdownSheet>
              <Badge
                v-if="isPhone && isManager() && user.role == 'System Manager'"
                :label="__('Admin')"
                variant="subtle"
              />
              <Tooltip
                v-else-if="isManager() && user.role == 'System Manager'"
                :text="__('Cannot change role of user with Admin access')"
              >
                <Button :label="__('Admin')" icon-left="lucide-shield" />
              </Tooltip>
              <DropdownSheet
                v-else
                :title="__('Role')"
                :options="getDropdownOptions(user)"
                :button="{
                  label: roleMap[user.role],
                  iconRight: 'lucide-chevron-down',
                  iconLeft:
                    user.role === 'System Manager'
                      ? 'lucide-shield'
                      : user.role === 'Sales Manager'
                        ? 'lucide-briefcase'
                        : 'lucide-user-check',
                }"
                align="end"
              >
                <template v-if="isPhone" #default>
                  <button
                    type="button"
                    class="flex"
                    :aria-label="__('Change role')"
                  >
                    <Badge :label="roleMap[user.role]" variant="subtle">
                      <template #suffix>
                        <span
                          class="lucide-chevron-down size-3"
                          aria-hidden="true"
                        />
                      </template>
                    </Badge>
                  </button>
                </template>
              </DropdownSheet>
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
            :loading="users.loading"
            :label="__('Load More')"
            icon-left="lucide-refresh-cw"
            @click="() => users.next()"
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
import AvailabilityDot from '@/components/AvailabilityDot.vue'
import Select from '@/components/Controls/Select.vue'
import DropdownSheet from '@/components/DropdownSheet.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import { isPhone } from '@/composables/phone'
import { activeSettingsPage } from '@/composables/settings'
import { usersStore } from '@/stores/users'
import { Avatar, Badge, TextInput, toast, call, Tooltip } from 'frappe-ui'
import { ref, computed, onMounted } from 'vue'
import { ConfirmDelete } from '../../utils'

const { users, isAdmin, isManager } = usersStore()

const showAddExistingModal = ref(false)
const searchRef = ref(null)
const search = ref('')
const currentRole = ref('All')

const roleMap = {
  'System Manager': __('Admin'),
  'Sales Manager': __('Manager'),
  'Sales User': __('Sales User'),
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

// whose row menu shows "Confirm Remove"
const confirmRemoveFor = ref(null)

function getMoreOptions(user) {
  const confirmRemove = computed({
    get: () => confirmRemoveFor.value === user.name,
    set: (confirming) =>
      (confirmRemoveFor.value = confirming ? user.name : null),
  })
  return [
    ...ConfirmDelete({
      onConfirmDelete: () => removeUser(user),
      isConfirmingDelete: confirmRemove,
      label: __('Remove'),
    }),
  ]
}

function getDropdownOptions(user) {
  let options = [
    {
      label: __('Admin'),
      icon: 'lucide-shield',
      selected: user.role === 'System Manager',
      onClick: () => updateRole(user, 'System Manager'),
      condition: () => isAdmin(),
    },
    {
      label: __('Manager'),
      icon: 'lucide-briefcase',
      selected: user.role === 'Sales Manager',
      onClick: () => updateRole(user, 'Sales Manager'),
      condition: () => isAdmin(),
    },
    {
      label: __('Sales User'),
      icon: 'lucide-user-check',
      selected: user.role === 'Sales User',
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
  })
    .then(() => {
      toast.success(
        __('{0} has been granted {1} access', [
          user.full_name,
          roleMap[newRole],
        ]),
      )
      users.reload()
    })
    .catch((e) => {
      toast.error(e?.messages?.[0] || __('Something went wrong'))
    })
}

function removeUser(user) {
  call('crm.api.user.remove_crm_roles_from_user', {
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
  if (searchRef.value && !isPhone.value) {
    searchRef.value.focus()
  }
})
</script>
