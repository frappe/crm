<template>
  <div class="flex h-full flex-col gap-8 p-8 text-ink-gray-9">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h2 class="flex gap-2 text-xl font-semibold leading-none h-5">
        {{ __('Users') }}
      </h2>
      <div class="flex item-center space-x-2">
        <FormControl
          v-model="search"
          :placeholder="'Search'"
          type="text"
          :debounce="300"
        >
          <template #prefix>
            <LucideSearch class="h-4 w-4 text-ink-gray-4" />
          </template>
        </FormControl>
        <FormControl
          type="select"
          :value="currentStatus"
          :options="[
            { label: __('All'), value: 'All' },
            { label: __('Active'), value: 'Active' },
            { label: __('Inactive'), value: 'Inactive' },
          ]"
          @change="(e) => changeStatus(e.target.value)"
        >
        </FormControl>
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
      v-if="!users.loading && !users.data?.length"
      class="flex mt-28 justify-between w-full h-full"
    >
      <p class="text-sm text-gray-500 w-full flex justify-center">
        {{ __('No users found') }}
      </p>
    </div>
    <!-- Users List -->
    <ul
      v-if="!users.loading && Boolean(users.data?.length)"
      class="divide-y overflow-auto"
    >
      <li
        class="flex items-center justify-between py-2"
        v-for="user in users.data"
        :key="user.name"
      >
        <div class="flex items-center">
          <Avatar :image="user.image" :label="user.user_name" size="xl" />
          <div class="flex flex-col gap-1 ml-3">
            <div class="flex items-center gap-2 text-base text-ink-gray-9 h-4">
              {{ user.user_name }}
              <Badge
                v-if="!user.is_active"
                variant="subtle"
                theme="gray"
                size="sm"
                label="Inactive"
              />
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
              label: roleMap[getUserRole(user.name)],
              iconRight: 'chevron-down',
            }"
            placement="right"
          />
        </div>
      </li>
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
</template>

<script setup>
import LucideCheck from '~icons/lucide/check'
import { activeSettingsPage } from '@/composables/settings'
import { usersStore } from '@/stores/users'
import {
  Avatar,
  Badge,
  createListResource,
  FormControl,
  toast,
  call,
} from 'frappe-ui'
import { ref, h, watch, onMounted } from 'vue'

const { users: usersResource, getUserRole, isAdmin, isManager } = usersStore()

const showAddExistingModal = ref(false)

const users = createListResource({
  doctype: 'CRM User',
  cache: 'CRM Users',
  fields: ['name', 'image', 'is_active', 'user_name'],
  filters: { is_active: ['=', 1] },
  auto: true,
  start: 0,
  pageLength: 20,
  orderBy: 'creation desc',
})

const roleMap = {
  'System Manager': __('Admin'),
  'Sales Manager': __('Manager'),
  'Sales User': __('Sales User'),
}

function getMoreOptions(user) {
  let options = [
    {
      label: __('Activate'),
      icon: 'check-circle',
      onClick: () => updateStatus(user, true),
      condition: () => !user.is_active,
    },
    {
      label: __('Deactivate'),
      icon: 'x-circle',
      onClick: () => updateStatus(user, false),
      condition: () => user.is_active,
    },
  ]

  return options.filter((option) => option.condition())
}

function getDropdownOptions(user) {
  const userRole = getUserRole(user.name)
  let options = [
    {
      label: __('Admin'),
      component: (props) =>
        RoleOption({
          role: __('Admin'),
          active: props.active,
          selected: userRole === 'System Manager',
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
          selected: userRole === 'Sales Manager',
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
          selected: userRole === 'Sales User',
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
        active ? 'bg-surface-gray-2' : 'text-ink-gray-9',
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
  const currentRole = getUserRole(user.name)
  if (currentRole === newRole) return

  call('crm.fcrm.doctype.crm_user.crm_user.update_user_role', {
    user: user.name,
    new_role: newRole,
  }).then(() => {
    toast.success(
      __('{0} has been granted {1} access', [user.user_name, roleMap[newRole]]),
    )
    usersResource.reload()
    users.reload()
  })
}

function updateStatus(user, status) {
  const currentStatus = user.is_active
  if (currentStatus === status) return

  call('crm.fcrm.doctype.crm_user.crm_user.update_user_status', {
    user: user.name,
    status,
  }).then(() => {
    toast.success(
      __('{0} has been {1}', [
        user.user_name,
        status ? 'activated' : 'deactivated',
      ]),
    )
    users.reload()
  })
}

const currentStatus = ref('Active')

function changeStatus(status) {
  currentStatus.value = status
  updateFilters()
}

function updateFilters() {
  const status = currentStatus.value || 'Active'

  users.filters = {}
  if (status === 'Active') {
    users.filters.is_active = ['=', 1]
  } else if (status === 'Inactive') {
    users.filters.is_active = ['=', 0]
  }
  users.reload()
}

onMounted(() => updateFilters())

const search = ref('')
watch(search, (newValue) => {
  users.filters = {
    is_active: ['=', 1],
    user_name: ['like', `%${newValue}%`],
  }
  if (!newValue) {
    users.filters = {
      is_active: ['=', 1],
    }
    users.start = 0
    users.pageLength = 10
  }
  users.reload()
})
</script>
