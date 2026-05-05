<template>
  <div class="flex h-full flex-col gap-4 p-6 text-ink-gray-8">
    <div class="flex justify-between px-2 pt-2">
      <div class="flex flex-col gap-1 w-9/12">
        <h2 class="flex gap-2 text-xl font-semibold leading-none h-5">
          {{ __('User Hierarchy') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Arrange users into a reporting tree. Drag a user onto another to make them a direct report.',
            )
          }}
        </p>
      </div>
      <div
        v-if="hierarchyEnabled && canEdit"
        class="flex item-center space-x-2 w-3/12 justify-end"
      >
        <Button
          :label="__('Add User')"
          icon-left="plus"
          variant="solid"
          @click="openAddDialog()"
        />
      </div>
    </div>

    <div
      v-if="fcrmSettings.loading && !fcrmSettings.doc"
      class="flex flex-1 items-center justify-center"
    >
      <LoadingIndicator class="size-6" />
    </div>

    <div
      v-else-if="!hierarchyEnabled"
      class="relative flex flex-1 w-full justify-center"
    >
      <div
        class="absolute left-1/2 flex w-64 -translate-x-1/2 flex-col items-center gap-3"
        :style="{ top: '35%' }"
      >
        <lucide-network class="size-7.5 text-ink-gray-5" />
        <div class="flex flex-col items-center gap-1.5 text-center">
          <span class="text-lg font-medium text-ink-gray-8">
            {{ __('Enable Sales Hierarchy') }}
          </span>
          <span class="text-center text-p-base text-ink-gray-6">
            {{
              __(
                'Restrict visibility using a reporting tree. Managers can see records owned by their team.',
              )
            }}
          </span>
          <Button
            variant="solid"
            :loading="fcrmSettings.setValue.loading"
            @click="toggleEnable(false)"
          >
            {{ __('Enable') }}
          </Button>
        </div>
      </div>
    </div>

    <div
      v-else
      class="flex-1 min-h-0 flex flex-col rounded-l bg-surface-white mx-2 px-0.5"
    >
      <div
        class="flex items-center gap-2 pt-2 pb-3 sticky top-0 z-10 bg-surface-white"
      >
        <TextInput
         v-if="visibleRoots.length"
          v-model="search"
          :placeholder="__('Search users')"
          :debounce="200"
          class="flex-1"
        >
          <template #prefix>
            <FeatherIcon name="search" class="size-4 text-ink-gray-5" />
          </template>
        </TextInput>
        <Button
          v-if="isExpandable"
          :label="collapsed ? __('Expand') : __('Collapse')"
          @click="toggleCollapseAll"
        />
      </div>
      <div class="flex-1 min-h-0 overflow-y-auto">
        <div
          v-if="nodes.loading"
          class="flex items-center justify-center py-12"
        >
          <LoadingIndicator class="size-6" />
        </div>
        <EmptyState
          v-else-if="!visibleRoots.length"
          name="Users in Hierarchy"
          :title="
            search || roleFilter !== 'All'
              ? __('No matching users')
              : __('No users in hierarchy')
          "
          :description="
            search || roleFilter !== 'All'
              ? __('No users match the current filter.')
              : __('Add one to get started.')
          "
          icon="users"
        />
        <Tree
          v-for="root in visibleRoots"
          :key="`${root.name}-${treeKey}`"
          :node="root"
          node-key="name"
          :options="treeOptions"
        >
          <template #node="{ node, hasChildren, isCollapsed, toggleCollapsed }">
            <HierarchyRow
              :node="node"
              :has-children="hasChildren"
              :is-collapsed="isCollapsed"
              :row-class="rowClasses(node)"
              :handlers="dragHandlers"
              :get-candidates="getCandidates"
              :can-edit="canEdit"
              @toggle="toggleCollapsed"
              @bulk-add="({ parent, userIds }) => bulkAdd(parent, userIds)"
              @remove="({ node: n, mode }) => removeNode(n, mode)"
              @move-to-root="(n) => reparent(n.name, null)"
            />
          </template>
        </Tree>
      </div>
    </div>

    <Teleport to="body">
      <div
        v-if="dragLabel"
        class="fixed pointer-events-none px-2 py-1 rounded-md bg-gray-900 text-white text-xs shadow-lg"
        :style="{
          top: `${dragState.y + 25}px`,
          left: `${dragState.x - 25}px`,
        }"
      >
        {{ dragLabel }}
      </div>
    </Teleport>
    <Dialog
      v-model="showAddDialog"
      :options="{
        title: __('Add Users'),
        actions: [
          {
            label: __('Add ({0})', [dialogSelected.length]),
            variant: 'solid',
            disabled: !dialogSelected.length,
            loading: saving,
            onClick: confirmBulkAdd,
          },
        ],
      }"
    >
      <template #body-content>
        <UserMultiSelect
          v-model="dialogSelected"
          :candidates="getCandidates(null)"
        />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import EmptyState from '@/components/ListViews/EmptyState.vue'
