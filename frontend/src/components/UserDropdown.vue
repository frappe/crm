<template>
  <Dropdown :options="userDropdownOptions">
    <template v-slot="{ open }">
      <button
        class="flex h-12 py-2 items-center rounded-md duration-300 ease-in-out"
        :class="
          isCollapsed
            ? 'px-0 w-auto'
            : open
            ? 'bg-white shadow-sm px-2 w-52'
            : 'hover:bg-gray-200 px-2 w-52'
        "
      >
        <CRMLogo class="w-8 h-8 rounded flex-shrink-0" />
        <div
          class="flex flex-1 flex-col text-left duration-300 ease-in-out"
          :class="
            isCollapsed
              ? 'opacity-0 ml-0 w-0 overflow-hidden'
              : 'opacity-100 ml-2 w-auto'
          "
        >
          <div class="text-base font-medium text-gray-900 leading-none">
            CRM
          </div>
          <div class="mt-1 text-sm text-gray-700 leading-none">
            {{ user.full_name }}
          </div>
        </div>
        <div
          class="duration-300 ease-in-out"
          :class="
            isCollapsed
              ? 'opacity-0 ml-0 w-0 overflow-hidden'
              : 'opacity-100 ml-2 w-auto'
          "
        >
          <FeatherIcon name="chevron-down" class="h-4 w-4 text-gray-600" aria-hidden="true" />
        </div>
      </button>
    </template>
  </Dropdown>
</template>

<script setup>
import CRMLogo from '@/components/Icons/CRMLogo.vue'
import { sessionStore } from '@/stores/session'
import { usersStore } from '@/stores/users'
import { Dropdown } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  isCollapsed: {
    type: Boolean,
    default: false,
  },
})

const { logout } = sessionStore()
const { getUser } = usersStore()

const user = computed(() => getUser() || {})

const userDropdownOptions = [
  {
    icon: 'log-out',
    label: 'Log out',
    onClick: () => logout.submit(),
  },
]
</script>
