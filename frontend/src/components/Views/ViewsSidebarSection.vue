<template>
  <div v-if="allViews">
    <Draggable
      v-if="editSidebar"
      :list="allViews"
      item-key="name"
      :delay="isTouchScreenDevice() ? 200 : 0"
      :group="{ name: 'view-sections', pull: false, put: false }"
      handle=".section-drag-handle"
      class="flex flex-col"
      ghost-class="opacity-70"
    >
      <template #item="{ element: view }">
        <div :key="view.name">
          <div
            v-if="!view.hideLabel && isSidebarCollapsed && view.views?.length"
            class="mx-2 my-2 h-1 border-b"
          />
          <CollapsibleSection
            :label="view.label"
            :hideLabel="view.hideLabel"
            :opened="view.opened"
          >
            <template #header="{ opened, hide, toggle }">
              <div
                v-if="!hide"
                class="group my-2 flex gap-2 min-h-7 items-center justify-between px-1 text-base font-medium text-ink-gray-5 transition-all duration-300 ease-in-out truncate"
                :class="{ 'bg-surface-gray-1': isSectionDropdownOpen(view.name) }"
              >
                <div
                  class="flex ml-2 h-7 cursor-pointer items-center gap-1.5 transition-all duration-300 ease-in-out truncate"
                  @click="toggle()"
                >
                  <FeatherIcon
                    name="chevron-right"
                    class="h-4 text-ink-gray-9 transition-all duration-300 ease-in-out"
                    :class="{ 'rotate-90': opened }"
                  />
                  <Tooltip :text="view.label">
                    <span class="truncate">{{ __(view.label) }}</span>
                  </Tooltip>
                </div>
                <div
                  class="flex items-center gap-1 mr-1 transition-[width,opacity] flex-shrink-0"
                  :class="[
                    isSectionDropdownOpen(view.name)
                      ? 'w-auto opacity-100 pointer-events-auto'
                      : 'w-0 overflow-hidden opacity-0 pointer-events-none group-hover:w-auto group-hover:opacity-100 group-hover:pointer-events-auto'
                  ]"
                >
                  <Button
                    variant="ghost"
                    class="!size-5.5 !p-1 cursor-grab section-drag-handle shrink-0"
                    @click.stop
                  >
                    <DragIcon class="size-3.5" />
                  </Button>
                  <Dropdown
                    placement="right"
                    :options="sectionOptions(view)"
                  >
                    <template #default="slotProps">
                      <Button
                        v-bind="slotProps"
                        variant="ghost"
                        class="!size-5.5 !p-1 cursor-pointer shrink-0"
                        icon="more-horizontal"
                        @click.stop
                        :data-open="syncSectionDropdown(view.name, slotProps.open)"
                      />
                    </template>
                  </Dropdown>
                </div>
              </div>
            </template>
            <nav class="flex flex-col">
              <Draggable
                :list="view.views"
                @end="apply"
                :delay="isTouchScreenDevice() ? 200 : 0"
                :group="{ name: 'views-items', pull: true, put: true }"
                handle=".item-drag-handle"
                item-key="name"
                class="list-group flex flex-col gap-1 mx-2 my-0.5"
              >
                <template #item="{ element: link }">
                  <div
                    class="group w-full flex justify-between gap-2 h-7 px-2 py-1 cursor-pointer items-center rounded text-ink-gray-7 transition-all duration-300 ease-in-out focus:outline-none focus:transition-none focus-visible:rounded focus-visible:ring-2 focus-visible:ring-outline-gray-3 hover:bg-surface-gray-2"
                    :class="{ 'bg-surface-gray-2': isItemDropdownOpen(link.name) }"
                  >
                    <div class="flex items-center truncate">
                      <Icon :icon="link.icon" class="size-4" />
                      <Tooltip :text="link.label" :hoverDelay="1.5">
                        <span
                          class="ml-2 flex-1 flex-shrink-0 truncate text-sm duration-300 ease-in-out"
                        >
                          {{ __(link.label) }}
                        </span>
                      </Tooltip>
                    </div>
                    <div
                      class="flex items-center gap-1 transition-[width,opacity] flex-shrink-0"
                      :class="[
                        isItemDropdownOpen(link.name)
                          ? 'w-auto opacity-100 pointer-events-auto'
                          : 'w-0 overflow-hidden opacity-0 pointer-events-none group-hover:w-auto group-hover:opacity-100 group-hover:pointer-events-auto'
                      ]"
                    >
                      <Button
                        variant="ghost"
                        class="!size-5.5 !p-1 cursor-grab item-drag-handle shrink-0"
                      >
                        <template #default>
                          <DragIcon class="size-3.5" />
                        </template>
                      </Button>
                      <Dropdown
                        placement="right"
                        :options="viewOptions(link)"
                      >
                        <template #default="slotProps">
                          <Button
                            v-bind="slotProps"
                            variant="ghost"
                            class="!size-5.5 !p-1 cursor-pointer shrink-0"
                            icon="more-horizontal"
                            @click.stop
                            :data-open="syncItemDropdown(link.name, slotProps.open)"
                          />
                        </template>
                      </Dropdown>
                    </div>
                  </div>
                </template>
              </Draggable>
            </nav>
          </CollapsibleSection>
        </div>
      </template>
    </Draggable>
    <template v-else>
      <div v-for="view in allViews" :key="view.name">
        <div
          v-if="!view.hideLabel && isSidebarCollapsed && view.views?.length"
          class="mx-2 my-2 h-1 border-b"
        />
        <CollapsibleSection
          :label="view.label"
          :hideLabel="view.hideLabel"
          :opened="view.opened"
        >
          <template #header="{ opened, hide, toggle }">
            <div
              v-if="!hide"
              class="flex items-center cursor-pointer gap-1.5 px-1 text-base font-medium text-ink-gray-5 transition-all duration-300 ease-in-out"
              :class="
                isSidebarCollapsed
                  ? 'ml-0 h-0 overflow-hidden opacity-0'
                  : 'ml-2 my-2 h-7 w-auto opacity-100'
              "
              @click="toggle()"
            >
              <FeatherIcon
                name="chevron-right"
                class="h-4 text-ink-gray-9 transition-all duration-300 ease-in-out"
                :class="{ 'rotate-90': opened }"
              />
              <Tooltip :text="view.label" placement="right">
                <span class="truncate">{{ __(view.label) }}</span>
              </Tooltip>
            </div>
          </template>
          <nav class="flex flex-col">
            <SidebarLink
              v-for="link in view.views"
              :key="link.name"
              :icon="link.icon"
              :label="__(link.label)"
              :to="link.to"
              :isCollapsed="isSidebarCollapsed"
              class="mx-2 my-0.5"
            />
          </nav>
        </CollapsibleSection>
      </div>
    </template>
  </div>
