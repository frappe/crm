<template>
  <Dialog v-model:open="show" size="5xl" bare>
    <template #default>
      <div class="px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-4 flex items-start justify-between gap-4">
          <div>
            <Dialog.Title as-child>
              <h3 class="text-2xl-semibold leading-6 text-ink-gray-9">
                {{ __('Merge leads') }}
              </h3>
            </Dialog.Title>
            <p class="mt-1.5 text-p-base text-ink-gray-5">
              {{ __('Pick the value to keep for each field.') }}
            </p>
          </div>
          <Dialog.Close as-child>
            <Button
              :aria-label="__('Close')"
              variant="ghost"
              class="w-7 shrink-0"
              icon="lucide-x"
            />
          </Dialog.Close>
        </div>

        <div
          class="mb-5 inline-flex max-w-full items-center rounded-4 bg-surface-gray-2 px-3 py-1.5 text-base text-ink-gray-6"
        >
          <span class="truncate">
            {{ source.lead_name || source.name }} · {{ source.name }}
          </span>
        </div>

        <div class="grid gap-6 md:grid-cols-[minmax(0,1fr)_360px]">
          <div class="min-w-0">
            <div
              v-if="loading"
              class="flex h-40 items-center justify-center text-p-base text-ink-gray-5"
            >
              {{ __('Loading...') }}
            </div>
            <MergeFieldRows
              v-else-if="loaded"
              :conflicts="conflicts"
              :autoFields="autoFields"
              :picks="picks"
              :displayOf="displayOf"
              :pickedDisplay="pickedDisplay"
              @pick="pick"
            />
          </div>
          <MergePreview
            v-if="loaded"
            :doc="mergedDoc"
            :displays="displays"
            :assignees="assignees"
          />
        </div>

        <ErrorMessage v-if="error" class="mt-4" :message="error" />
      </div>
      <div class="flex justify-end gap-2 px-4 pb-6 sm:px-6">
        <Button variant="subtle" :label="__('Back')" @click="emit('back')" />
        <Button
          variant="solid"
          :label="__('Merge')"
          :loading="merging"
          :disabled="!loaded"
          @click="onMerge"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import MergeFieldRows from '@/components/Modals/MergeLead/MergeFieldRows.vue'
import MergePreview from '@/components/Modals/MergeLead/MergePreview.vue'
import type { SelectableLead } from '@/components/Modals/SelectLeadModal.vue'
import { useLeadMerge } from '@/composables/useLeadMerge'
import { Dialog, ErrorMessage, toast } from 'frappe-ui'
import { computed, watch } from 'vue'

const props = defineProps<{
  // the lead being kept: the Lead page's doc
  target: Record<string, unknown> & { name: string; lead_name?: string }
  targetAssignees: string[]
  // the lead merged into it and then marked as merged
  source: SelectableLead
}>()

const emit = defineEmits<{ back: []; merged: [targetName: string] }>()

const show = defineModel<boolean>({ default: false })

const {
  fields,
  conflicts,
  autoFields,
  picks,
  assignees,
  loaded,
  loading,
  merging,
  error,
  load,
  pick,
  displayOf,
  pickedValue,
  pickedDisplay,
  merge,
} = useLeadMerge(
  () => props.target.name,
  () => props.source.name,
  () => props.targetAssignees,
)

const mergedDoc = computed(() => ({
  ...props.target,
  ...Object.fromEntries(fields.value.map((f) => [f.fieldname, pickedValue(f)])),
}))

const displays = computed(() =>
  Object.fromEntries(fields.value.map((f) => [f.fieldname, pickedDisplay(f)])),
)

watch(
  () => show.value && props.source?.name,
  (sourceName) => {
    if (sourceName) load()
  },
  { immediate: true },
)

async function onMerge() {
  const targetName = await merge()
  if (!targetName) return
  toast.success(__('Leads merged'))
  emit('merged', targetName)
  show.value = false
}
</script>
