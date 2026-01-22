<template>
  <div class="flex h-full flex-col gap-6 p-6 text-ink-gray-8">
    <!-- Header -->
    <div class="flex justify-between px-2 pt-2">
      <div class="flex flex-col gap-1 w-9/12">
        <h2 class="flex gap-2 text-xl font-semibold leading-none h-5">
          {{ __('Email templates') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Add, edit, and manage email templates for various CRM communications',
            )
          }}
        </p>
      </div>
      <div class="flex item-center space-x-2 w-3/12 justify-end">
        <Button
          :label="__('New')"
          icon-left="plus"
          variant="solid"
          @click="emit('updateStep', 'new-template')"
        />
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
      name="email templates"
      description="Add one to get started."
      :icon="EmailTemplateIcon"
    />

    <!-- Email template list -->
    <div
      class="flex flex-col overflow-hidden"
      v-if="!templates.loading && templates.data?.length"
    >
      <div
        v-if="templates.data?.length > 10"
        class="flex items-center justify-between mb-4 px-2 pt-0.5"
      >
        <TextInput
          ref="searchRef"
          v-model="search"
          :placeholder="__('Search template')"
          class="w-1/3"
          :debounce="300"
        >
          <template #prefix>
            <FeatherIcon name="search" class="h-4 w-4 text-ink-gray-6" />
          </template>
        </TextInput>
        <FormControl
          type="select"
          v-model="currentDoctype"
          :options="[
            { label: __('All'), value: 'All' },
            { label: __('Lead'), value: 'CRM Lead' },
            { label: __('Deal'), value: 'CRM Deal' },
          ]"
        />
      </div>
      <div class="flex items-center py-2 px-4 text-sm text-ink-gray-5">
        <div class="w-4/6">{{ __('Template name') }}</div>
        <div class="w-1/6">{{ __('For') }}</div>
        <div class="w-1/6">{{ __('Enabled') }}</div>
      </div>
      <div class="h-px border-t mx-4 border-outline-gray-modals" />
      <ul class="overflow-y-auto px-2">
        <template v-for="(template, i) in templatesList" :key="template.name">
          <li
            class="flex items-center justify-between p-3 cursor-pointer hover:bg-surface-menu-bar rounded"
            @click="() => emit('updateStep', 'edit-template', { ...template })"
          >
            <div class="flex flex-col w-4/6 pr-5">
              <div class="text-p-base font-medium text-ink-gray-7 truncate">
                {{ template.name }}
              </div>
              <div class="text-p-sm text-ink-gray-5 truncate">
                {{ template.subject }}
              </div>
            </div>
            <div class="text-base text-ink-gray-6 w-1/6">
              {{ template.reference_doctype.replace('CRM ', '') }}
            </div>
            <div class="flex items-center justify-between w-1/6">
              <Switch
                size="sm"
                v-model="template.enabled"
                @update:model-value="toggleEmailTemplate(template)"
                @click.stop
              />
              <Dropdown
                class=""
                :options="getDropdownOptions(template)"
                placement="right"
                :button="{
                  icon: 'more-horizontal',
                  variant: 'ghost',
                  onblur: (e) => {
                    e.stopPropagation()
                    confirmDelete = false
                  },
                }"
                @click.stop
              />
            </div>
          </li>
          <div
            v-if="templatesList.length !== i + 1"
            class="h-px border-t mx-2 border-outline-gray-modals"
          />
        </template>
        <!-- Load More Button -->
        <div
          v-if="!templates.loading && templates.hasNextPage"
          class="flex justify-center"
        >
          <Button
            class="mt-3.5 p-2"
            @click="() => templates.next()"
            :loading="templates.loading"
            :label="__('Load more')"
            icon-left="refresh-cw"
          />
        </div>
      </ul>
    </div>
  </div>
</template>
<script setup>
import EmailTemplateIcon from '@/components/Icons/EmailTemplateIcon.vue'
import EmptyState from '../../ListViews/EmptyState.vue'
import {
  TextInput,
  FormControl,
  Switch,
  Dropdown,
  FeatherIcon,
  toast,
} from 'frappe-ui'
import { ref, computed, inject } from 'vue'

const emit = defineEmits(['updateStep'])

const templates = inject('templates')

const search = ref('')
const currentDoctype = ref('All')
const confirmDelete = ref(false)

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

function toggleEmailTemplate(template) {
  templates.setValue.submit(
    {
      name: template.name,
      enabled: template.enabled ? 1 : 0,
    },
    {
      onSuccess: () => {
        toast.success(
          template.enabled
            ? __('Template enabled successfully')
            : __('Template disabled successfully'),
        )
      },
      onError: (error) => {
        toast.error(error.messages[0] || __('Failed to update template'))
        // Revert the change if there was an error
        template.enabled = !template.enabled
      },
    },
  )
}

function deleteTemplate(template) {
  confirmDelete.value = false
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
  let options = [
    {
      label: __('Duplicate'),
      icon: 'copy',
      onClick: () => emit('updateStep', 'new-template', { ...template }),
    },
    {
      label: __('Delete'),
      icon: 'trash-2',
      onClick: (e) => {
        e.preventDefault()
        e.stopPropagation()
        confirmDelete.value = true
      },
      condition: () => !confirmDelete.value,
    },
    {
      label: __('Confirm delete'),
      icon: 'trash-2',
      theme: 'red',
      onClick: () => deleteTemplate(template),
      condition: () => confirmDelete.value,
    },
  ]

  return options
}
</script>
