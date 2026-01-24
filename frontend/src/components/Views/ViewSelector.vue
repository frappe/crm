<template>
  <Dropdown v-if="currentView" :options="viewsDropdownOptions">
    <template #default="{ open }">
      <Button
        variant="ghost"
        class="text-lg font-medium text-nowrap"
        :label="__(currentView.label)"
        :iconRight="open ? 'chevron-up' : 'chevron-down'"
      >
        <template #prefix>
          <Icon :icon="getIcon(currentView.icon || ListIcon)" class="h-4" />
        </template>
      </Button>
    </template>
    <template #item="{ item, close }">
      <button
        class="group flex text-ink-gray-6 gap-4 h-7 w-full justify-between items-center rounded px-2 text-base hover:bg-surface-gray-3"
        @click="item.onClick"
      >
        <div class="flex items-center">
          <Icon :icon="getIcon(item.icon || ListIcon)" class="h-4 mr-2" />
          <span class="whitespace-nowrap">
            {{ item.label }}
          </span>
        </div>
        <div
          v-if="item.name"
          class="flex flex-row-reverse gap-2 items-center min-w-11"
        >
          <Dropdown
            side="right"
            :offset="15"
            :options="viewActions(item, close)"
          >
            <template #default>
              <Button
                variant="ghost"
                class="!size-5 opacity-0 group-hover:opacity-100 pointer-events-none group-hover:pointer-events-auto transition-opacity"
                icon="more-horizontal"
                @click.stop
              />
            </template>
          </Dropdown>
          <FeatherIcon
            v-if="isCurrentView(item)"
            name="check"
            class="size-4 text-ink-gray-7"
          />
        </div>
      </button>
    </template>
  </Dropdown>
  <ViewModal
    v-if="showViewModal"
    v-model="showViewModal"
    v-model:view="view"
    :mode="mode"
  />
</template>
<script setup>
import ViewModal from '@/components/Views/ViewModal.vue'
import ListIcon from '@/components/Icons/ListIcon.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import DuplicateIcon from '@/components/Icons/DuplicateIcon.vue'
import PinIcon from '@/components/Icons/PinIcon.vue'
import UnpinIcon from '@/components/Icons/UnpinIcon.vue'
import Icon from '@/components/Icon.vue'
import { usersStore } from '@/stores/users'
import { useViews } from '@/stores/view'
import { globalStore } from '@/stores/global'
import { isEmoji } from '@/utils'
import { Dropdown, FeatherIcon, call } from 'frappe-ui'
import { computed, markRaw, ref, h, inject } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const currentView = inject('currentView')

const { $dialog } = globalStore()
const { isManager } = usersStore()

const { reloadViews, allViews } = useViews()

const route = useRoute()
const router = useRouter()

const standardViews = []

const viewsDropdownOptions = computed(() => {
  let _views = [
    {
      group: __('Standard views'),
      hideLabel: true,
      items: standardViews,
    },
  ]

  if (allViews.value?.length) {
    allViews.value.forEach((v) => {
      v.label = __(v.label)
      v.type = v.type || 'list'
      v.filters =
        typeof v.filters == 'string' ? JSON.parse(v.filters) : v.filters
      v.onClick = () => {
        router.push({
          name: v.route_name,
          params: { viewName: v.name },
        })
      }
    })
    let publicViews = allViews.value.filter((v) => v.public)
    let savedViews = allViews.value.filter(
      (v) => !v.pinned && !v.public && !v.is_standard,
    )
    let pinnedViews = allViews.value.filter((v) => v.pinned)
    savedViews.length &&
      _views.push({
        group: __('Saved views'),
        items: savedViews,
      })
    publicViews.length &&
      _views.push({
        group: __('Public views'),
        items: publicViews,
      })
    pinnedViews.length &&
      _views.push({
        group: __('Pinned views'),
        items: pinnedViews,
      })
  }

  _views.push({
    group: __('Actions'),
    hideLabel: true,
    items: [
      {
        label: __('Create view'),
        icon: 'plus',
        onClick: () => createView(),
      },
    ],
  })

  return _views
})

