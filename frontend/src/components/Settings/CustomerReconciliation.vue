<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div class="min-w-0 flex-1">
        <h3 class="text-base-medium text-ink-gray-8">
          {{ __('Customer Synchronization') }}
        </h3>
        <p class="mt-1 text-p-sm text-ink-gray-5">
          {{
            __(
              'Import ERPNext company customers and review their CRM organization links.',
            )
          }}
        </p>
      </div>
      <div class="flex items-center gap-2">
        <Button variant="subtle" :loading="loading" @click="loadPage">
          {{ __('Refresh') }}
        </Button>
        <Button
          v-if="canManage"
          variant="solid"
          icon-left="lucide-refresh-cw"
          :loading="startingSync"
          :disabled="settingsDirty || syncQueued || serverRunBusy || resolving"
          @click="runSync"
        >
          {{ __('Sync Customers') }}
        </Button>
      </div>
    </div>

    <p v-if="settingsDirty" class="text-p-sm text-ink-gray-6" role="status">
      {{
        __(
          'Save your ERPNext settings before synchronizing or reviewing customer links.',
        )
      }}
    </p>
    <p v-if="syncNotice" class="text-p-sm text-ink-gray-6" role="status">
      {{ syncNotice }}
    </p>
    <ErrorMessage v-if="syncError" :message="syncError" />
    <div
      v-if="serverRun?.status"
      class="space-y-2 rounded-4 border border-outline-elevation-2 p-3"
      :role="serverRun.status === 'Failed' ? 'alert' : 'status'"
    >
      <div class="text-p-sm-medium text-ink-gray-8">
        {{ __('Synchronization Run') }}: {{ __(serverRun.status) }}
      </div>
      <ErrorMessage
        v-if="serverRun.status === 'Failed'"
        :message="
          serverRun.message ||
          __(
            'The synchronization job could not finish. Review the connection and permissions before trying again.',
          )
        "
      />
      <p
        v-else-if="serverRun.message"
        class="whitespace-pre-wrap break-words text-p-sm text-ink-gray-6"
      >
        {{ serverRun.message }}
      </p>
      <p
        v-if="serverRun.status === 'Completed'"
        class="text-p-sm text-ink-gray-6"
      >
        {{
          __(
            'The background job completed. Review the customer statuses below for records that still need attention.',
          )
        }}
      </p>
      <div class="flex flex-wrap gap-x-4 gap-y-1 text-p-sm text-ink-gray-5">
        <span v-if="serverRun.last_attempt"
          >{{ __('Last Attempt') }}:
          {{ formatDate(serverRun.last_attempt) }}</span
        >
        <span v-if="serverRun.last_success"
          >{{ __('Last Completed Run') }}:
          {{ formatDate(serverRun.last_success) }}</span
        >
      </div>
    </div>

    <div class="flex flex-wrap items-end gap-3">
      <FormControl
        v-model="search"
        type="search"
        :label="__('Search Customers')"
        :placeholder="__('Customer name or ID')"
        class="min-w-48 flex-1"
      />
      <FormControl
        v-model="status"
        type="select"
        :label="__('Status')"
        :options="statusOptions"
        class="w-40"
      />
    </div>

    <div v-if="loadError" class="space-y-2" role="alert">
      <ErrorMessage :message="loadError" />
      <Button variant="subtle" :loading="loading" @click="loadPage">
        {{ __('Try Again') }}
      </Button>
    </div>
    <div
      v-if="loading && !pageData"
      class="flex min-h-32 items-center justify-center"
      role="status"
      :aria-label="__('Loading customer synchronization records')"
    >
      <LoadingIndicator class="size-5" />
    </div>
    <div v-else-if="pageData" :aria-busy="loading">
      <div
        v-if="!pageData.rows.length"
        class="rounded-4 border border-outline-elevation-2 px-4 py-8 text-center text-p-sm text-ink-gray-5"
      >
        <template v-if="start > 0">
          <p>{{ __('There are no records on this page.') }}</p>
          <Button class="mt-3" variant="subtle" @click="firstPage">
            {{ __('First Page') }}
          </Button>
        </template>
        <p v-else-if="search || status">
          {{ __('No customer synchronization records match these filters.') }}
        </p>
        <p v-else>
          {{
            __(
              'No customers have been reviewed yet. Select Sync Customers to import them from ERPNext.',
            )
          }}
        </p>
      </div>
      <div v-else class="overflow-x-auto">
        <table class="w-full text-left text-p-sm">
          <thead class="text-ink-gray-5">
            <tr class="border-b border-outline-elevation-2">
              <th class="min-w-44 px-2 py-2 font-normal" scope="col">
                {{ __('ERPNext Customer') }}
              </th>
              <th class="min-w-40 px-2 py-2 font-normal" scope="col">
                {{ __('CRM Organization') }}
              </th>
              <th class="px-2 py-2 font-normal" scope="col">
                {{ __('Status') }}
              </th>
              <th class="min-w-28 px-2 py-2 font-normal" scope="col">
                {{ __('Match') }}
              </th>
              <th class="min-w-36 px-2 py-2 font-normal" scope="col">
                {{ __('Last Attempt') }}
              </th>
              <th class="min-w-48 px-2 py-2 font-normal" scope="col">
                {{ __('Details') }}
              </th>
              <th v-if="canManage" class="px-2 py-2 font-normal" scope="col">
                <span class="sr-only">{{ __('Actions') }}</span>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in pageData.rows"
              :key="row.name"
              class="border-b border-outline-elevation-2 last:border-b-0"
            >
              <td class="px-2 py-3 align-top">
                <a
                  :href="customerUrl(row.customer)"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="text-p-sm-medium text-ink-gray-8 hover:underline"
                >
                  {{ row.customer_name || row.customer }}
                </a>
                <div
                  v-if="row.customer_name && row.customer_name !== row.customer"
                  class="mt-1 text-ink-gray-5"
                >
                  {{ row.customer }}
                </div>
                <div v-if="row.customer_type" class="mt-1 text-ink-gray-5">
                  {{ __(row.customer_type) }}
                </div>
              </td>
              <td class="px-2 py-3 align-top">
                <RouterLink
                  v-if="row.organization"
                  :to="{
                    name: 'Organization',
                    params: { organizationId: row.organization },
                  }"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="text-ink-gray-8 hover:underline"
                >
                  {{ row.organization }}
                </RouterLink>
                <span v-else class="text-ink-gray-5">{{
                  __('Not linked')
                }}</span>
              </td>
              <td class="px-2 py-3 align-top">
                <Badge
                  :label="__(row.status)"
                  :theme="statusTheme(row.status)"
                  variant="outline"
                />
              </td>
              <td class="px-2 py-3 align-top text-ink-gray-6">
                {{ row.match_rule ? __(row.match_rule) : '—' }}
              </td>
              <td class="px-2 py-3 align-top text-ink-gray-6">
                {{ row.last_attempt ? formatDate(row.last_attempt) : '—' }}
              </td>
              <td
                class="max-w-xs whitespace-pre-wrap break-words px-2 py-3 align-top text-ink-gray-6"
              >
                {{ row.message || '—' }}
              </td>
              <td v-if="canManage" class="px-2 py-3 align-top">
                <Button
                  variant="subtle"
                  :disabled="settingsDirty || resolving"
                  @click="openReview(row)"
                  >{{ __('Review') }}</Button
                >
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div
        class="mt-3 flex flex-wrap items-center justify-between gap-3 text-p-sm text-ink-gray-5"
      >
        <span>{{ rangeLabel }}</span>
        <div class="flex gap-2">
          <Button
            variant="subtle"
            :disabled="loading || start === 0"
            @click="changePage(-1)"
            >{{ __('Previous') }}</Button
          >
          <Button
            variant="subtle"
            :disabled="loading || !pageData.has_more"
            @click="changePage(1)"
            >{{ __('Next') }}</Button
          >
        </div>
      </div>
    </div>

    <Dialog
      v-model:open="showReview"
      :title="__('Review Customer Link')"
      :dismissible="!resolving"
      @after-leave="resetReview"
    >
      <template #default>
        <div v-if="reviewRow" class="space-y-4">
          <dl
            class="grid grid-cols-[auto_minmax(0,1fr)] gap-x-4 gap-y-2 text-p-sm"
          >
            <dt class="text-ink-gray-5">{{ __('ERPNext Customer') }}</dt>
            <dd class="break-words text-ink-gray-8">
              {{ reviewRow.customer_name || reviewRow.customer }} ·
              {{ reviewRow.customer }}
            </dd>
            <dt class="text-ink-gray-5">{{ __('CRM Organization') }}</dt>
            <dd class="break-words text-ink-gray-8">
              {{ reviewRow.organization || __('Not linked') }}
            </dd>
            <dt class="text-ink-gray-5">{{ __('Status') }}</dt>
            <dd class="text-ink-gray-8">{{ __(reviewRow.status) }}</dd>
            <dt class="text-ink-gray-5">{{ __('Match') }}</dt>
            <dd class="text-ink-gray-8">
              {{ reviewRow.match_rule ? __(reviewRow.match_rule) : '—' }}
            </dd>
            <dt class="text-ink-gray-5">{{ __('Last Success') }}</dt>
            <dd class="text-ink-gray-8">
              {{
                reviewRow.last_success
                  ? formatDate(reviewRow.last_success)
                  : '—'
              }}
            </dd>
          </dl>
          <p
            v-if="reviewRow.message"
            class="whitespace-pre-wrap break-words text-p-sm text-ink-gray-6"
          >
            {{ reviewRow.message }}
          </p>
          <p
            v-if="reviewRow.status === 'Unlinked' && reviewRow.organization"
            class="text-p-sm text-ink-gray-6"
          >
            {{
              __(
                'The ERPNext unlink has not been confirmed. Retry Unlink before synchronizing this Customer again.',
              )
            }}
          </p>
          <FormControl
            v-if="actionOptions.length"
            v-model="action"
            type="select"
            :label="__('Action')"
            :options="[
              { label: __('Select an action'), value: '' },
              ...actionOptions,
            ]"
            :disabled="resolving || reviewNeedsRefresh"
          />
          <p v-else class="text-p-sm text-ink-gray-5">
            {{
              __('This Customer type is not synchronized to CRM organizations.')
            }}
          </p>
          <Link
            v-if="action === 'link'"
            v-model="organization"
            doctype="CRM Organization"
            :label="__('CRM Organization')"
            :placeholder="__('Select an existing organization')"
            :disabled="resolving || reviewNeedsRefresh"
            required
          />
          <p v-if="actionDescription" class="text-p-sm text-ink-gray-6">
            {{ actionDescription }}
          </p>
          <ErrorMessage v-if="reviewError" :message="reviewError" />
        </div>
      </template>
      <template #actions>
        <div class="flex justify-end gap-2">
          <Button variant="subtle" :disabled="resolving" @click="closeReview">{{
            reviewNeedsRefresh ? __('Close and Refresh') : __('Cancel')
          }}</Button>
          <Button
            v-if="!reviewNeedsRefresh"
            variant="solid"
            :theme="action === 'unlink' ? 'red' : 'gray'"
            :loading="resolving"
            :disabled="!canApply"
            @click="resolveReview"
            >{{ actionLabel || __('Apply') }}</Button
          >
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { watchDebounced } from '@vueuse/core'
import {
  Badge,
  Button,
  createResource,
  Dialog,
  ErrorMessage,
  FormControl,
  LoadingIndicator,
  toast,
} from 'frappe-ui'
import Link from '@/components/Controls/Link.vue'
import { globalStore } from '@/stores/global'
import { formatDate } from '@/utils'

