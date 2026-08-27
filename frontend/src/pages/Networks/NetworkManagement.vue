<template>
  <div class="flex h-full flex-col overflow-hidden">

    <!-- Header -->
    <div class="flex items-center justify-between border-b border-outline-gray-2 px-5 py-3">
      <h1 class="text-xl font-semibold text-ink-gray-9">{{ __('Opt-In Networks') }}</h1>
      <Button variant="solid" size="sm" @click="openAddForm">{{ __('Add Network') }}</Button>
    </div>

    <!-- Inline add form (top, minimal) -->
    <div v-if="showForm" class="border-b border-outline-gray-2 bg-surface-gray-1 px-5 py-4 dark:bg-surface-gray-2">
      <h2 class="mb-4 text-sm font-semibold text-ink-gray-9">{{ __('New Network') }}</h2>
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">

        <!-- Slug -->
        <div class="flex flex-col gap-1">
          <label class="text-xs font-medium text-ink-gray-6">
            {{ __('Slug') }} <span class="text-red-600">*</span>
          </label>
          <input
            v-model="form.slug"
            type="text"
            class="rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-sm text-ink-gray-9 focus:outline-none focus:ring-2 focus:ring-red-600 dark:bg-surface-gray-3 dark:text-ink-gray-3"
            placeholder="e.g. careverse-ke"
          />
        </div>

        <!-- Display Name -->
        <div class="flex flex-col gap-1">
          <label class="text-xs font-medium text-ink-gray-6">
            {{ __('Display Name') }} <span class="text-red-600">*</span>
          </label>
          <input
            v-model="form.display_name"
            type="text"
            class="rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-sm text-ink-gray-9 focus:outline-none focus:ring-2 focus:ring-red-600 dark:bg-surface-gray-3 dark:text-ink-gray-3"
          />
        </div>

        <!-- Contact Email -->
        <div class="flex flex-col gap-1">
          <label class="text-xs font-medium text-ink-gray-6">{{ __('Contact Email') }}</label>
          <input
            v-model="form.contact_email"
            type="email"
            class="rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-sm text-ink-gray-9 focus:outline-none focus:ring-2 focus:ring-red-600 dark:bg-surface-gray-3 dark:text-ink-gray-3"
          />
        </div>

        <!-- Enabled -->
        <div class="flex flex-col gap-1">
          <label class="text-xs font-medium text-ink-gray-6">{{ __('Status') }}</label>
          <label class="flex cursor-pointer items-center gap-2 pt-1.5">
            <input
              v-model="form.enabled"
              type="checkbox"
              class="h-4 w-4 rounded border-outline-gray-3 accent-red-600"
            />
            <span class="text-sm text-ink-gray-7">{{ __('Enabled') }}</span>
          </label>
        </div>
      </div>

      <p v-if="formError" class="mt-2 text-xs text-red-600">{{ formError }}</p>

      <div class="mt-4 flex gap-2">
        <Button variant="solid" :loading="saveResource.loading" @click="saveNetwork">{{ __('Save') }}</Button>
        <Button variant="subtle" @click="cancelForm">{{ __('Cancel') }}</Button>
      </div>
    </div>

    <!-- Table area -->
    <div class="flex-1 overflow-auto">
      <div v-if="listResource.loading" class="flex items-center justify-center py-16">
        <div class="h-6 w-6 animate-spin rounded-full border-2 border-red-600 border-t-transparent" />
      </div>

      <div v-else-if="!rows.length" class="flex flex-col items-center justify-center py-16 text-center">
        <p class="text-sm font-medium text-ink-gray-5">{{ __('No networks found') }}</p>
        <p class="mt-1 text-xs text-ink-gray-4">{{ __('Click "Add Network" to create one.') }}</p>
      </div>

      <table v-else class="w-full text-sm">
        <thead class="sticky top-0 z-10 bg-surface-gray-1 text-xs uppercase tracking-wide text-ink-gray-5">
          <tr>
            <th class="px-5 py-2.5 text-left font-medium">{{ __('Display Name') }}</th>
            <th class="px-4 py-2.5 text-left font-medium">{{ __('Slug') }}</th>
            <th class="px-4 py-2.5 text-left font-medium">{{ __('Status') }}</th>
            <th class="px-4 py-2.5 text-left font-medium">{{ __('Contact Email') }}</th>
            <th class="px-4 py-2.5 text-left font-medium">{{ __('Footer Name') }}</th>
            <th class="px-4 py-2.5 text-right font-medium"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-outline-elevation-2">
          <tr
            v-for="row in rows"
            :key="row.name"
            class="cursor-pointer transition-colors hover:bg-surface-gray-1"
            @click="openNetwork(row)"
          >
            <td class="px-5 py-3 font-medium text-ink-gray-9">{{ row.display_name }}</td>
            <td class="px-4 py-3 font-mono text-xs text-ink-gray-6">{{ row.slug }}</td>
            <td class="px-4 py-3">
              <span :class="statusPill(row.enabled)">
                {{ row.enabled ? __('Enabled') : __('Disabled') }}
              </span>
            </td>
            <td class="px-4 py-3 text-xs text-ink-gray-6">{{ row.contact_email || '—' }}</td>
            <td class="px-4 py-3 text-xs text-ink-gray-6">{{ row.footer_legal_name || '—' }}</td>
            <td class="px-4 py-3 text-right text-ink-gray-4">
              <svg xmlns="http://www.w3.org/2000/svg" class="inline h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="9 18 15 12 9 6"/>
              </svg>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination -->
      <div v-if="total > pageSize" class="flex items-center justify-between border-t border-outline-gray-2 px-5 py-3">
        <span class="text-xs text-ink-gray-5">
          {{ __('Showing {0}–{1} of {2}', [page * pageSize + 1, Math.min((page + 1) * pageSize, total), total]) }}
        </span>
        <div class="flex gap-2">
          <Button size="sm" variant="subtle" :disabled="page === 0" @click="prevPage">{{ __('Prev') }}</Button>
          <Button size="sm" variant="subtle" :disabled="(page + 1) * pageSize >= total" @click="nextPage">{{ __('Next') }}</Button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { createResource, Button } from 'frappe-ui'

