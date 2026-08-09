<template>
  <div class="fc-crud-section">
    <!-- Breadcrumb trail + primary action -->
    <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
      <Breadcrumbs :items="breadcrumbs" />
      <div v-if="mode === 'list'" class="flex flex-wrap items-center gap-2">
        <!-- Create-From (mapped-doc) actions — visible-but-disabled without create
             permission, matching the New gate. -->
        <Button
          v-for="flow in createFrom"
          :key="flow.key"
          variant="outline"
          theme="gray"
          :disabled="!canCreate"
          :title="!canCreate ? 'You do not have permission to create' : ''"
          @click="canCreate && goCreateFrom(flow)"
        >
          <template #prefix><FcIcon name="copy-plus" :size="15" /></template>
          {{ flow.label }}
        </Button>
        <Button
          variant="solid"
          theme="blue"
          :disabled="!canCreate"
          :title="!canCreate ? 'You do not have permission to create' : ''"
          @click="canCreate && goNew()"
        >
          <template #prefix><FcIcon name="plus" :size="15" /></template>
          New
        </Button>
      </div>
    </div>

    <!-- LIST -->
    <template v-if="mode === 'list'">
      <div class="flex flex-wrap items-center gap-2 mb-3">
        <slot name="filters" />
      </div>

      <!-- Loading -->
      <div v-if="listLoading" class="space-y-2">
        <div v-for="n in 6" :key="n" class="h-11 bg-surface-gray-2 rounded-lg animate-pulse" />
      </div>

      <!-- Error -->
      <div v-else-if="listError" class="text-sm text-red-600 dark:text-red-400 py-6 text-center">
        Failed to load data.
        <button class="underline ml-1" @click="refetch">Retry</button>
      </div>

      <!-- Empty -->
      <div v-else-if="!rows.length" class="text-center py-12 text-sm text-ink-gray-4">
        {{ emptyLabel }}
      </div>

      <template v-else>
        <!-- Desktop: frappe-ui ListView -->
        <ListView
          v-if="!isMobile"
          :columns="listColumns"
          :rows="rows"
          row-key="name"
          :options="listOptions"
          class="fc-listview border border-outline-gray-1 rounded-lg"
        >
          <template #cell="{ item, row, column }">
            <StatusBadge v-if="column.type === 'status'" :status="item" />
            <span
              v-else-if="column.type === 'currency'"
              class="font-medium text-ink-gray-8 tabular-nums"
            >{{ formatCurrency(item, row.currency) }}</span>
            <span v-else-if="column.type === 'date'" class="text-ink-gray-6">{{ item || '—' }}</span>
            <span v-else class="text-ink-gray-7">{{ item ?? '—' }}</span>
          </template>
        </ListView>

        <!-- Mobile: frappe-ui-styled card fallback -->
        <div v-else class="space-y-3">
          <button
            v-for="row in rows"
            :key="row.name"
            type="button"
            class="w-full text-left bg-surface-white rounded-lg border border-outline-gray-1 p-3 shadow-sm active:bg-surface-gray-1 transition-colors"
            @click="goView(row)"
          >
            <div class="flex items-start justify-between gap-2">
              <div class="min-w-0">
                <p class="font-medium text-ink-gray-8 text-sm truncate">{{ row[primaryKey] || row.name }}</p>
                <p v-if="secondaryKey" class="text-xs text-ink-gray-5 mt-0.5 truncate">{{ row[secondaryKey] }}</p>
              </div>
              <div class="text-right flex-shrink-0 space-y-1">
                <p v-if="amountKey" class="font-semibold text-ink-gray-8 text-sm tabular-nums">{{ formatCurrency(row[amountKey], row.currency) }}</p>
                <StatusBadge v-if="statusKey" :status="row[statusKey]" />
              </div>
            </div>
          </button>
        </div>

        <!-- Pagination -->
        <div v-if="rows.length === pageSize || page > 0" class="flex items-center justify-end gap-2 mt-3">
          <Button variant="outline" theme="gray" size="sm" :disabled="page <= 0" @click="onPage(page - 1)">Previous</Button>
          <span class="text-xs text-ink-gray-5">Page {{ page + 1 }}</span>
          <Button variant="outline" theme="gray" size="sm" :disabled="rows.length < pageSize" @click="onPage(page + 1)">Next</Button>
        </div>
      </template>
    </template>

    <!-- VIEW -->
    <FinanceDetail
      v-else-if="mode === 'view'"
      :doctype="doctype"
      :name="activeName"
      @edit="goEdit"
      @deleted="onMutated"
      @close="goList"
    />

    <!-- CREATE FROM: inline submitted-source picker -> mapped seed -->
    <CreateFromPicker
      v-else-if="mode === 'createFrom' && activeFlow"
      :flow="activeFlow"
      @mapped="onMapped"
      @close="goBackFromForm"
    />

    <!-- NEW via custom composer (e.g. payment allocation). A mapped seed always
         wins so a Create-From result can never be swallowed by a section that
         also defines a custom newComponent. -->
    <component
      :is="newComponent"
      v-else-if="mode === 'new' && newComponent && !seedDoc"
      @saved="onSaved"
      @close="goBackFromForm"
    />

    <!-- NEW / EDIT via generic layout-driven form. `seed` pre-fills a new doc
         from a mapped source (Create From); ignored when editing (name set). -->
    <FinanceForm
      v-else-if="mode === 'new' || mode === 'edit'"
      :doctype="doctype"
      :name="mode === 'edit' ? activeName : null"
      :seed="mode === 'new' ? seedDoc : null"
      @saved="onSaved"
      @close="goBackFromForm"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { createResource, Button, ListView, Breadcrumbs } from 'frappe-ui'
