<template>
  <!-- The notifications panel is absolutely positioned at `left: 100%`, so it
       needs a positioning context that is not the Sidebar itself (Sidebar sets
       overflow-x-hidden, which would clip the panel away).

       It also paints the sidebar surface: Sidebar's own `bg-surface-sidebar` is
       transparent in dark mode, and nothing behind it sets a background, so the
       column falls through to the white page canvas. The token cannot be
       overridden on the Sidebar element itself — `bg-surface-sidebar` is emitted
       after `bg-surface-gray-1` in the utilities layer and would win. -->
  <div class="relative flex h-full bg-surface-gray-1">
    <Sidebar
      v-model:collapsed="isSidebarCollapsed"
      :collapsible="!mobile"
      :width="mobile ? '260px' : undefined"
      class="peer/sidebar border-r border-outline-gray-1"
    >
      <div class="flex h-full flex-col p-2">
        <UserDropdown :isCollapsed="isCollapsed" />

        <!-- overflow-y-auto forces overflow-x to clip too, which would slice the
             active row's shadow. Widen the scroll box to the sidebar edges and
             pad the content back in so the shadow has room.
             Its rows are shrink-0: once the views overflow the box, flex would
             otherwise squeeze them below their h-7. -->
        <div class="-mx-2 mt-2 flex flex-1 flex-col gap-1 overflow-y-auto px-2">
          <!-- Set apart from the views by the same gap as the app logo above. -->
          <div class="mb-3 flex shrink-0 flex-col gap-1">
            <SidebarItem
              class="shrink-0"
              :label="__('Search')"
              @click="onSearchClick"
            >
              <template #prefix>
                <LucideSearch class="size-4 text-ink-gray-7" />
              </template>
              <span class="flex-1 truncate text-sm leading-tighter">
                {{ __('Search') }}
              </span>
              <span
                v-if="!mobile"
                class="mr-2 rounded-1 bg-surface-gray-2 px-1 py-0.5"
              >
                <KeyboardShortcut combo="Mod+K" />
              </span>
            </SidebarItem>

            <SidebarItem
              id="notifications-btn"
              class="shrink-0"
              :label="__('Notifications')"
              :route="mobile ? { name: 'Notifications' } : undefined"
              :active="mobile && activeItem === 'Notifications'"
              @click="onNotificationsClick"
            >
              <template #prefix>
                <span class="relative grid size-4 place-items-center">
                  <NotificationsIcon class="size-4 text-ink-gray-7" />
                  <span
                    v-if="isCollapsed && unreadNotificationsCount"
                    class="absolute -right-1 -top-1 size-1.5 rounded-full bg-surface-gray-9 ring-1 ring-[var(--surface-gray-1)]"
                  />
                </span>
              </template>
              <!-- Not in #suffix: that slot sits outside the button, so a click on
                   the count would not toggle the panel. -->
              <span class="flex-1 truncate text-sm leading-tighter">
                {{ __('Notifications') }}
              </span>
              <Badge
                v-if="unreadNotificationsCount"
                class="mr-2"
                :label="unreadNotificationsCount"
                variant="subtle"
              />
            </SidebarItem>

            <SidebarItem
              v-if="showFlow"
              class="shrink-0"
              :label="__('Flow')"
              @click="onFlowClick"
            >
              <template #prefix>
                <FlowIcon class="size-4 text-ink-gray-7" />
              </template>
              <span class="flex-1 truncate text-sm leading-tighter">
                {{ __('Flow') }}
              </span>
              <span
                v-if="!mobile"
                class="mr-2 rounded-1 bg-surface-gray-2 px-1 py-0.5"
              >
                <KeyboardShortcut combo="Mod+I" />
              </span>
            </SidebarItem>
          </div>

          <CollapsibleSection
            v-for="section in allViews"
            :key="section.name"
            :label="section.name"
            :hideLabel="section.hideLabel"
            :opened="section.opened"
          >
            <template #header="{ opened, hide, toggle }">
              <SidebarLabel
                v-if="!hide"
                divider
                class="mb-1 mt-4 select-none"
                :class="!isCollapsed && 'cursor-pointer'"
                @click="toggle()"
              >
                <span class="flex items-center gap-1.5">
                  <span
                    class="lucide-chevron-right -ml-0.5 size-4 shrink-0 text-ink-gray-9 transition-transform duration-300 ease-in-out"
                    :class="{ 'rotate-90': opened }"
                    aria-hidden="true"
                  />
                  <span class="truncate">{{ __(section.name) }}</span>
                </span>
              </SidebarLabel>
            </template>
            <nav class="flex flex-col gap-1">
              <SidebarItem
                v-for="link in section.views"
                :key="link.key"
                :route="link.to"
                :label="__(link.label)"
                :active="activeItem === link.key"
                @click="selectItem($event, link.key)"
              >
                <template #prefix>
                  <Icon :icon="link.icon" class="size-4 text-ink-gray-7" />
                </template>
                <Tooltip
                  :text="__(link.label)"
                  side="right"
                  :hoverDelay="1500"
                  :disabled="isCollapsed"
                >
                  <span class="truncate text-sm">{{ __(link.label) }}</span>
                </Tooltip>
              </SidebarItem>
            </nav>
          </CollapsibleSection>
        </div>

        <div class="mt-auto flex flex-col gap-2 pt-2">
          <SidebarNoticeStack v-if="!mobile" :isCollapsed="isCollapsed" />
          <UserMenu :isCollapsed="isCollapsed" />
        </div>
      </div>
    </Sidebar>
    <SidebarEdge
      v-if="!mobile"
      :collapsed="isCollapsed"
      @toggle="isSidebarCollapsed = !isSidebarCollapsed"
    />
    <Notifications v-if="!mobile" />
  </div>

  <template v-if="!mobile">
    <Settings />
  </template>