import HierarchyRow from './HierarchyRow.vue'
import UserMultiSelect from './UserMultiSelect.vue'
import { useRemoveNode } from './useRemoveNode'
import { useDragDrop } from './useDragDrop'
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import LucideNetwork from '~icons/lucide/network'
import {
  Button,
  Dialog,
  FeatherIcon,
  LoadingIndicator,
  TextInput,
  Tree,
  call,
  createDocumentResource,
  createListResource,
  toast,
} from 'frappe-ui'
import { computed, ref } from 'vue'

const DOCTYPE = 'CRM Sales Hierarchy'

const ROLE_RANK = {
  'Sales Manager': 0,
  'Sales User': 1,
}
const ROLE_LABEL = {
  'Sales Manager': __('Sales Manager'),
  'Sales User': __('Sales User'),
}

const { users: usersResource, getUserRole, isAdmin } = usersStore()
const canEdit = computed(() => isAdmin())
const { $dialog } = globalStore()

const fcrmSettings = createDocumentResource({
  doctype: 'FCRM Settings',
  name: 'FCRM Settings',
  auto: true,
  setValue: {
    onError(error) {
      toast.error(error?.messages?.[0] || __('Failed to update setting'))
    },
  },
})

const hierarchyEnabled = computed(
  () => !!fcrmSettings.doc?.enable_sales_hierarchy,
)

const nodes = createListResource({
  doctype: DOCTYPE,
  fields: ['name', 'user', 'full_name', 'reports_to', 'is_group'],
  orderBy: 'lft asc',
  pageLength: 0,
  auto: true,
})

function toggleEnable(currentlyEnabled) {
  if (currentlyEnabled) {
    $dialog({
      title: __('Disable Sales Hierarchy'),
      message: __(
        'Lead and deal visibility will no longer be restricted by the reporting tree. Are you sure?',
      ),
      actions: [
        {
          label: __('Disable'),
          variant: 'solid',
          theme: 'red',
          onClick: ({ close }) => {
            fcrmSettings.setValue.submit(
              { enable_sales_hierarchy: 0 },
              {
                onSuccess: () => toast.success(__('Sales Hierarchy disabled')),
              },
            )
            close()
          },
        },
      ],
    })
  } else {
    fcrmSettings.setValue.submit(
      { enable_sales_hierarchy: 1 },
      { onSuccess: () => toast.success(__('Sales Hierarchy enabled')) },
    )
  }
}

const search = ref('')
const roleFilter = ref('All')
const treeKey = ref(0)
const collapsed = ref(false)
const showAddDialog = ref(false)
const dialogSelected = ref([])
const saving = ref(false)

const treeOptions = computed(() => ({
  rowHeight: '32px',
  indentWidth: '18px',
  defaultCollapsed: collapsed.value,
}))

function toggleCollapseAll() {
  collapsed.value = !collapsed.value
  treeKey.value++
}

