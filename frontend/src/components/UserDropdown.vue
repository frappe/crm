<template>
  <Dropdown :options="dropdownItems.doc || []" v-bind="$attrs">
    <template v-slot="{ open }">
      <button
        class="flex h-12 items-center rounded-md py-2 duration-300 ease-in-out"
        :class="
          isCollapsed
            ? 'w-auto px-0'
            : open
              ? 'w-52 bg-surface-white px-2 shadow-sm'
              : 'w-52 px-2 hover:bg-surface-gray-3'
        "
      >
        <CRMLogo class="size-8 flex-shrink-0 rounded" />
        <div
          class="flex flex-1 flex-col text-left duration-300 ease-in-out"
          :class="
            isCollapsed
              ? 'ml-0 w-0 overflow-hidden opacity-0'
              : 'ml-2 w-auto opacity-100'
          "
        >
          <div class="text-base font-medium leading-none text-ink-gray-9">
            {{ __('CRM') }}
          </div>
          <div class="mt-1 text-sm leading-none text-ink-gray-7">
            {{ user.full_name }}
          </div>
        </div>
        <div
          class="duration-300 ease-in-out"
          :class="
            isCollapsed
              ? 'ml-0 w-0 overflow-hidden opacity-0'
              : 'ml-2 w-auto opacity-100'
          "
        >
          <FeatherIcon
            name="chevron-down"
            class="size-4 text-ink-gray-5"
            aria-hidden="true"
          />
        </div>
      </button>
    </template>
  </Dropdown>
</template>

<script setup>
import CRMLogo from '@/components/Icons/CRMLogo.vue'
import Apps from '@/components/Apps.vue'
import { sessionStore } from '@/stores/session'
import { usersStore } from '@/stores/users'
import { showSettings } from '@/composables/settings'
import { createDocumentResource, Dropdown } from 'frappe-ui'
import { useStorage } from '@vueuse/core'
import { computed, markRaw, onMounted } from 'vue'

const props = defineProps({
  isCollapsed: {
    type: Boolean,
    default: false,
  },
})

const { logout } = sessionStore()
const { getUser } = usersStore()

const user = computed(() => getUser() || {})

const theme = useStorage('theme', 'light')

const dropdownItems = createDocumentResource({
  doctype: 'FCRM Settings',
  name: 'FCRM Settings',
  fields: ['dropdown_items'],
  auto: true,
  transform: (data) => {
    let items = data.dropdown_items

    let _dropdownItems = [
      {
        group: 'Dropdown Items',
        hideLabel: true,
        items: [],
      },
    ]

    items.forEach((item) => {
      if (item.hidden) return
      if (item.type !== 'Separator') {
        _dropdownItems[_dropdownItems.length - 1].items.push(
          dropdownItemObj(item),
        )
      } else {
        _dropdownItems.push({
          group: '',
          hideLabel: true,
          items: [],
        })
      }
    })

    return _dropdownItems
  },
})

function dropdownItemObj(item) {
  let openInNewWindow = item.open_in_new_window
  if (item.is_standard) {
    return getStandardItem(item)
  }
  return {
    icon: item.icon || 'external-link',
    label: __(item.label),
    onClick: () => window.open(item.url, openInNewWindow ? '_blank' : ''),
  }
}

function getStandardItem(item) {
  switch (item.name1) {
    case 'app_selector':
      return {
        component: markRaw(Apps),
      }
    case 'support_link':
      return {
        icon: item.icon,
        label: __(item.label),
        onClick: () => window.open(item.route, '_blank'),
      }
    case 'docs_link':
      return {
        icon: item.icon,
        label: __(item.label),
        onClick: () => window.open(item.route, '_blank'),
      }
    case 'toggle_theme':
      return {
        icon: computed(() => (theme.value === 'dark' ? 'sun' : item.icon)),
        label: __(item.label),
        onClick: toggleTheme,
      }
    case 'settings':
      return {
        icon: item.icon,
        label: __(item.label),
        onClick: () => (showSettings.value = true),
      }
    case 'logout':
      return {
        icon: item.icon,
        label: __(item.label),
        onClick: () => logout.submit(),
      }
  }
}

function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute('data-theme')
  theme.value = currentTheme === 'dark' ? 'light' : 'dark'
  document.documentElement.setAttribute('data-theme', theme.value)
}

onMounted(() => {
  if (['light', 'dark'].includes(theme.value)) {
    document.documentElement.setAttribute('data-theme', theme.value)
  }
})
</script>