</template>

<script setup>
import CollapsibleSection from '@/components/CollapsibleSection.vue'
import Icon from '@/components/Icon.vue'
import PinIcon from '@/components/Icons/PinIcon.vue'
import UserDropdown from '@/components/UserDropdown.vue'
import { getNavigationItems } from '@/utils/navigation'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import NotificationsIcon from '@/components/Icons/NotificationsIcon.vue'
import Notifications from '@/components/Notifications.vue'
import LucideSearch from '~icons/lucide/search'
import FlowIcon from '@/components/Icons/FlowIcon.vue'
import { hasFlowLauncher } from '@/utils/flowLauncher'
import { openCommandPalette } from '@/composables/useCommandPalette'
import Settings from '@/components/Settings/Settings.vue'
import { viewsStore } from '@/stores/views'
import {
  unreadNotificationsCount,
  notificationsStore,
} from '@/stores/notifications'
import { mobileSidebarOpened, closeMobileSidebar } from '@/composables/settings'
import {
  KeyboardShortcut,
  Sidebar,
  SidebarItem,
  SidebarLabel,
  Tooltip,
} from 'frappe-ui'
import UserMenu from '@/components/Layouts/UserMenu.vue'
import SidebarNoticeStack from '@/components/Layouts/SidebarNoticeStack.vue'
import SidebarEdge from '@/components/Layouts/SidebarEdge.vue'
import { useStorage } from '@vueuse/core'
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps({
  mobile: { type: Boolean, default: false },
})

const route = useRoute()

const { getPinnedViews, getPublicViews } = viewsStore()
const { toggle: toggleNotificationPanel } = notificationsStore()

const isSidebarCollapsed = useStorage('isSidebarCollapsed', false)

// The mobile drawer pins the sidebar open, so it is never visually collapsed
// even when the stored rail state says otherwise.
const isCollapsed = computed(() => isSidebarCollapsed.value && !props.mobile)

const links = getNavigationItems({ mobile: props.mobile })
const showFlow = hasFlowLauncher()

const allViews = computed(() => {
  let _views = [
    {
      name: 'All Views',
      hideLabel: true,
      opened: true,
      views: links.map((link) => ({
        label: link.label,
        icon: link.icon,
        key: link.route,
        to: { name: link.route },
      })),
    },
  ]
  if (getPublicViews().length) {
    _views.push({
      name: 'Public Views',
      opened: true,
      views: parseView(getPublicViews()),
    })
  }

  if (getPinnedViews().length) {
    _views.push({
      name: 'Pinned Views',
      opened: true,
      views: parseView(getPinnedViews()),
    })
  }
  return _views
})

function parseView(views) {
  return views.map((view) => {
    return {
      label: view.label,
      icon: getIcon(view.route_name, view.icon),
      key: view.name,
      to: {
        name: view.route_name,
        params: { viewType: view.type || 'list' },
        query: { view: view.name },
      },
    }
  })
}

function getIcon(routeName, icon) {
  if (icon) return icon

  switch (routeName) {
    case 'Leads':
      return LeadsIcon
    case 'Deals':
      return DealsIcon
    case 'Contacts':
      return ContactsIcon
    case 'Organizations':
      return OrganizationsIcon
    case 'Notes':
      return NoteIcon
    case 'Call Logs':
      return PhoneIcon
    default:
      return PinIcon
  }
}

// A saved view's key is its name; a plain nav item's key is its route name.
function currentRouteKey() {
  return route.query.view || route.name
}

// Set the highlight on click rather than waiting for the route, since route
// components are lazily imported and the first visit waits on a chunk fetch.
// Modified clicks open a new tab without navigating this one, so they must not
// move the highlight here.
const activeItem = ref(currentRouteKey())

function selectItem(event, key) {
  if (
    event.metaKey ||
    event.ctrlKey ||
    event.shiftKey ||
    event.altKey ||
    event.button === 1
  ) {
    return
  }
  activeItem.value = key
  // Selecting the row for the route already open leaves the URL unchanged, so
  // the drawer's navigation watcher never fires. Close it here too.
  if (props.mobile) {
    mobileSidebarOpened.value = false
  }
}

watch(
  () => [route.name, route.query.view],
  () => (activeItem.value = currentRouteKey()),
)

function onSearchClick() {
  if (props.mobile) closeMobileSidebar(openCommandPalette)
  else openCommandPalette()
}

function onFlowClick() {
  if (props.mobile) closeMobileSidebar(() => window.flow.toggle())
  else window.flow.toggle()
}

function onNotificationsClick(event) {
  if (props.mobile) {
    selectItem(event, 'Notifications')
  } else {
    toggleNotificationPanel()
  }
}
</script>
