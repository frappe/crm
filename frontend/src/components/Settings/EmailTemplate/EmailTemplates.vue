<template>
  <div
    class="flex h-full flex-col gap-6 p-6 text-ink-gray-8 max-sm:gap-0 max-sm:p-0"
  >
    <!-- Header -->
    <div class="flex justify-between px-2 pt-2 max-sm:hidden">
      <div class="flex flex-col gap-1 w-9/12">
        <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
          {{ __('Email Templates') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Add, edit, and manage email templates for various CRM communications.',
            )
          }}
        </p>
      </div>
      <div class="flex item-center space-x-2 w-3/12 justify-end">
        <Teleport defer to="#settings-phone-actions" :disabled="!isPhone">
          <Button
            :label="__('New')"
            icon-left="lucide-plus"
            variant="solid"
            @click="emit('updateStep', 'new-template')"
          />
        </Teleport>
      </div>
    </div>

    <!-- loading state -->
    <div
      v-if="templates.loading"
      class="flex mt-28 justify-between w-full h-full"
    >
      <Button
        :loading="templates.loading"
        variant="ghost"
        class="w-full"
        size="2xl"
      />
    </div>

    <!-- Empty State -->
    <EmptyState
      v-else-if="!templates.loading && !templates.data?.length"
      name="Email Templates"
      :description="__('Add one to get started.')"
      :icon="EmailTemplateIcon"
    />

    <!-- Email template list -->
    <div
      v-if="!templates.loading && templates.data?.length"
      class="flex flex-col overflow-hidden"
    >
      <div
        v-if="templates.data?.length > 10"
        class="flex items-center gap-2 mb-4 px-2 pt-0.5 max-sm:mb-0 max-sm:px-4 max-sm:py-3"
      >
        <TextInput
          ref="searchRef"
          v-model="search"
          :placeholder="__('Search Template')"
          class="w-full"
          :debounce="300"
        >
          <template #prefix>
            <span
              class="lucide-search h-4 w-4 text-ink-gray-6"
              aria-hidden="true"
            />
          </template>
        </TextInput>
        <Select
          v-model="currentDoctype"
          class="shrink-0 max-sm:w-32"
          :options="[
            { label: __('All'), value: 'All' },
            { label: __('Lead'), value: 'CRM Lead' },
            { label: __('Deal'), value: 'CRM Deal' },
          ]"
        />
      </div>
      <div
        class="flex items-center py-2 px-4 text-sm text-ink-gray-5 max-sm:hidden"
      >
        <div class="w-4/6">{{ __('Template Name') }}</div>
        <div class="w-1/6">{{ __('For') }}</div>
        <div class="w-1/6">{{ __('Enabled') }}</div>
      </div>
      <div
        class="h-px border-t mx-4 border-outline-elevation-2 max-sm:hidden"
      />
      <ul
        class="overflow-y-auto px-2 max-sm:border-b max-sm:border-outline-gray-1 max-sm:px-0"
      >
        <template v-for="(template, i) in templatesList" :key="template.name">
          <li
            class="flex items-center justify-between p-3 cursor-pointer hover:bg-surface-sidebar rounded-4 max-sm:min-h-14 max-sm:gap-3 max-sm:rounded-none max-sm:px-4 max-sm:py-2"
            @click="() => emit('updateStep', 'edit-template', { ...template })"
          >
            <div
              class="flex flex-col w-4/6 pr-5 max-sm:w-auto max-sm:min-w-0 max-sm:flex-1 max-sm:pr-0"
            >
              <div
                class="text-p-base-medium text-ink-gray-7 truncate max-sm:text-base-medium max-sm:text-ink-gray-9"
              >
                {{ template.name }}
              </div>
              <div class="text-p-sm text-ink-gray-5 truncate max-sm:text-sm">
                <span class="sm:hidden">
                  {{ template.reference_doctype.replace('CRM ', '') }} ·
                </span>
                {{ template.subject }}
              </div>
            </div>
            <div class="text-base text-ink-gray-6 w-1/6 max-sm:hidden">
              {{ template.reference_doctype.replace('CRM ', '') }}
            </div>
            <div
              class="flex items-center justify-between w-1/6 max-sm:w-auto max-sm:shrink-0 max-sm:gap-2"
            >
              <Switch
                v-model="template.enabled"
                size="sm"
                @update:model-value="
                  (val) => toggleEmailTemplate(template, val)
                "
                @click.stop
              />
              <DropdownSheet
                class=""
                :title="template.name"
                :options="getDropdownOptions(template)"
                align="end"
                :button="{
                  icon: 'lucide-more-horizontal',
                  variant: 'ghost',
                  onblur: (e) => {
                    e.stopPropagation()
                    confirmDeleteFor = null
                  },
                }"
                @update:open="(open) => open && (confirmDeleteFor = null)"
                @click.stop
              >
                <template v-if="isPhone" #default>
                  <Button
                    variant="ghost"
                    icon="lucide-more-horizontal"
                    :aria-label="__('More options')"
                  />
                </template>
              </DropdownSheet>
            </div>
          </li>
          <div
            v-if="templatesList.length !== i + 1"
            class="h-px border-t mx-2 border-outline-elevation-2 max-sm:mx-0 max-sm:border-outline-gray-1"
          />
        </template>
        <!-- Load More Button -->
        <div
          v-if="!templates.loading && templates.hasNextPage"
          class="flex justify-center"
        >
          <Button
            class="mt-3.5 p-2"
            :loading="templates.loading"
            :label="__('Load More')"
            icon-left="lucide-refresh-cw"
            @click="() => templates.next()"
          />
        </div>
      </ul>
    </div>
  </div>
