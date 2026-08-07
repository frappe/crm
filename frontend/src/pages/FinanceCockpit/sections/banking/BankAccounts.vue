<template>
  <div class="space-y-3">
    <div v-if="loading" class="text-sm text-gray-500 dark:text-gray-400">Loading bank accounts…</div>

    <div v-else-if="error" class="text-sm text-red-600 dark:text-red-400">
      Failed to load bank accounts.
      <button class="underline ml-1" @click="refetch">Retry</button>
    </div>

    <div v-else-if="!accounts.length" class="text-sm text-gray-500 dark:text-gray-400 py-8 text-center">
      No company bank accounts configured.
    </div>

    <div v-else class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      <div
        v-for="acct in accounts"
        :key="acct.name"
        class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4 space-y-2"
      >
        <div class="flex items-start justify-between gap-2">
          <div>
            <p class="text-sm font-semibold text-gray-800 dark:text-gray-200">{{ acct.account }}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400">{{ acct.bank }}</p>
          </div>
        </div>
        <div class="pt-1">
          <a
            :href="'/app/bank-reconciliation-tool?bank_account=' + encodeURIComponent(acct.name)"
            target="_blank"
            class="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded bg-blue-600 text-white hover:bg-blue-700 transition-colors"
          >
            <LucideRefreshCw class="w-3 h-3" />
            Reconcile
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, watch } from 'vue'
import { createResource } from 'frappe-ui'
import LucideRefreshCw from '~icons/lucide/refresh-cw'
import { useCompanyContext } from '../../composables/useCompanyContext.js'

const { company } = useCompanyContext()

const resource = createResource({
  url: 'crm.finance.api.get_bank_accounts',
  makeParams() { return { company: company.value } },
  auto: true,
})

const loading = computed(() => resource.loading)
const error = computed(() => resource.error)
const accounts = computed(() => resource.data || [])

function refetch() { resource.fetch() }
watch(company, () => resource.fetch())
</script>
