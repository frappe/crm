<template>
  <div class="flex h-full flex-col gap-6 p-8 text-ink-gray-8">
    <!-- Header -->
    <div class="flex justify-between">
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
        <Button :label="__('New')" icon-left="plus" variant="solid" />
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
    <div
      v-if="!templates.loading && !templates.data?.length"
      class="flex justify-between w-full h-full"
    >
      <div
        class="text-ink-gray-4 border border-dashed rounded w-full flex items-center justify-center"
      >
        {{ __('No email templates found') }}
      </div>
    </div>

    <!-- Email template list -->
    <div
      class="flex flex-col overflow-hidden"
      v-if="!templates.loading && templates.data?.length"
    >
      <div
        v-if="templates.data?.length > 10"
        class="flex items-center justify-between mb-4"
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
      <div class="flex items-center p-2 text-sm border-b text-ink-gray-5">
        <div class="w-4/6">{{ __('Template name') }}</div>
        <div class="w-1/6">{{ __('For') }}</div>
        <div class="w-1/6">{{ __('Enabled') }}</div>
      </div>
      <ul class="divide-y divide-outline-gray-modals overflow-y-auto">
        <template v-for="template in templatesList" :key="template.name">
          <li class="flex items-center justify-between px-2 py-3">
            <div class="flex flex-col w-4/6 pr-5">
              <div class="text-base font-medium text-ink-gray-7">
                {{ template.name }}
              </div>
              <div class="text-p-base text-ink-gray-5 truncate">
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
              />
              <Dropdown
                :options="[
                  {
                    label: __('Edit'),
                    icon: 'edit-2',
                    onClick: () => {},
                  },
                  {
                    label: __('Duplicate'),
                    icon: 'copy',
                    onClick: () => {},
                  },
                  {
                    label: __('Delete'),
                    icon: 'trash-2',
                    onClick: () => {},
                  },
                ]"
                placement="right"
                :button="{
                  icon: 'more-horizontal',
                  variant: 'ghost',
                }"
              />
            </div>
          </li>
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
            :label="__('Load More')"
            icon-left="refresh-cw"
          />
        </div>
      </ul>
    </div>
  </div>
</template>
<script setup>
import {
  TextInput,
  FormControl,
  Switch,
  createListResource,
  Dropdown,
} from 'frappe-ui'
import { ref, computed } from 'vue'

const templates = createListResource({
  type: 'list',
  doctype: 'Email Template',
  cache: 'emailTemplates',
  fields: [
    'name',
    'enabled',
    'use_html',
    'reference_doctype',
    'subject',
    'response',
    'response_html',
    'modified',
    'owner',
  ],
  auto: true,
  filters: { reference_doctype: ['in', ['CRM Lead', 'CRM Deal']] },
  orderBy: 'modified desc',
  pageLength: 20,
})

const search = ref('')
const currentDoctype = ref('All')

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
  templates.setValue.submit({
    name: template.name,
    enabled: template.enabled ? 1 : 0,
  })
}
</script>
