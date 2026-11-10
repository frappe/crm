<template>
  <Dialog v-model:open="show" :size="'lg'">
    <template #title>
      <div class="text-xl font-semibold text-ink-gray-9">
        {{ __('Import Data') }}
      </div>
    </template>
    <template #default>
      <div class="flex flex-col gap-4 py-2">
        <p class="text-sm text-ink-gray-6">
          {{ __('Choose how you would like to import your data into Frappe CRM:') }}
        </p>

        <div class="flex flex-col gap-3">
          <!-- Option A: Single Import (first / default) -->
          <div
            class="flex cursor-pointer items-start gap-3.5 rounded-lg border p-4 transition-all"
            :class="[
              selectedType === 'single'
                ? 'border-surface-gray-7 bg-surface-gray-2 shadow-xs'
                : 'border-outline-gray-2 bg-surface-white hover:bg-surface-gray-1',
            ]"
            @click="selectedType = 'single'"
          >
            <div class="mt-0.5">
              <input
                type="radio"
                name="importType"
                value="single"
                :checked="selectedType === 'single'"
                class="size-4 text-ink-gray-9 focus:ring-0"
                @change="selectedType = 'single'"
              />
            </div>
            <div class="flex-1">
              <div class="text-base font-semibold text-ink-gray-9">
                {{ __('Single Import') }}
              </div>
              <div class="mt-0.5 text-sm text-ink-gray-6">
                {{ __('Create/import one record manually.') }}
              </div>
            </div>
          </div>

          <!-- Option B: Bulk Import -->
          <div
            class="flex cursor-pointer items-start gap-3.5 rounded-lg border p-4 transition-all"
            :class="[
              selectedType === 'bulk'
                ? 'border-surface-gray-7 bg-surface-gray-2 shadow-xs'
                : 'border-outline-gray-2 bg-surface-white hover:bg-surface-gray-1',
            ]"
            @click="selectedType = 'bulk'"
          >
            <div class="mt-0.5">
              <input
                type="radio"
                name="importType"
                value="bulk"
                :checked="selectedType === 'bulk'"
                class="size-4 text-ink-gray-9 focus:ring-0"
                @change="selectedType = 'bulk'"
              />
            </div>
            <div class="flex-1">
              <div class="text-base font-semibold text-ink-gray-9">
                {{ __('Bulk Import') }}
              </div>
              <div class="mt-0.5 text-sm text-ink-gray-6">
                {{ __('Upload an Excel/CSV file and import multiple records.') }}
              </div>
            </div>
          </div>
        </div>

        <div class="mt-1 flex items-center justify-between pt-2 text-xs text-ink-gray-5">
          <button
            type="button"
            class="hover:underline text-ink-gray-6"
            @click="openLegacyImport"
          >
            {{ __('Looking for standard Frappe Data Import? Click here') }}
          </button>
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex w-full justify-end gap-2">
        <Button
          variant="subtle"
          :label="__('Cancel')"
          @click="show = false"
        />
        <Button
          variant="solid"
          :label="__('Continue')"
          @click="proceed"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { Dialog, Button } from 'frappe-ui'
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'select'])
const router = useRouter()

const show = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const selectedType = ref('single')

function proceed() {
  show.value = false
  emit('select', selectedType.value)
}

function openLegacyImport() {
  show.value = false
  router.push({ name: 'NewDataImport' })
}
</script>

