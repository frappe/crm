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
        v-if="hierarchyEnabled"
        class="flex item-center space-x-2 w-3/12 justify-end"
      >
        <Button
          :label="__('Add User')"
          icon-left="plus"
          variant="solid"
          @click="openAddDialog(null)"
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
        class="absolute left-1/2 flex w-72 -translate-x-1/2 flex-col items-center gap-3"
        :style="{ top: '25%' }"
      >
        <FeatherIcon name="git-branch" class="size-7.5 text-ink-gray-5" />
        <div class="flex flex-col items-center gap-1.5 text-center">
          <span class="text-lg font-medium text-ink-gray-8">
            {{ __('Enable Sales Hierarchy') }}
          </span>
          <span class="text-center text-p-base text-ink-gray-6">
            {{
              __(
                'Restrict lead and deal visibility based on a reporting tree. Managers will see all records owned by or assigned to their reports.',
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
      class="flex-1 overflow-y-auto rounded-l bg-surface-white p-3 mx-2 min-h-72"
    >
      <div v-if="nodes.loading" class="flex items-center justify-center py-12">
        <LoadingIndicator class="size-6" />
      </div>
      <div
        v-else-if="!visibleRoots.length"
        class="flex flex-col items-center justify-center py-12 text-ink-gray-5"
      >
        <FeatherIcon name="users" class="size-8 mb-2" />
        <p class="text-p-base">
          {{
            search || roleFilter !== 'All'
              ? __('No users match the current filter.')
              : __('No users in the hierarchy yet. Add one to get started.')
          }}
        </p>
      </div>
      <Tree
        v-for="root in visibleRoots"
        :key="`${root.name}-${treeKey}`"
        :node="root"
        node-key="name"
        :options="treeOptions"
      >
        <template #node="{ node, hasChildren, isCollapsed, toggleCollapsed }">
          <HierarchyNodeRow
            :node="node"
            :has-children="hasChildren"
            :is-collapsed="isCollapsed"
            :row-class="rowClasses(node)"
            :handlers="dragHandlers"
            @toggle="toggleCollapsed"
            @add="openAddDialog"
            @remove="removeNode"
            @move-to-root="(n) => reparent(n.name, null)"
          />
        </template>
      </Tree>
    </div>

    <Dialog
      v-model="showAddDialog"
      :options="{
        title: dialogTitle,
        actions: [
          {
            label: __('Add to tree'),
            variant: 'solid',
            disabled: !selectedUser || !!rankWarning,
            loading: saving,
            onClick: confirmAdd,
          },
        ],
      }"
    >
      <template #body-content>
        <div v-if="addParent" class="mb-3 text-p-sm text-ink-gray-6">
          {{ __('Will report to') }}
          <span class="font-medium text-ink-gray-8">{{
            addParent.full_name
          }}</span>
        </div>
        <Autocomplete
          v-model="selectedUser"
          :options="candidateUsers"
          :placeholder="__('Pick a user…')"
        />
        <div
          v-if="selectedUser && rankWarning"
          class="mt-3 p-2 rounded-md bg-surface-red-1 text-p-sm text-ink-red-4"
        >
          {{ rankWarning }}
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
import HierarchyNodeRow from './HierarchyNodeRow.vue'
import { useRemoveNode } from './useRemoveNode'
import { useDragDrop } from './useDragDrop'
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import {
  Button,
  Dialog,
  FeatherIcon,
  LoadingIndicator,
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

const { users: usersResource, getUserRole } = usersStore()
const { $dialog } = globalStore()

const fcrmSettings = createDocumentResource({
  doctype: 'FCRM Settings',
  name: 'FCRM Settings',
  auto: true,
  setValue: {
    onError(error) {
      toast.error(error?.messages?.[0] || __('Failed to update setting.'))
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
                onSuccess: () => toast.success(__('Sales Hierarchy disabled.')),
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
      { onSuccess: () => toast.success(__('Sales Hierarchy enabled.')) },
    )
  }
}

const search = ref('')
const roleFilter = ref('All')
const treeKey = ref(0)
const showAddDialog = ref(false)
const addParent = ref(null)
const selectedUser = ref(null)
const saving = ref(false)

const treeOptions = computed(() => ({
  rowHeight: '32px',
  indentWidth: '18px',
  showIndentationGuides: true,
}))

function enrich(node) {
  const user =
    usersResource.data?.allUsers?.find((x) => x.name === node.user) || {}
  const role = getUserRole(node.user) || 'Sales User'
  return {
    ...node,
    full_name: user.full_name || node.full_name || node.user,
    email: user.email || node.user,
    user_image: user.user_image,
    enabled: user.enabled !== 0,
    role,
    role_label: ROLE_LABEL[role] || role,
    role_rank: ROLE_RANK[role] ?? 4,
  }
}

const enrichedNodes = computed(() => (nodes.data || []).map(enrich))

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
  const children = (node.children || [])
    .map(clearTree)
    .filter((c) => c !== null)
  if (matchesFilters(node) || children.length) {
    return { ...node, children }
  }
  return null
}

const visibleRoots = computed(() =>
  tree.value.map(clearTree).filter((n) => n !== null),
)

const placedUserIds = computed(
  () => new Set(enrichedNodes.value.map((n) => n.user)),
)

const ALLOWED_ROLES = new Set(['Sales Manager', 'Sales User'])

const candidateUsers = computed(() => {
  const all = usersResource.data?.crmUsers || []
  return all
    .filter(
      (u) =>
        !placedUserIds.value.has(u.name) &&
        u.name !== 'Administrator' &&
        ALLOWED_ROLES.has(getUserRole(u.name)),
    )
    .map((u) => ({
      label: `${u.full_name} · ${u.email || u.name}`,
      value: u.name,
    }))
})

const rankWarning = computed(() => {
  if (!selectedUser.value || !addParent.value) return null
  const role = getUserRole(selectedUser.value.value) || 'Sales User'
  const childRank = ROLE_RANK[role] ?? 99
  if (childRank < addParent.value.role_rank) {
    return __('A {0} cannot report to a {1}.', [
      ROLE_LABEL[role],
      addParent.value.role_label,
    ])
  }
  return null
})

const dialogTitle = computed(() =>
  addParent.value ? __('Add direct report') : __('Add User'),
)

async function reparent(name, newParent) {
  try {
    await call('frappe.client.set_value', {
      doctype: DOCTYPE,
      name,
      fieldname: 'reports_to',
      value: newParent || '',
    })
    toast.success(__('Updated reports-to.'))
    nodes.reload()
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not update.'))
  }
}

function openAddDialog(parent) {
  addParent.value = parent
  selectedUser.value = null
  showAddDialog.value = true
}

async function confirmAdd() {
  if (!selectedUser.value || rankWarning.value) return
  saving.value = true
  try {
    await call('frappe.client.insert', {
      doc: {
        doctype: DOCTYPE,
        user: selectedUser.value.value,
        reports_to: addParent.value ? addParent.value.name : null,
        is_group: 0,
      },
    })
    toast.success(__('Added to hierarchy.'))
    showAddDialog.value = false
    nodes.reload()
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not add user.'))
  } finally {
    saving.value = false
  }
}

const { removeNode } = useRemoveNode({
  doctype: DOCTYPE,
  nodes,
  enrichedNodes,
})

const { handlers: dragHandlers, rowClasses } = useDragDrop({
  onReparent: reparent,
})
</script>