import FinanceDetail from './FinanceDetail.vue'
import FinanceForm from './FinanceForm.vue'
import CreateFromPicker from './CreateFromPicker.vue'
import FcIcon from './FcIcon.vue'
import StatusBadge from './StatusBadge.vue'
import { useBoot } from '../../composables/useBoot.js'
import { useCurrency } from '../../composables/useCurrency.js'
import { useBreakpoint } from '../../composables/useBreakpoint.js'

const props = defineProps({
  doctype: { type: String, required: true },
  title: { type: String, default: '' },
  columns: { type: Array, default: () => [] },
  listResourceUrl: { type: String, required: true },
  listParams: { type: Function, default: () => ({}) },
  emptyLabel: { type: String, default: 'No records found.' },
  pageSize: { type: Number, default: 20 },
  // Optional custom component used for the "New" flow instead of FinanceForm.
  newComponent: { type: [Object, Function], default: null },
  // Optional "Create From" (mapped-doc) flows. Each entry renders a button that
  // opens an inline source picker, calls a whitelisted ERPNext mapper, and seeds
  // FinanceForm with the returned (unsaved) target doc for review + save. Shape:
  //   { key, label, sourceDoctype, sourceLabel, subtitleField?, mapMethod, targetDoctype }
  createFrom: { type: Array, default: () => [] },
  // Optional role allow-list for the "New" gate. Defaults to the native-DocType
  // create roles. Sections whose create goes through a custom endpoint (e.g.
  // Payments -> create_customer_payment, AR-gated) pass their own list so the
  // button's enabled state matches the backend and never shows a false-positive.
  createRoles: { type: Array, default: () => ['System Manager', 'Finance Manager', 'Accounts Manager', 'Accounts User'] },
})

const { getRoles, isAdministrator } = useBoot()
const { formatCurrency } = useCurrency()
const { isMobile } = useBreakpoint()

const mode = ref('list')
const activeName = ref(null)
const page = ref(0)

// Create-From state: the active flow config while picking a source, and the
// mapped (unsaved) target doc used to seed FinanceForm once a source is chosen.
const activeFlow = ref(null)
const seedDoc = ref(null)