function getIcon(icon) {
  if (isEmoji(icon)) {
    return h('div', icon)
  }
  return icon || markRaw(ListIcon)
}

const isCurrentView = (item) => {
  return item.name === currentView.value?.name
}

// View Actions
const viewActions = (v, close) => {
  let actions = [
    {
      group: __('Actions'),
      hideLabel: true,
      items: [
        {
          label: __('Duplicate'),
          icon: () => h(DuplicateIcon, { class: 'h-4 w-4' }),
          onClick: () => duplicateView(v, close),
        },
      ],
    },
  ]

  // if (!isDefaultView(v, v.is_standard)) {
  //   actions[0].items.unshift({
  //     label: __('Set as default'),
  //     icon: () => h(CheckIcon, { class: 'h-4 w-4' }),
  //     onClick: () => setAsDefault(v),
  //   })
  // }

  if (!v.is_standard && (!v.public || isManager())) {
    actions[0].items.push({
      label: __('Edit'),
      icon: () => h(EditIcon, { class: 'h-4 w-4' }),
      onClick: () => editView(v, close),
    })

    if (!v.public) {
      actions[0].items.push({
        label: v.pinned ? __('Unpin view') : __('Pin view'),
        icon: () => h(v.pinned ? UnpinIcon : PinIcon, { class: 'h-4 w-4' }),
        onClick: () => pinView(v),
      })
    }

    if (isManager()) {
      actions[0].items.push({
        label: v.public ? __('Make private') : __('Make public'),
        icon: () =>
          h(FeatherIcon, {
            name: v.public ? 'lock' : 'unlock',
            class: 'h-4 w-4',
          }),
        onClick: () => publicView(v),
      })
    }

    actions.push({
      group: __('Delete view'),
      hideLabel: true,
      items: [
        {
          label: __('Delete'),
          icon: 'trash-2',
          onClick: () =>
            $dialog({
              title: __('Delete view'),
              message: __('Are you sure you want to delete "{0}" view?', [
                v.label,
              ]),
              variant: 'danger',
              actions: [
                {
                  label: __('Delete'),
                  variant: 'solid',
                  theme: 'red',
                  onClick: (close) => deleteView(v, close),
                },
              ],
            }),
        },
      ],
    })
  }
  return actions
}

const view = ref({})
const mode = ref('create')
const showViewModal = ref(false)

function createView() {
  view.value = currentView.value ? { ...currentView.value } : {}
  mode.value = 'create'
  view.value.name = ''
  view.value.label = ''
  view.value.icon = ''
  showViewModal.value = true
}

function editView(v, close) {
  view.value = { ...v }
  mode.value = 'edit'
  showViewModal.value = true
  close()
}

function duplicateView(v, close) {
  view.value = { ...v }
  mode.value = 'duplicate'
  view.value.name = ''
  view.value.label = `${v.label} ${__('(Copy)')}`
  showViewModal.value = true
  close()
}

function publicView(v) {
  call('crm.fcrm.doctype.crm_view_settings.crm_view_settings.public', {
    name: v.name,
    value: !v.public,
  }).then(() => {
    v.public = !v.public
    reloadViews()
  })
}

function pinView(v) {
  call('crm.fcrm.doctype.crm_view_settings.crm_view_settings.pin', {
    name: v.name,
    value: !v.pinned,
  }).then(() => {
    v.pinned = !v.pinned
    reloadViews()
  })
}

function deleteView(v, close) {
  call('crm.fcrm.doctype.crm_view_settings.crm_view_settings.delete', {
    name: v.name,
  }).then(() => {
    const firstMatchedRoute = route.matched?.[0]
    if (firstMatchedRoute) {
      router.push({ name: firstMatchedRoute.name })
    } else {
      router.push({ name: 'Home' })
    }
    reloadViews()
  })
  close()
}
</script>