const props = defineProps({
  settingsDirty: { type: Boolean, default: false },
  erpnextSiteUrl: { type: String, default: '' },
})
const { $socket } = globalStore()
const api = 'crm.integrations.erpnext.customers'
const pageLength = 20
const start = ref(0)
const pageStart = ref(0)
const search = ref('')
const status = ref('')
const pageData = ref(null)
const loading = ref(false)
const loadError = ref('')
const startingSync = ref(false)
const syncQueued = ref(false)
const syncNotice = ref('')
const syncError = ref('')
const showReview = ref(false)
const reviewRow = ref(null)
const action = ref('')
const organization = ref('')
const resolving = ref(false)
const reviewError = ref('')
const reviewNeedsRefresh = ref(false)
let active = true
let requestVersion = 0
let refreshTimer
let remainingRefreshes = 0
let observedBusyRun = false

const statusResource = createResource({
  url: `${api}.get_customer_sync_status`,
})
const syncResource = createResource({
  url: `${api}.run_customer_sync`,
  method: 'POST',
})
const resolveResource = createResource({
  url: `${api}.resolve_customer`,
  method: 'POST',
})
const canManage = computed(() =>
  Boolean(pageData.value?.can_manage && !loadError.value),
)
const serverRun = computed(() => pageData.value?.run)
const serverRunBusy = computed(() =>
  ['Queued', 'Running'].includes(serverRun.value?.status),
)
const rangeLabel = computed(() => {
  if (!pageData.value) return ''
  return pageData.value.rows.length
    ? __('{0}–{1} of {2}', [
        pageStart.value + 1,
        pageStart.value + pageData.value.rows.length,
        pageData.value.total,
      ])
    : __('{0} records', [pageData.value.total])
})
const statusOptions = [
  { label: __('All statuses'), value: '' },
  ...['Pending', 'Synced', 'Review', 'Failed', 'Ignored', 'Unlinked'].map(
    (value) => ({ label: __(value), value }),
  ),
]
const actionLabels = {
  link: __('Link Organization'),
  create: __('Create Organization'),
  resync: __('Resync'),
  ignore: __('Ignore'),
  unlink: __('Unlink'),
}
const actionOptions = computed(() => {
  if (!reviewRow.value) return []
  const row = reviewRow.value
  const actions =
    row.status === 'Synced'
      ? ['resync', 'unlink']
      : row.status === 'Unlinked' && row.organization
        ? ['unlink']
        : row.status === 'Ignored'
          ? ['resync']
          : ['link', 'create', 'resync', 'ignore']
  return actions
    .filter(
      (value) =>
        !['link', 'create', 'resync'].includes(value) ||
        row.customer_type === 'Company',
    )
    .map((value) => ({
      value,
      label:
        value === 'unlink' && row.status === 'Unlinked' && row.organization
          ? __('Retry Unlink')
          : actionLabels[value],
    }))
})
const actionLabel = computed(
  () =>
    actionOptions.value.find((option) => option.value === action.value)
      ?.label || '',
)
const actionDescription = computed(
  () =>
    ({
      link: __(
        'Link this Customer to the selected organization and apply the current ERPNext-owned organization fields and contact and address mappings.',
      ),
      create: __(
        'Create a CRM organization from this Customer using the current ERPNext-owned fields and contact and address mappings.',
      ),
      resync: __(
        'Apply the current ERPNext-owned organization fields and contact and address mappings. This does not change ERPNext accounting records.',
      ),
      ignore: __(
        'Exclude this Customer from automatic synchronization. You can review it again later.',
      ),
      unlink: __(
        'Remove the Customer–Organization link without deleting either record. Review the Customer again before linking it.',
      ),
    })[action.value] || '',
)
const canApply = computed(() =>
  Boolean(
    canManage.value &&
    !props.settingsDirty &&
    reviewRow.value?.modified &&
    actionOptions.value.some((option) => option.value === action.value) &&
    (action.value !== 'link' || organization.value) &&
    !resolving.value,
  ),
)