</template>
<script setup>
import EmailTemplateIcon from '@/components/Icons/EmailTemplateIcon.vue'
import EmptyState from '../../ListViews/EmptyState.vue'
import Select from '@/components/Controls/Select.vue'
import DropdownSheet from '@/components/DropdownSheet.vue'
import { isPhone } from '@/composables/phone'
import { useBroadcast } from '@/composables/useBroadcast'
import { TextInput, Switch, toast } from 'frappe-ui'
import { ref, computed, inject } from 'vue'
import { ConfirmDelete } from '../../../utils'

const emit = defineEmits(['updateStep'])

const { send } = useBroadcast()

const templates = inject('templates')

const search = ref('')
const currentDoctype = ref('All')
// whose row menu shows "Confirm Delete"
const confirmDeleteFor = ref(null)

const templatesList = computed(() => {
  let list = templates.data || []
  if (search.value) {
    list = list.filter(
      (template) =>
        template.name.toLowerCase().includes(search.value.toLowerCase()) ||
        template.subject.toLowerCase().includes(search.value.toLowerCase()),
    )
  }
  if (currentDoctype.value !== 'All') {
    list = list.filter(
      (template) => template.reference_doctype === currentDoctype.value,
    )
  }
  return list
})

function toggleEmailTemplate(template, enabledVal) {
  templates.setValue.submit(
    {
      name: template.name,
      enabled: enabledVal ? 1 : 0,
    },
    {
      onSuccess: () => {
        toast.success(
          enabledVal
            ? __('Template enabled successfully')
            : __('Template disabled successfully'),
        )
        send('refresh-email-templates')
      },
      onError: (error) => {
        toast.error(error.messages[0] || __('Failed to update template'))
        // Revert the change if there was an error
        template.enabled = !enabledVal
      },
    },
  )
}

function deleteTemplate(template) {
  confirmDeleteFor.value = null
  templates.delete.submit(template.name, {
    onSuccess: () => {
      toast.success(__('Template deleted successfully'))
    },
    onError: (error) => {
      toast.error(error.messages[0] || __('Failed to delete template'))
    },
  })
}

function getDropdownOptions(template) {
  const confirmDelete = computed({
    get: () => confirmDeleteFor.value === template.name,
    set: (confirming) =>
      (confirmDeleteFor.value = confirming ? template.name : null),
  })
  let options = [
    {
      label: __('Duplicate'),
      icon: 'lucide-copy',
      onClick: () => emit('updateStep', 'new-template', { ...template }),
    },
    ...ConfirmDelete({
      onConfirmDelete: () => deleteTemplate(template),
      isConfirmingDelete: confirmDelete,
    }),
  ]

  return options
}
</script>
