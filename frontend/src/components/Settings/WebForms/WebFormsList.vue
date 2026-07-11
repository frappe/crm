<template>
  <div class="flex h-full flex-col gap-6 p-6 text-ink-gray-8">
    <!-- Header -->
    <div class="flex justify-between px-2 pt-2">
      <div class="flex flex-col gap-1 w-9/12">
        <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
          {{ __('Web Forms') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{ __('Capture leads and deals from public forms you embed on your website.') }}
        </p>
      </div>
      <div class="flex item-center space-x-2 w-3/12 justify-end">
        <Button :label="__('New')" icon-left="lucide-plus" variant="solid" @click="openCreate" />
      </div>
    </div>

    <!-- List -->
    <div class="flex h-full flex-col overflow-y-auto">
      <div v-if="forms.loading && !forms.data" class="flex items-center justify-center mt-12">
        <LoadingIndicator class="w-4" />
      </div>
      <EmptyState
        v-else-if="forms.data?.length === 0"
        :title="__('No web forms yet')"
        :description="__('Create one to start capturing leads.')"
        :icon="h(LucideTextCursorInput)"
      />
      <div v-else class="w-full">
        <div class="flex items-center p-2 text-sm text-ink-gray-5">
          <div class="w-6/12">{{ __('Form') }}</div>
          <div class="w-3/12">{{ __('Maps to') }}</div>
          <div class="w-3/12">{{ __('Published') }}</div>
        </div>
        <div class="h-px border-t mx-2 border-outline-elevation-2" />
        <template v-for="(form, i) in forms.data" :key="form.name">
          <div class="flex w-full items-center rounded p-2 hover:bg-surface-gray-2">
            <div class="w-6/12 min-w-0 cursor-pointer" @click="$emit('open', form.name)">
              <div class="truncate text-base text-ink-gray-8">{{ form.title }}</div>
              <div class="truncate text-p-sm text-ink-gray-4">/crm-form/{{ form.route }}</div>
            </div>
            <div class="w-3/12 cursor-pointer text-base text-ink-gray-7" @click="$emit('open', form.name)">
              {{ docLabel(form.document_type) }}
            </div>
            <div class="flex w-3/12 items-center justify-between">
              <Switch size="sm" :modelValue="!!form.published" @update:modelValue="(v) => togglePublished(form, v)" />
              <Dropdown placement="right" :options="rowOptions(form)">
                <Button icon="lucide-more-horizontal" variant="ghost" @click="isConfirmingDelete = false" />
              </Dropdown>
            </div>
          </div>
          <hr v-if="forms.data.length !== i + 1" class="mx-2" />
        </template>
      </div>
    </div>
  </div>

  <!-- create dialog -->
  <Dialog v-model="showCreate" :options="{ title: __('New form') }">
    <template #body-content>
      <div class="flex flex-col gap-4">
        <FormControl
          v-model="draft.title"
          type="text"
          :label="__('Form title')"
          :placeholder="__('Contact sales')"
          @input="onTitleInput"
        />
        <div>
          <div class="mb-1.5 text-sm text-ink-gray-5">{{ __('Route') }}</div>
          <div class="flex items-center gap-1.5">
            <span class="whitespace-nowrap text-sm text-ink-gray-4">/crm-form/</span>
            <TextInput v-model="draft.route" class="flex-1" :placeholder="__('contact-sales')" />
          </div>
        </div>
        <FormControl v-model="draft.document_type" type="select" :label="__('Maps to')" :options="targetOptions" />
        <ErrorMessage v-if="createError" :message="createError" />
      </div>
    </template>
    <template #actions>
      <Button class="w-full" variant="solid" :label="__('Create form')" :loading="creating" @click="createForm" />
    </template>
  </Dialog>
</template>

<script setup>
import EmptyState from '@/components/ListViews/EmptyState.vue'
import {
  Button,
  Switch,
  Dropdown,
  Dialog,
  FormControl,
  TextInput,
  ErrorMessage,
  LoadingIndicator,
  createListResource,
  call,
  toast,
} from 'frappe-ui'
import LucideTextCursorInput from '~icons/lucide/text-cursor-input'
import { ref, reactive, h } from 'vue'
import { ConfirmDelete } from '../../../utils'

const emit = defineEmits(['open'])

const isConfirmingDelete = ref(false)

const targetOptions = [
  { label: 'Lead', value: 'CRM Lead' },
  { label: 'Deal', value: 'CRM Deal' },
]
const docLabel = (dt) => targetOptions.find((o) => o.value === dt)?.label || dt

const forms = createListResource({
  doctype: 'CRM Web Form',
  fields: ['name', 'title', 'route', 'document_type', 'published', 'modified'],
  orderBy: 'modified desc',
  pageLength: 200,
  auto: true,
})

// create
const showCreate = ref(false)
const creating = ref(false)
const createError = ref('')
const draft = reactive({ title: '', route: '', document_type: 'CRM Lead' })
let routeEdited = false

function slugify(v) {
  return (v || '').toString().trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '')
}
function openCreate() {
  draft.title = ''
  draft.route = ''
  draft.document_type = 'CRM Lead'
  routeEdited = false
  createError.value = ''
  showCreate.value = true
}
function onTitleInput(e) {
  if (!routeEdited) draft.route = slugify(e?.target?.value ?? draft.title)
}
async function createForm() {
  createError.value = ''
  const route = slugify(draft.route || draft.title)
  if (!draft.title || !route) {
    createError.value = __('Title and route are required')
    return
  }
  creating.value = true
  try {
    const doc = await forms.insert.submit({
      title: draft.title,
      route,
      document_type: draft.document_type,
    })
    showCreate.value = false
    emit('open', doc.name)
  } catch (e) {
    createError.value = e?.messages?.[0] || e?.message || __('Could not create form')
  } finally {
    creating.value = false
  }
}

async function togglePublished(form, value) {
  try {
    await call('frappe.client.set_value', {
      doctype: 'CRM Web Form',
      name: form.name,
      fieldname: 'published',
      value: value ? 1 : 0,
    })
    form.published = value ? 1 : 0
    toast.success(value ? __('Form published') : __('Form unpublished'))
  } catch (e) {
    forms.reload()
    toast.error(e?.messages?.[0] || __('Could not update form'))
  }
}

function copyLink(form) {
  const url = `${window.location.origin}/crm-form/${form.route}`
  navigator.clipboard?.writeText(url)
  toast.success(__('Copied to clipboard'))
}

async function deleteForm(form) {
  await call('frappe.client.delete', { doctype: 'CRM Web Form', name: form.name })
  forms.reload()
  toast.success(__('Form deleted'))
}

function rowOptions(form) {
  return [
    { label: __('Edit'), icon: 'edit-2', onClick: () => emit('open', form.name) },
    { label: __('Copy link'), icon: 'link', onClick: () => copyLink(form) },
    ...ConfirmDelete({
      isConfirmingDelete,
      onConfirmDelete: () => deleteForm(form),
    }),
  ]
}

defineExpose({ reload: () => forms.reload() })
</script>