function message(error, fallback) {
  return error?.messages?.[0] || error?.message || fallback
}

async function loadPage() {
  const version = ++requestVersion
  const requestedStart = start.value
  loading.value = true
  try {
    const data = await statusResource.submit({
      start: requestedStart,
      page_length: pageLength,
      search: search.value.trim(),
      status: status.value,
    })
    if (!active || version !== requestVersion) return
    if (
      !Array.isArray(data?.rows) ||
      typeof data.total !== 'number' ||
      typeof data.has_more !== 'boolean'
    )
      throw new Error(
        __(
          'Customer synchronization results could not be read. Refresh to try again.',
        ),
      )
    pageData.value = data
    pageStart.value = requestedStart
    loadError.value = ''
    if (['Completed', 'Failed'].includes(data.run?.status)) {
      stopRefreshing()
      observedBusyRun = false
      syncNotice.value = ''
    } else if (
      ['Queued', 'Running'].includes(data.run?.status) &&
      !observedBusyRun
    ) {
      observedBusyRun = true
      syncQueued.value = true
      remainingRefreshes = 12
      scheduleRefresh()
    }
  } catch (error) {
    if (active && version === requestVersion)
      loadError.value = message(
        error,
        __('Customer synchronization records could not be loaded.'),
      )
  } finally {
    if (active && version === requestVersion) loading.value = false
  }
}

