<template>
  <div class="flex h-full flex-col gap-6 p-8 text-ink-gray-8">
    <!-- Header -->
    <div class="flex justify-between">
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
    <div
      v-if="!users.loading && users.data?.crmUsers?.length == 1"
      class="flex justify-between w-full h-full"
    >
      <div
        class="text-ink-gray-4 border border-dashed rounded w-full flex items-center justify-center"
      >
        {{ __('No users found') }}
      </div>
    </div>

    <!-- Users List -->
    <div v-if="!users.loading && users.data?.crmUsers?.length > 1">
      <div class="flex items-center justify-between mb-4">
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
            { label: __('Sales User'), value: 'Sales User' },
          ]"
        />
      </div>
      <ul class="divide-y divide-outline-gray-modals overflow-auto">
        <template v-for="user in usersList" :key="user.name">
          <li class="flex items-center justify-between py-2">
            <div class="flex items-center">
              <Avatar
                :image="user.user_image"
                :label="user.full_name"
                size="xl"
              />
              <div class="flex flex-col gap-1 ml-3">
                <div class="flex items-center text-base text-ink-gray-8 h-4">
                  {{ user.full_name }}
                </div>
                <div class="text-base text-ink-gray-5">
                  {{ user.name }}
                </div>
              </div>
            </div>
            <div class="flex gap-2 items-center flex-row-reverse">
              <Dropdown
                :options="getMoreOptions(user)"
                :button="{
                  icon: 'more-horizontal',
                }"
                placement="right"
              />
              <Dropdown
                :options="getDropdownOptions(user)"
                :button="{
                  label: roleMap[user.role],
                  iconRight: 'chevron-down',
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
            :label="__('Load More')"
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
import LucideCheck from '~icons/lucide/check'
import AddExistingUserModal from '@/components/Modals/AddExistingUserModal.vue'
import { activeSettingsPage } from '@/composables/settings'
import { usersStore } from '@/stores/users'
import { Avatar, TextInput, toast, call } from 'frappe-ui'
import { ref, computed, h, onMounted } from 'vue'

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

function getMoreOptions(user) {
  let options = [
    {
      label: __('Remove'),
      icon: 'trash-2',
      onClick: () => removeUser(user, true),
    },
  ]

  return options.filter((option) => option.condition?.() || true)
}

function getDropdownOptions(user) {
  let options = [
    {
      label: __('Admin'),
      component: (props) =>
        RoleOption({
          role: __('Admin'),
          active: props.active,
          selected: user.role === 'System Manager',
          onClick: () => updateRole(user, 'System Manager'),
        }),
      condition: () => isAdmin(),
    },
    {
      label: __('Manager'),
      component: (props) =>
        RoleOption({
          role: __('Manager'),
          active: props.active,
          selected: user.role === 'Sales Manager',
          onClick: () => updateRole(user, 'Sales Manager'),
        }),
      condition: () => isManager(),
    },
    {
      label: __('Sales User'),
      component: (props) =>
        RoleOption({
          role: __('Sales User'),
          active: props.active,
          selected: user.role === 'Sales User',
          onClick: () => updateRole(user, 'Sales User'),
        }),
    },
  ]

  return options.filter((option) => option.condition?.() || true)
}

function RoleOption({ active, role, onClick, selected }) {
  return h(
    'button',
    {
      class: [
        active ? 'bg-surface-gray-2' : 'text-ink-gray-8',
        'group flex w-full justify-between items-center rounded-md px-2 py-2 text-sm',
      ],
      onClick: !selected ? onClick : null,
    },
    [
      h('span', { class: 'whitespace-nowrap' }, role),
      selected
        ? h(LucideCheck, {
            class: ['h-4 w-4 shrink-0 text-ink-gray-7'],
            'aria-hidden': true,
          })
        : null,
    ],
  )
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
  }).then(() => {
    toast.success(__('User {0} has been removed', [user.full_name]))
    users.reload()
  })
}

onMounted(() => {
  if (searchRef.value) {
    searchRef.value.el.focus()
  }
})
</script>
