<template>
  <div class="flex flex-col gap-4">
    <p v-if="!result" class="text-p-base text-ink-gray-6">
      {{
        __('{0} leads are ready to import. Here are the first few rows.', [
          totalRows,
        ])
      }}
    </p>

    <ul
      v-if="!result && warnings.length"
      class="flex flex-col gap-1 rounded-md bg-surface-amber-2 p-2 text-sm text-ink-amber-6"
    >
      <li v-for="(warning, i) in warnings" :key="i">{{ warning }}</li>
    </ul>

    <div
      v-if="!result"
      class="max-h-[280px] overflow-auto rounded-md border border-outline-gray-2"
    >
      <table class="w-full text-sm">
        <thead class="bg-surface-gray-1 text-left text-ink-gray-5">
          <tr>
            <th v-for="column in columns" :key="column.key" class="px-3 py-2">
              {{ column.label }}
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-outline-gray-1 text-ink-gray-7">
          <tr v-for="(row, i) in rows" :key="i">
            <td v-for="column in columns" :key="column.key" class="px-3 py-2">
              {{ row[column.key] }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="importing" class="flex flex-col gap-2" role="status">
      <div class="text-base text-ink-gray-7">{{ progressLabel }}</div>
      <div class="h-1.5 w-full rounded-full bg-surface-gray-2">
        <div
          class="h-1.5 rounded-full bg-surface-gray-9 transition-all duration-300"
          :style="{ width: `${progressPercent}%` }"
        />
      </div>
    </div>

    <SetupImportResult v-if="result" :result="result" />

    <div class="mt-auto flex justify-between">
      <Button
        v-if="!result"
        :label="__('Back')"
        :disabled="importing"
        @click="emit('back')"
      />
      <Button
        v-if="result && !succeeded"
        :label="__('Start over')"
        @click="emit('restart')"
      />
      <span v-else-if="result" />
      <Button
        v-if="!result"
        variant="solid"
        :label="__('Import {0} leads', [totalRows])"
        :loading="importing"
        @click="emit('import')"
      />
      <Button
        v-else-if="succeeded"
        variant="solid"
        :label="__('Continue')"
        @click="emit('continue')"
      />
    </div>
  </div>
</template>

<script setup>
import SetupImportResult from '@/components/Setup/SetupImportResult.vue'
import { stripTags } from '@/utils/setup'
import { Button } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  preview: { type: Object, required: true },
  importing: { type: Boolean, default: false },
  progress: { type: Object, default: null },
  result: { type: Object, default: null },
})

const emit = defineEmits(['back', 'import', 'restart', 'continue'])

const PREVIEW_ROWS = 10

const totalRows = computed(() => props.preview.total_number_of_rows || 0)

const columns = computed(() =>
  props.preview.columns
    .map((column, key) => ({ key, label: column.df?.label, column }))
    .filter(({ key, column }) => key > 0 && !column.skip_import && column.df),
)

const rows = computed(() => (props.preview.data || []).slice(0, PREVIEW_ROWS))

const warnings = computed(() =>
  (props.preview.warnings || [])
    .filter((w) => w.type !== 'info')
    .map((w) => stripTags(w.message)),
)

const progressPercent = computed(() => {
  const { current, total } = props.progress || {}
  return total ? Math.floor((current / total) * 100) : 10
})

const progressLabel = computed(() => {
  const { current, total } = props.progress || {}
  if (!total) return __('Importing leads...')
  return __('Importing {0} of {1} leads...', [current, total])
})

const succeeded = computed(() =>
  ['Success', 'Partial Success'].includes(props.result?.status),
)
</script>