function firstPage() {
  start.value = 0
  loadPage()
}
function changePage(direction) {
  start.value = Math.max(0, start.value + direction * pageLength)
  loadPage()
}
watchDebounced(search, firstPage, { debounce: 300 })
watch(status, firstPage)

function stopRefreshing() {
  clearTimeout(refreshTimer)
  refreshTimer = undefined
  remainingRefreshes = 0
  syncQueued.value = false
}
function scheduleRefresh() {
  clearTimeout(refreshTimer)
  if (!active || !syncQueued.value) return
  if (!remainingRefreshes) {
    syncQueued.value = false
    syncNotice.value = __(
      'Automatic refresh stopped. Use Refresh to check the latest results.',
    )
    return
  }
  refreshTimer = setTimeout(async () => {
    remainingRefreshes--
    await loadPage()
    if (!active || !syncQueued.value) return
    if (loadError.value) {
      stopRefreshing()
      return
    }
    scheduleRefresh()
  }, 10_000)
}
async function runSync() {
  if (
    !canManage.value ||
    props.settingsDirty ||
    startingSync.value ||
    syncQueued.value ||
    serverRunBusy.value
  )
    return
  startingSync.value = true
  syncError.value = ''
  try {
    const result = await syncResource.submit()
    if (!active) return
    if (!result?.queued)
      throw new Error(
        __(
          'The customer synchronization could not be started. Refresh the results before trying again.',
        ),
      )
    syncQueued.value = true
    observedBusyRun = true
    syncNotice.value = __(
      'Customer synchronization is queued. Results refresh automatically for up to two minutes.',
    )
    remainingRefreshes = 12
    await loadPage()
    scheduleRefresh()
  } catch (error) {
    if (active)
      syncError.value = message(
        error,
        __('Customer synchronization could not be started.'),
      )
  } finally {
    if (active) startingSync.value = false
  }
}
function onSyncComplete() {
  stopRefreshing()
  syncNotice.value = ''
  loadPage()
}