function enrich(node) {
  const user =
    usersResource.data?.crmUsers?.find((x) => x.name === node.user) || {}
  const role = getUserRole(node.user) || 'Sales User'
  const role_rank = ROLE_RANK[role]
  if (role_rank == undefined) return

  return {
    ...node,
    full_name: user.full_name || node.full_name || node.user,
    email: user.email || node.user,
    user_image: user.user_image,
    enabled: user.enabled !== 0,
    role,
    role_label: ROLE_LABEL[role] || role,
    role_rank,
  }
}

const enrichedNodes = computed(() =>
  (nodes.data || []).map(enrich).filter(Boolean),
)

const tree = computed(() => {
  const byName = new Map(
    enrichedNodes.value.map((n) => [n.name, { ...n, children: [] }]),
  )
  const roots = []
  for (const n of byName.values()) {
    if (n.reports_to && byName.has(n.reports_to)) {
      byName.get(n.reports_to).children.push(n)
    } else {
      roots.push(n)
    }
  }
  return roots
})

function matchesFilters(node) {
  const query = search.value.trim().toLowerCase()
  const matchSearch =
    !query ||
    node.full_name?.toLowerCase().includes(query) ||
    node.email?.toLowerCase().includes(query)
  const matchRole = roleFilter.value === 'All' || node.role === roleFilter.value
  return matchSearch && matchRole
}

function clearTree(node) {
  if (matchesFilters(node)) {
    return { ...node, children: node.children || [] }
  }
  const children = (node.children || [])
    .map(clearTree)
    .filter((c) => c !== null)
  if (children.length) {
    return { ...node, children }
  }
  return null
}

const visibleRoots = computed(() =>
  tree.value.map(clearTree).filter((n) => n !== null),
)

const isExpandable = computed(() =>
  visibleRoots.value.some((n) => n.children?.length),
)

const placedUserIds = computed(
  () => new Set(enrichedNodes.value.map((n) => n.user)),
)

const ALLOWED_ROLES = new Set(['Sales Manager', 'Sales User'])

function getCandidates(parent) {
  const all = usersResource.data?.crmUsers || []
  const parentRank = parent?.role_rank ?? -1
  return all
    .filter((u) => {
      if (placedUserIds.value.has(u.name)) return false
      if (u.name === 'Administrator') return false
      const role = getUserRole(u.name)
      if (!ALLOWED_ROLES.has(role)) return false
      return (ROLE_RANK[role] ?? 99) >= parentRank
    })
    .map((u) => ({
      value: u.name,
      full_name: u.full_name || u.name,
      email: u.email || u.name,
      user_image: u.user_image,
    }))
}

async function reparent(name, newParent) {
  try {
    await call('frappe.client.set_value', {
      doctype: DOCTYPE,
      name,
      fieldname: 'reports_to',
      value: newParent || '',
    })
    toast.success(__('Updated reports to'))
    nodes.reload()
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not update report to'))
  }
}

function openAddDialog() {
  dialogSelected.value = []
  showAddDialog.value = true
}

async function bulkAdd(parent, userIds) {
  if (!userIds?.length) return false
  saving.value = true
  let added = 0
  let lastError = null
  try {
    for (const user of userIds) {
      try {
        await call('frappe.client.insert', {
          doc: {
            doctype: DOCTYPE,
            user,
            reports_to: parent ? parent.name : null,
            is_group: 0,
          },
        })
        added++
      } catch (e) {
        lastError = e
      }
    }
    if (added) {
      toast.success(
        added === 1
          ? __('User added to hierarchy')
          : __('{0} users added to hierarchy', [added]),
      )
    }
    if (lastError) {
      toast.error(
        lastError?.messages?.[0] || __('Some users could not be added'),
      )
    }
    await nodes.reload()
    return added > 0 && !lastError
  } finally {
    saving.value = false
  }
}

async function confirmBulkAdd() {
  const ok = await bulkAdd(null, dialogSelected.value)
  if (ok) {
    showAddDialog.value = false
    dialogSelected.value = []
  }
}

const { removeNode } = useRemoveNode({
  doctype: DOCTYPE,
  nodes,
  enrichedNodes,
})

const {
  handlers: dragHandlers,
  rowClasses,
  dragState,
  dragLabel,
} = useDragDrop({
  onReparent: reparent,
})
</script>