</template>

<script setup>
import Icon from '@/components/Icon.vue'
import DragIcon from '@/components/Icons/DragIcon.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import DuplicateIcon from '@/components/Icons/DuplicateIcon.vue'
import CollapsibleSection from '@/components/CollapsibleSection.vue'
import LucideLayoutDashboard from '~icons/lucide/layout-dashboard'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import PinIcon from '@/components/Icons/PinIcon.vue'
import SidebarLink from '@/components/SidebarLink.vue'
import Draggable from 'vuedraggable'
import { useViews } from '@/stores/view'
import { sidebarLayouts } from '@/doctype/generateRoutes.js'
import { editSidebar } from '@/composables/settings.js'
import { isTouchScreenDevice } from '@/utils'
import { Tooltip, FeatherIcon, Dropdown } from 'frappe-ui'
import { computed, h, reactive, ref, watch } from 'vue'

defineProps({
  isSidebarCollapsed: {
    type: Boolean,
    required: true,
  },
})

const { pinnedViews, publicViews } = useViews()

const sectionDropdownState = reactive({})
const itemDropdownState = reactive({})

const iconMap = {
  Dashboard: LucideLayoutDashboard,
  Leads: LeadsIcon,
  Deals: DealsIcon,
  Contacts: ContactsIcon,
  Organizations: OrganizationsIcon,
  Notes: NoteIcon,
  Tasks: TaskIcon,
  Calendar: CalendarIcon,
  'Call Logs': PhoneIcon,
}