function openReview(row) {
  reviewRow.value = { ...row }
  action.value = ''
  organization.value = ''
  reviewError.value = ''
  reviewNeedsRefresh.value = false
  showReview.value = true
}
function resetReview() {
  reviewRow.value = null
  action.value = ''
  organization.value = ''
  reviewError.value = ''
  reviewNeedsRefresh.value = false
}
function closeReview() {
  if (resolving.value) return
  const refresh = reviewNeedsRefresh.value
  showReview.value = false
  if (refresh) loadPage()
}
async function resolveReview() {
  if (!canApply.value || reviewNeedsRefresh.value) return
  resolving.value = true
  reviewError.value = ''
  try {
    const result = await resolveResource.submit({
      name: reviewRow.value.name,
      action: action.value,
      organization: action.value === 'link' ? organization.value : null,
      modified: reviewRow.value.modified,
    })
    if (!active) return
    const expectedStatus = {
      link: 'Synced',
      create: 'Synced',
      resync: 'Synced',
      ignore: 'Ignored',
      unlink: 'Unlinked',
    }[action.value]
    if (result?.status !== expectedStatus)
      throw new Error(
        result?.message ||
          __(
            'The customer still needs review. Close and refresh the record before trying again.',
          ),
      )
    showReview.value = false
    toast.success(__('Customer review saved'))
    await loadPage()
  } catch (error) {
    if (!active) return
    reviewError.value = message(
      error,
      __(
        'The result could not be confirmed. Close and refresh the records before trying again.',
      ),
    )
    reviewNeedsRefresh.value = true
  } finally {
    if (active) resolving.value = false
  }
}
function statusTheme(value) {
  return value === 'Synced'
    ? 'green'
    : value === 'Failed'
      ? 'red'
      : value === 'Review'
        ? 'orange'
        : 'gray'
}
function customerUrl(customer) {
  try {
    const url = new URL(
      `/app/customer/${encodeURIComponent(customer)}`,
      props.erpnextSiteUrl || window.location.origin,
    )
    return ['http:', 'https:'].includes(url.protocol) ? url.toString() : ''
  } catch {
    return ''
  }
}
onMounted(() => {
  loadPage()
  $socket.on('crm_customer_sync_complete', onSyncComplete)
})
onBeforeUnmount(() => {
  active = false
  requestVersion++
  stopRefreshing()
  $socket.off('crm_customer_sync_complete', onSyncComplete)
})
</script>
