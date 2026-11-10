<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Contacts" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="contactsListView?.customListActions"
        :actions="contactsListView.customListActions"
      />
      <Button
        variant="solid"
        :label="__('Create')"
        iconLeft="lucide-plus"
        @click="showContactModal = true"
      />
    </template>
  </LayoutHeader>

  <!-- Contacts Categorization Tabs -->
  <div class="border-b border-outline-gray-2 bg-surface-base px-3 sm:px-5">
    <div class="flex items-center gap-6 overflow-x-auto">
      <button
        v-for="tab in tabs"
        :key="tab.value"
        type="button"
        class="flex items-center gap-2 border-b-2 py-3 text-sm font-medium transition-colors whitespace-nowrap focus:outline-none"
        :class="[
          activeTab === tab.value
            ? 'border-surface-gray-9 text-ink-gray-9 font-semibold dark:border-ink-white dark:text-ink-white'
            : 'border-transparent text-ink-gray-5 hover:text-ink-gray-8 dark:text-ink-gray-4 dark:hover:text-ink-white',
        ]"
        @click="setTab(tab.value)"
      >
        <span>{{ tab.label }}</span>
        <Badge
          variant="solid"
          size="sm"
          :class="[
            activeTab === tab.value
              ? 'bg-surface-gray-9 text-surface-white dark:bg-surface-gray-7 dark:text-ink-white'
              : 'bg-surface-gray-2 text-ink-gray-7 dark:bg-surface-gray-8 dark:text-ink-gray-3',
          ]"
        >
          {{ tab.count }}
        </Badge>
      </button>
    </div>
  </div>

  <ViewControls
    :key="activeTab"
    ref="viewControls"
    v-model="contacts"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    :filters="activeTabFilters"
    doctype="Contact"
  />
  <ContactsListView
    v-if="contacts.data && rows.length"
    :key="activeTab"
    ref="contactsListView"
    v-model="contacts.data.page_length_count"
    v-model:list="contacts"
    :currentTab="activeTab"
    :rows="rows"
    :columns="columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: contacts.data.row_count,
      totalCount: contacts.data.total_count,
    }"
    @reload="fetchTabCounts"
    @loadMore="() => loadMore++"
    @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)"
    @applyFilter="(data) => viewControls.applyFilter(data)"
    @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
    @likeDoc="(data) => viewControls.likeDoc(data)"
    @selectionsChanged="
      (selections) => viewControls.updateSelections(selections)
    "
  />
  <EmptyState
    v-else-if="contacts.data && !rows.length"
    name="Contacts"
    :icon="ContactsIcon"
    :title="__('No contacts yet')"
    :description="
      __(
        'Contacts are the people you talk to at your leads and customers. They are added when you convert a lead, or you can add them here.',
      )
    "
    :filtered="!!Object.keys(contacts.params?.filters || {}).length"
    docsLink="https://docs.frappe.io/crm/contact"
    importDoctype="Contact"
    @create="showContactModal = true"
  />
  <ContactModal
    v-if="showContactModal"
    v-model="showContactModal"
    :contact="{}"
  />
</template>

<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import CustomActions from '@/components/CustomActions.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ContactModal from '@/components/Modals/ContactModal.vue'
import ContactsListView from '@/components/ListViews/ContactsListView.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import ViewControls from '@/components/ViewControls.vue'
import { getMeta } from '@/stores/meta'
import { organizationsStore } from '@/stores/organizations.js'
import { sessionStore } from '@/stores/session'
import { usersStore } from '@/stores/users'
import { globalStore } from '@/stores/global'
import { formatDate } from '@/utils'
import { timestampCell } from '@/composables/useTimelinePreferences'
import { Badge, createResource } from 'frappe-ui'
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const { $socket } = globalStore()

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
  getMeta('Contact')
const { getOrganization } = organizationsStore()
const { user: currentSessionUser } = sessionStore()
const { getUser, isAdmin: checkIsAdmin } = usersStore()

const route = useRoute()
const router = useRouter()

const showContactModal = ref(false)
const contactsListView = ref(null)

// contacts data is loaded in the ViewControls component
const contacts = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

// 1. User role & permissions
const isAdmin = computed(() => {
  if (currentSessionUser === 'Administrator') return true
  const u = getUser(currentSessionUser)
  return (
    u?.role === 'System Manager' ||
    u?.role === 'Sales Manager' ||
    checkIsAdmin(currentSessionUser)
  )
})

// 2. Active Tab (default: unassigned)
const activeTab = ref(
  ['unassigned', 'assigned', 'dropped'].includes(route.query.tab)
    ? route.query.tab
    : 'unassigned',
)

watch(
  () => route.query.tab,
  (tab) => {
    if (tab && ['unassigned', 'assigned', 'dropped'].includes(tab) && activeTab.value !== tab) {
      activeTab.value = tab
      fetchTabCounts()
    }
  },
)

// 3. Dynamic Counts for the tabs
const tabCounts = ref({
  unassigned: 0,
  assigned: 0,
  dropped: 0,
})

const tabCountsResource = createResource({
  url: 'crm.api.contact.get_contact_tab_counts',
  auto: true,
  onSuccess: (data) => {
    if (data) {
      tabCounts.value = {
        unassigned: data.unassigned ?? 0,
        assigned: data.assigned ?? 0,
        dropped: data.dropped ?? 0,
      }
    }
  },
})