const links = computed(() => {
  const staticLinks = Object.keys(iconMap).map((key) => {
    return {
      name: key,
      label: key,
      icon: iconMap[key],
      to: key,
    }
  })

  if (!sidebarLayouts.value?.length) {
    return staticLinks
  }

  return sidebarLayouts.value.map((link) => {
    return {
      name: link.routeName || link.doctype || link.label,
      label: link.label || link.doctype || link.routeName,
      icon: iconMap[link.label || link.routeName] || link.icon,
      to: link.routeName || link.doctype + ' List',
    }
  })
})

const baseViewGroups = computed(() => {
  const viewGroups = [
    {
      name: 'all-views',
      label: __('All Views'),
      hideLabel: true,
      opened: true,
      views: links.value.filter((link) => {
        if (link.condition) {
          return link.condition()
        }
        return true
      }),
    },
  ]

  if (publicViews.value?.length) {
    viewGroups.push({
      name: 'public-views',
      label: __('Public Views'),
      opened: true,
      views: parseView(publicViews.value),
    })
  }

  if (pinnedViews.value?.length) {
    viewGroups.push({
      name: 'pinned-views',
      label: __('Pinned Views'),
      opened: true,
      views: parseView(pinnedViews.value),
    })
  }

  return viewGroups
})

const allViews = ref([])

watch(
  baseViewGroups,
  (groups) => {
    allViews.value = cloneGroups(groups)
  },
  { immediate: true, deep: true },
)

function isSectionDropdownOpen(name) {
  return !!sectionDropdownState[name]
}

function isItemDropdownOpen(name) {
  return !!itemDropdownState[name]
}

function syncSectionDropdown(name, open) {
  if (open) {
    sectionDropdownState[name] = true
  } else {
    delete sectionDropdownState[name]
  }
  return open
}

function syncItemDropdown(name, open) {
  if (open) {
    itemDropdownState[name] = true
  } else {
    delete itemDropdownState[name]
  }
  return open
}

function parseView(views) {
  return views.map((view) => {
    return {
      name: view.name || view.route_name,
      label: view.label,
      icon: getIcon(view.route_name, view.icon),
      to: {
        name: view.route_name,
        params: { viewName: view.name },
      },
    }
  })
}

function getIcon(routeName, icon) {
  if (icon) {
    return h('div', { class: 'size-auto' }, icon)
  }

  return iconMap[routeName] || PinIcon
}

function cloneGroups(groups) {
  return groups.map((group) => ({
    ...group,
    views: group.views?.map((view) => ({ ...view })) || [],
  }))
}

function viewOptions(link) {
  return [
    {
      label: __('Edit'),
      icon: () => h(EditIcon, { class: 'h-4 w-4' }),
      onClick: () => {
        /* Placeholder for edit action */
      },
    },
    {
      label: __('Duplicate'),
      icon: () => h(DuplicateIcon, { class: 'h-4 w-4' }),
      onClick: () => {
        /* Placeholder for duplicate action */
      },
    },
    {
      label: __('Add below'),
      icon: 'plus',
      onClick: () => {
        /* Placeholder for edit action */
      },
    },
    {
      group: __('Delete View'),
      hideLabel: true,
      items: [
        {
          label: __('Delete'),
          icon: 'trash-2',
          onClick: () => {
            /* Placeholder for delete action */
          },
        },
      ],
    },
  ]
}

function sectionOptions(section) {
  return [
    {
      label: __('Rename'),
      icon: 'edit-2',
      onClick: () => {
        /* Placeholder for rename action */
      },
    },
    {
      label: __('Hide section'),
      icon: 'eye-off',
      onClick: () => {
        /* Placeholder for hide action */
      },
    },
    {
      group: __('Delete Section'),
      hideLabel: true,
      items: [
        {
          label: __('Delete'),
          icon: 'trash-2',
          onClick: () => {
            /* Placeholder for delete action */
          },
        },
      ],
    },
  ]
}

function resetSidebar() {
  editSidebar.value = false
  allViews.value = cloneGroups(baseViewGroups.value)
}

function saveSidebar() {
  editSidebar.value = false
}

function apply() {
  // Placeholder for any action needed after drag-and-drop
}

defineExpose({
  resetSidebar,
  saveSidebar,
})
</script>