const router = useRouter()

const page = ref(0)
const pageSize = 20
const showForm = ref(false)
const formError = ref('')

function emptyForm() {
  return {
    slug: '',
    display_name: '',
    enabled: true,
    contact_email: '',
  }
}

const form = reactive(emptyForm())

const listResource = createResource({
  url: 'crm.api.optin_admin.list_networks',
  makeParams: () => ({ page: page.value, page_size: pageSize }),
  auto: true,
})

const rows = computed(() => listResource.data?.rows ?? [])
const total = computed(() => listResource.data?.total ?? 0)

const saveResource = createResource({ url: 'crm.api.optin_admin.save_network' })

function openAddForm() {
  Object.assign(form, emptyForm())
  formError.value = ''
  showForm.value = true
}

function cancelForm() {
  showForm.value = false
  formError.value = ''
}

async function saveNetwork() {
  if (!form.slug.trim()) { formError.value = __('Slug is required.'); return }
  if (!form.display_name.trim()) { formError.value = __('Display Name is required.'); return }
  formError.value = ''
  const slug = form.slug.trim()
  try {
    await saveResource.submit({ data: { ...form, slug } })
    showForm.value = false
    router.push({ name: 'NetworkDetail', params: { networkSlug: slug } })
  } catch (e) {
    formError.value = e?.messages?.[0] ?? e?.message ?? __('Save failed.')
  }
}

function openNetwork(row) {
  router.push({ name: 'NetworkDetail', params: { networkSlug: row.slug } })
}

function prevPage() {
  page.value--
  listResource.reload()
}

function nextPage() {
  page.value++
  listResource.reload()
}

function statusPill(enabled) {
  const base = 'rounded-full px-2 py-0.5 text-xs font-medium'
  return enabled
    ? `${base} bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400`
    : `${base} bg-surface-gray-2 text-ink-gray-6 dark:bg-surface-gray-4 dark:text-ink-gray-4`
}
</script>