function fetchTabCounts() {
  tabCountsResource.reload()
}

function onContactsRealtimeUpdate() {
  fetchTabCounts()
  viewControls.value?.reload?.()
}

onMounted(() => {
  fetchTabCounts()
  if ($socket) {
    $socket.on('crm_tasks_updated', onContactsRealtimeUpdate)
  }
})

onBeforeUnmount(() => {
  if ($socket) {
    $socket.off('crm_tasks_updated', onContactsRealtimeUpdate)
  }
})

watch(
  () => contacts.value?.data,
  () => {
    fetchTabCounts()
  },
)

const tabs = computed(() => [
  {
    label: __('Unassigned'),
    value: 'unassigned',
    count: tabCounts.value.unassigned,
  },
  {
    label: __('Assigned'),
    value: 'assigned',
    count: tabCounts.value.assigned,
  },
  {
    label: __('Dropped'),
    value: 'dropped',
    count: tabCounts.value.dropped,
  },
])

function setTab(tab) {
  if (activeTab.value === tab) return
  activeTab.value = tab
  router.replace({ query: { ...route.query, tab } })
  fetchTabCounts()
  nextTick(() => {
    viewControls.value?.reload?.()
  })
}

// 4. Mutually exclusive active tab filters
const activeTabFilters = computed(() => {
  if (activeTab.value === 'assigned') {
    if (isAdmin.value) {
      return {
        _assign: ['is', 'set'],
        custom_is_dropped: 0,
      }
    } else {
      return {
        _assign: ['like', `%${currentSessionUser}%`],
        custom_is_dropped: 0,
      }
    }
  } else if (activeTab.value === 'dropped') {
    return {
      custom_is_dropped: 1,
    }
  } else {
    // Unassigned (default)
    return {
      _assign: ['is', 'not set'],
      custom_is_dropped: 0,
    }
  }
})

const rows = computed(() => {
  if (
    !contacts.value?.data?.data ||
    !['list', 'group_by'].includes(contacts.value.data.view_type)
  )
    return []
  return contacts.value?.data.data.map((contact) => {
    let _rows = {}
    contacts.value?.data.rows.forEach((row) => {
      _rows[row] = contact[row]

      let fieldType = contacts.value?.data.columns?.find(
        (col) => (col.key || col.value) == row,
      )?.type

      if (
        fieldType &&
        ['Date', 'Datetime'].includes(fieldType) &&
        !['modified', 'creation'].includes(row)
      ) {
        _rows[row] = formatDate(contact[row], '', true, fieldType == 'Datetime')
      }

      if (fieldType && fieldType == 'Currency') {
        _rows[row] = getFormattedCurrency(row, contact)
      }

      if (fieldType && fieldType == 'Float') {
        _rows[row] = getFormattedFloat(row, contact)
      }

      if (fieldType && fieldType == 'Percent') {
        _rows[row] = getFormattedPercent(row, contact)
      }

      if (row == 'full_name') {
        _rows[row] = {
          label: contact.full_name,
          image_label: contact.full_name,
          image: contact.image,
        }
      } else if (row == 'company_name') {
        _rows[row] = {
          label: contact.company_name,
          logo: getOrganization(contact.company_name)?.organization_logo,
        }
      } else if (row == '_assign') {
        let assignees = []
        try {
          assignees =
            typeof contact._assign === 'string'
              ? JSON.parse(contact._assign || '[]')
              : contact._assign || []
        } catch (e) {
          assignees = []
        }
        _rows[row] = (assignees || []).map((user) => ({
          name: user,
          image: getUser(user)?.user_image,
          label: getUser(user)?.full_name || user,
        }))
      } else if (['modified', 'creation'].includes(row)) {
        _rows[row] = timestampCell(contact[row])
      }
    })
    if (contact._assign && !_rows['_assign']) {
      let assignees = []
      try {
        assignees =
          typeof contact._assign === 'string'
            ? JSON.parse(contact._assign || '[]')
            : contact._assign || []
      } catch (e) {
        assignees = []
      }
      _rows['_assign'] = (assignees || []).map((user) => ({
        name: user,
        image: getUser(user)?.user_image,
        label: getUser(user)?.full_name || user,
      }))
    }
    return _rows
  })
})

const columns = computed(() => {
  let _columns = [...(contacts.value?.data?.columns || [])]

  if (activeTab.value === 'assigned') {
    if (!_columns.some((c) => (c.key || c.value) === '_assign')) {
      const assignCol = {
        label: __('Assigned To'),
        type: 'Data',
        key: '_assign',
        width: '13rem',
      }
      const lastIndex = _columns.findIndex(
        (c) => (c.key || c.value) === 'modified',
      )
      if (lastIndex !== -1) {
        _columns.splice(lastIndex, 0, assignCol)
      } else {
        _columns.push(assignCol)
      }
    }
  } else {
    _columns = _columns.filter((c) => (c.key || c.value) !== '_assign')
  }

  // Set align right for last column
  if (_columns.length) {
    _columns = _columns.map((col, index) => {
      if (index === _columns.length - 1) {
        return { ...col, align: 'right' }
      }
      return col
    })
  }

  return _columns
})
</script>