const listResource = createResource({
  url: props.listResourceUrl,
  makeParams() {
    return { ...props.listParams(), page: page.value, page_size: props.pageSize }
  },
  auto: true,
})

const rows = computed(() => listResource.data || [])
const listLoading = computed(() => listResource.loading)
const listError = computed(() => listResource.error)

// ListView column shape: {label, key, width, align, getLabel, type(custom)}.
// getLabel drives the tooltip/plain value; the #cell slot handles rendering.
const listColumns = computed(() =>
  props.columns.map((c) => ({
    label: c.label,
    key: c.key,
    type: c.type,
    align: c.align || 'left',
    width: c.width || 1,
    getLabel: ({ row }) => {
      const v = row[c.key]
      if (c.type === 'currency') return formatCurrency(v, row.currency)
      return v == null || v === '' ? '—' : String(v)
    },
  })),
)

const listOptions = computed(() => ({
  selectable: false,
  showTooltip: false,
  resizeColumn: false,
  rowHeight: 44,
  onRowClick: (row) => goView(row),
  emptyState: { title: props.emptyLabel, description: '' },
}))

// Mobile card key hints derived from columns.
const primaryKey = computed(() => props.columns[0]?.key || 'name')
const secondaryKey = computed(() => props.columns[1]?.key || '')
const amountKey = computed(() => props.columns.find((c) => c.type === 'currency')?.key || '')
const statusKey = computed(() => props.columns.find((c) => c.type === 'status')?.key || '')

const roles = computed(() => getRoles())
const canCreate = computed(
  () => isAdministrator() || props.createRoles.some((r) => roles.value.includes(r)),
)

// Breadcrumb trail: Title / Record / Edit — routeless buttons (standalone page).
const breadcrumbs = computed(() => {
  const trail = [{ label: props.title || props.doctype, onClick: goList }]
  if (mode.value === 'view' && activeName.value) {
    trail.push({ label: activeName.value, onClick: () => {} })
  } else if (mode.value === 'edit' && activeName.value) {
    trail.push({ label: activeName.value, onClick: () => goView({ name: activeName.value }) })
    trail.push({ label: 'Edit', onClick: () => {} })
  } else if (mode.value === 'createFrom' && activeFlow.value) {
    trail.push({ label: activeFlow.value.label, onClick: () => {} })
  } else if (mode.value === 'new') {
    // Seeded new docs (Create From) keep the flow label in the trail for context.
    trail.push({ label: seedDoc.value && activeFlow.value ? activeFlow.value.label : 'New', onClick: () => {} })
  }
  return trail
})

function refetch() {
  listResource.fetch()
}
function onPage(p) {
  page.value = p
  refetch()
}

function resetCreateFrom() {
  activeFlow.value = null
  seedDoc.value = null
}

function goList() {
  mode.value = 'list'
  activeName.value = null
  resetCreateFrom()
}
function goView(row) {
  activeName.value = row.name
  mode.value = 'view'
}
function goNew() {
  activeName.value = null
  resetCreateFrom()
  mode.value = 'new'
}
function goEdit() {
  mode.value = 'edit'
}
function goBackFromForm() {
  // Editing an existing doc returns to its detail; anything else (new / seeded
  // new / create-from picker) returns to the list.
  if (activeName.value) {
    resetCreateFrom()
    mode.value = 'view'
  } else {
    goList()
  }
}

// Open the inline source picker for a Create-From flow.
function goCreateFrom(flow) {
  seedDoc.value = null
  activeFlow.value = flow
  mode.value = 'createFrom'
}
// A source was picked and mapped -> seed a new form with the target doc.
function onMapped(doc) {
  seedDoc.value = doc
  activeName.value = null
  mode.value = 'new'
}

function onSaved(doc) {
  activeName.value = doc?.name || activeName.value
  resetCreateFrom()
  refetch()
  mode.value = activeName.value ? 'view' : 'list'
}
function onMutated() {
  refetch()
  goList()
}

defineExpose({ refetch, resetPage: () => { page.value = 0 } })
</script>
