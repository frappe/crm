<template>
  <div class="flex h-full flex-col gap-8 p-8 text-ink-gray-9">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h2 class="flex gap-2 text-xl font-semibold leading-none h-5">
        {{ __('Agents') }}
      </h2>
      <div class="flex item-center space-x-2 mr-2">
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
      </div>
    </div>

    <!-- loading state -->
    <div v-if="agents.loading" class="flex mt-28 justify-between w-full h-full">
      <Button
        :loading="agents.loading"
        variant="ghost"
        class="w-full"
        size="2xl"
      />
    </div>
    <!-- Empty State -->
    <div
      v-if="!agents.loading && !agents.data?.length"
      class="flex mt-28 justify-between w-full h-full"
    >
      <p class="text-sm text-gray-500 w-full flex justify-center">
        {{ __('No agents found') }}
      </p>
    </div>
    <!-- Agents List -->
    <ul
      v-if="!agents.loading && Boolean(agents.data?.length)"
      class="divide-y overflow-auto"
    >
      <li
        class="flex items-center justify-between p-2"
        v-for="agent in agents.data"
        :key="agent.name"
      >
        <div class="flex items-center">
          <Avatar :image="agent.image" :label="agent.agent_name" size="xl" />
          <div class="flex flex-col gap-1 ml-3">
            <div class="flex items-center gap-2 text-base text-ink-gray-9 h-4">
              {{ agent.agent_name }}
              <Badge
                v-if="!agent.is_active"
                variant="subtle"
                theme="gray"
                size="sm"
                label="Inactive"
              />
            </div>
            <div class="text-base text-ink-gray-5">
              {{ agent.name }}
            </div>
          </div>
        </div>
        <div class="flex gap-1 items-center flex-row-reverse">
          <Dropdown
            :options="getMoreOptions(agent)"
            :button="{
              icon: 'more-horizontal',
              variant: 'ghost',
            }"
            placement="right"
          />
          <Dropdown
            :options="getDropdownOptions(agent)"
            :button="{
              label: roleMap[getUserRole(agent.name)],
              iconRight: 'chevron-down',
              variant: 'ghost',
            }"
            placement="right"
          />
        </div>
      </li>
      <!-- Load More Button -->
      <div class="flex justify-center">
        <Button
          v-if="!agents.loading && agents.hasNextPage"
          class="mt-3.5 p-2"
          @click="() => agents.next()"
          :loading="agents.loading"
          :label="__('Load More')"
          icon-left="refresh-cw"
        />
      </div>
    </ul>
  </div>
</template>

<script setup>
import LucideCheck from '~icons/lucide/check'
import { usersStore } from '@/stores/users'
import {
  Avatar,
  Badge,
  createListResource,
  FormControl,
  toast,
  call,
} from 'frappe-ui'
import { ref, h, watch } from 'vue'

const { users, getUserRole } = usersStore()

const agents = createListResource({
  doctype: 'CRM Agent',
  cache: 'CRM Agents',
  fields: ['name', 'image', 'is_active', 'agent_name'],
  auto: true,
  start: 0,
  pageLength: 20,
  orderBy: 'creation desc',
})

const roleMap = {
  'Sales Manager': __('Manager Access'),
  'Sales User': __('Regular Access'),
}

function getMoreOptions(agent) {
  let options = [
    {
      label: __('Activate'),
      icon: 'check-circle',
      onClick: () => updateStatus(agent, true),
      condition: () => !agent.is_active,
    },
    {
      label: __('Deactivate'),
      icon: 'x-circle',
      onClick: () => updateStatus(agent, false),
      condition: () => agent.is_active,
    },
  ]

  return options.filter((option) => option.condition())
}

function getDropdownOptions(agent) {
  const agentRole = getUserRole(agent.name)
  return [
    {
      label: __('Manager Access'),
      component: (props) =>
        RoleOption({
          role: __('Manager Access'),
          active: props.active,
          selected: agentRole === 'Sales Manager',
          onClick: () => updateRole(agent, 'Sales Manager'),
        }),
    },
    {
      label: __('Regular Access'),
      component: (props) =>
        RoleOption({
          role: __('Regular Access'),
          active: props.active,
          selected: agentRole === 'Sales User',
          onClick: () => updateRole(agent, 'Sales User'),
        }),
    },
  ]
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

function updateRole(agent, newRole) {
  const currentRole = getUserRole(agent.name)
  if (currentRole === newRole) return

  call('crm.fcrm.doctype.crm_agent.crm_agent.update_agent_role', {
    user: agent.name,
    new_role: newRole,
  }).then(() => {
    toast.success(
      __('{0} has been granted {1}', [agent.agent_name, roleMap[newRole]]),
    )
    users.reload()
    agents.reload()
  })
}

function updateStatus(agent, status) {
  const currentStatus = agent.is_active
  if (currentStatus === status) return

  call('crm.fcrm.doctype.crm_agent.crm_agent.update_agent_status', {
    agent: agent.name,
    status,
  }).then(() => {
    toast.success(
      __('{0} has been {1}', [
        agent.agent_name,
        status ? 'activated' : 'deactivated',
      ]),
    )
    agents.reload()
  })
}

const search = ref('')
watch(search, (newValue) => {
  agents.filters = {
    is_active: ['=', 1],
    agent_name: ['like', `%${newValue}%`],
  }
  if (!newValue) {
    agents.filters = {
      is_active: ['=', 1],
    }
    agents.start = 0
    agents.pageLength = 10
  }
  agents.reload()
})
</script>
