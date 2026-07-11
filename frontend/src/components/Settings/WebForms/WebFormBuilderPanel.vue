<template>
  <div class="flex h-full flex-col text-ink-gray-8">
    <!-- header -->
    <div class="flex items-center justify-between border-b px-6 py-3">
      <Button
        variant="ghost"
        icon-left="lucide-chevron-left"
        :label="form.title || __('Untitled')"
        size="md"
        class="-ml-4 cursor-pointer !max-w-96 !justify-start !pr-0 text-2xl-semibold no-underline hover:bg-transparent hover:no-underline hover:opacity-70 focus:bg-transparent focus:outline-none focus:ring-0"
        @click="$emit('back')"
      />
      <div class="flex items-center gap-3">
        <Badge v-if="dirty" :label="__('Not Saved')" variant="subtle" theme="orange" />
        <Button
          :label="mode === 'edit' ? __('Preview') : __('Edit')"
          @click="((mode = mode === 'edit' ? 'preview' : 'edit'), resetPreview())"
        >
          <template #prefix>
            <LucideEye v-if="mode === 'edit'" class="h-4 w-4" />
            <LucidePencil v-else class="h-4 w-4" />
          </template>
        </Button>
        <Button variant="solid" :label="__('Update')" :loading="saving" :disabled="!dirty" @click="save" />
      </div>
    </div>

    <div v-if="loaded" class="flex-1 overflow-y-auto p-6">
      <!-- EDIT MODE -->
      <div v-if="mode === 'edit'" class="mx-auto flex max-w-2xl flex-col">
        <!-- form details -->
        <div>
          <div class="flex flex-col gap-1">
            <span class="text-lg-semibold text-ink-gray-8">{{ __('Form details') }}</span>
            <span class="text-p-sm text-ink-gray-6">{{ __('Basic settings for this form.') }}</span>
          </div>
          <div class="mt-3.5 flex flex-col gap-4">
            <div class="grid grid-cols-2 gap-4">
              <FormControl type="text" :label="__('Title')" v-model="form.title" @input="markDirty" />
              <div>
                <div class="mb-1.5 text-sm text-ink-gray-5">{{ __('Route') }}</div>
                <div class="flex items-center gap-1.5">
                  <span class="whitespace-nowrap text-sm text-ink-gray-4">/crm-form/</span>
                  <TextInput class="flex-1" v-model="form.route" @input="markDirty" />
                </div>
              </div>
              <FormControl
                type="select"
                :label="__('Maps to')"
                v-model="form.document_type"
                :options="targetOptions"
                @update:modelValue="onDoctypeChange"
              />
              <FormControl type="text" :label="__('Submit button label')" v-model="form.submit_button_label" @input="markDirty" />
            </div>
            <FormControl type="textarea" :label="__('Description')" :rows="2" v-model="form.description" @input="markDirty" />
            <FormControl
              type="textarea"
              :label="__('Success message')"
              :rows="2"
              v-model="form.success_message"
              :placeholder="__('Shown after a successful submission')"
              @input="markDirty"
            />
          </div>
        </div>

        <hr class="my-8 border-outline-gray-2" />

        <!-- fields -->
        <div>
          <div class="flex items-center justify-between">
            <div class="flex flex-col gap-1">
              <span class="text-lg-semibold text-ink-gray-8">{{ __('Fields') }}</span>
              <span class="text-p-sm text-ink-gray-6">
                {{ inputFieldCount ? __('{0} fields · drag to reorder.', [inputFieldCount]) : __('Add the fields people fill in.') }}
              </span>
            </div>
            <Button :label="__('Add field')" icon-left="plus" @click="openAddField" />
          </div>

          <div v-if="!form.fields.length" class="mt-4 rounded-lg border border-dashed py-8 text-center text-sm text-ink-gray-4">
            {{ __('No fields yet. Click “Add field” to choose from {0} fields.', [docLabel(form.document_type)]) }}
          </div>

          <Draggable
            v-else
            :list="form.fields"
            item-key="fieldname"
            handle=".drag-handle"
            class="mt-4 flex flex-col gap-2"
            ghost-class="opacity-40"
            :animation="150"
            :force-fallback="true"
            :fallback-on-body="false"
            fallback-class="wf-drag-fallback"
            @end="markDirty"
          >
            <template #item="{ element: f, index: i }">
              <div>
              <!-- SECTION BREAK -->
              <div
                v-if="f.fieldtype === 'Section Break'"
                class="flex items-center gap-2 rounded-lg border border-dashed bg-surface-gray-1 px-3 py-2"
              >
                <LucideGripVertical class="drag-handle h-4 w-4 shrink-0 cursor-grab text-ink-gray-4" />
                <span class="shrink-0 text-xs font-medium uppercase tracking-wide text-ink-gray-4">{{ __('Section') }}</span>
                <TextInput class="flex-1" size="sm" v-model="f.label" :placeholder="__('Section title (optional)')" @input="markDirty" />
                <Button variant="ghost" @click="removeField(i)">
                  <template #icon><LucideX class="h-4 w-4 text-ink-gray-5" /></template>
                </Button>
              </div>

              <!-- COLUMN BREAK -->
              <div
                v-else-if="f.fieldtype === 'Column Break'"
                class="flex items-center gap-2 rounded-lg border border-dashed bg-surface-gray-1 px-3 py-2"
              >
                <LucideGripVertical class="drag-handle h-4 w-4 shrink-0 cursor-grab text-ink-gray-4" />
                <span class="flex-1 text-xs font-medium uppercase tracking-wide text-ink-gray-4">{{ __('Column break') }}</span>
                <Button variant="ghost" @click="removeField(i)">
                  <template #icon><LucideX class="h-4 w-4 text-ink-gray-5" /></template>
                </Button>
              </div>

              <!-- FIELD -->
              <div v-else class="rounded-lg border">
                <div class="flex items-center gap-2 px-3 py-2.5">
                  <LucideGripVertical class="drag-handle h-4 w-4 shrink-0 cursor-grab text-ink-gray-4" />
                  <div class="min-w-0 flex-1 cursor-pointer" @click="toggle(i)">
                    <div class="truncate text-base text-ink-gray-8">
                      {{ f.label }}<span v-if="f.reqd" class="text-ink-red-5">*</span>
                    </div>
                    <div class="truncate text-xs text-ink-gray-4">{{ f.fieldname }} · {{ f.fieldtype }}</div>
                  </div>
                  <Button variant="ghost" @click="toggle(i)">
                    <template #icon>
                      <LucideChevronDown class="h-4 w-4 transition-transform" :class="{ 'rotate-180': expanded === i }" />
                    </template>
                  </Button>
                  <Button variant="ghost" @click="removeField(i)">
                    <template #icon><LucideX class="h-4 w-4 text-ink-gray-5" /></template>
                  </Button>
                </div>
                <div v-if="expanded === i" class="border-t bg-surface-gray-1 px-3 py-3">
                  <div class="flex items-center justify-between py-1">
                    <span class="text-sm text-ink-gray-7">{{ __('Required') }}</span>
                    <Switch v-model="f.reqd" @update:modelValue="markDirty" />
                  </div>
                  <div class="mt-2 grid grid-cols-2 gap-3">
                    <FormControl type="text" :label="__('Label')" v-model="f.label" @input="markDirty" />
                    <FormControl type="text" :label="__('Placeholder')" v-model="f.placeholder" @input="markDirty" />
                  </div>
                  <FormControl
                    type="text"
                    class="mt-3"
                    :label="__('Description')"
                    v-model="f.field_description"
                    :placeholder="__('Helper text under the field')"
                    @input="markDirty"
                  />
                  <div v-if="f.fieldtype === 'Select' && optionList(f).length" class="mt-3">
                    <div class="mb-1.5 text-sm text-ink-gray-5">{{ __('Options') }}</div>
                    <div class="flex flex-wrap gap-1.5">
                      <span
                        v-for="o in optionList(f)"
                        :key="o"
                        class="rounded bg-surface-white px-2 py-1 text-xs text-ink-gray-7 ring-1 ring-outline-gray-2"
                      >
                        {{ o }}
                      </span>
                    </div>
                    <p class="mt-1.5 text-xs text-ink-gray-4">
                      {{ __('Choices come from the {0} field on {1}.', [f.fieldname, docLabel(form.document_type)]) }}
                    </p>
                  </div>
                </div>
              </div>
              </div>
            </template>
          </Draggable>
        </div>

        <hr class="my-8 border-outline-gray-2" />

        <!-- publish -->
        <div>
          <div class="flex items-center justify-between">
            <div class="flex flex-col gap-1 pr-4">
              <span class="text-lg-semibold text-ink-gray-8">{{ __('Publish') }}</span>
              <span class="text-p-sm text-ink-gray-6">
                {{ form.published ? __('This form is live and accepting submissions.') : __('Turn on to make this form public.') }}
              </span>
            </div>
            <Switch v-model="publishedModel" />
          </div>
          <div v-if="form.published" class="mt-4 flex items-center gap-2">
            <TextInput class="flex-1" size="sm" readonly :modelValue="publicUrl">
              <template #suffix>
                <button
                  class="flex text-ink-gray-5 transition-colors hover:text-ink-gray-8"
                  :title="__('Copy link')"
                  @click="copy(publicUrl)"
                >
                  <LucideCopy class="h-4 w-4" />
                </button>
              </template>
            </TextInput>
            <Button :label="__('Embed')" @click="((shareTab = 'iframe'), (shareOpen = true))">
              <template #prefix><LucideShare2 class="h-4 w-4" /></template>
            </Button>
          </div>
        </div>
      </div>

      <!-- PREVIEW MODE -->
      <div v-else class="mx-auto max-w-2xl">
        <div class="mb-3 flex items-center justify-end">
          <a
            :href="publicUrl"
            target="_blank"
            class="flex items-center gap-1 text-sm text-ink-gray-5 hover:text-ink-gray-8"
          >
            <LucideExternalLink class="h-3.5 w-3.5" />
            {{ __('Open live form') }}
          </a>
        </div>
        <div class="rounded-xl border bg-surface-white p-7">
          <!-- simulated success screen -->
          <div v-if="previewSubmitted" class="flex flex-col items-center gap-3 py-10 text-center">
            <div class="flex h-12 w-12 items-center justify-center rounded-full bg-surface-green-2 text-ink-green-3">
              <LucideCheck class="h-6 w-6" />
            </div>
            <div class="text-lg font-semibold text-ink-gray-9">
              {{ form.success_message || __('Thank you!') }}
            </div>
            <Button :label="__('Preview again')" @click="resetPreview" />
          </div>

          <template v-else>
          <div class="text-lg font-semibold text-ink-gray-9">{{ form.title || __('Form title') }}</div>
          <div v-if="form.description" class="mt-1 text-sm text-ink-gray-6">{{ form.description }}</div>
          <div class="mt-5 flex flex-col gap-5">
            <div v-for="(section, si) in layout" :key="si">
              <div v-if="section.label" class="mb-3 text-sm font-semibold text-ink-gray-8">{{ section.label }}</div>
              <div class="grid gap-x-5" :style="{ gridTemplateColumns: `repeat(${section.columns.length}, minmax(0,1fr))` }">
                <div v-for="(col, ci) in section.columns" :key="ci" class="flex flex-col gap-4">
                  <div v-for="f in col" :key="f.fieldname">
                    <div v-if="f.fieldtype !== 'Check'" class="mb-1.5 text-sm text-ink-gray-5">
                      {{ f.label }}<span v-if="f.reqd" class="text-ink-red-5">*</span>
                    </div>
                    <FormControl
                      v-if="['Small Text', 'Text', 'Long Text'].includes(f.fieldtype)"
                      type="textarea"
                      v-model="previewModel[f.fieldname]"
                      :placeholder="f.placeholder"
                    />
                    <FormControl
                      v-else-if="f.fieldtype === 'Select'"
                      type="select"
                      v-model="previewModel[f.fieldname]"
                      :options="selectOptions(f)"
                      :placeholder="f.placeholder || __('Select an option')"
                    />
                    <div v-else-if="f.fieldtype === 'Check'" class="flex items-center gap-2">
                      <FormControl type="checkbox" v-model="previewModel[f.fieldname]" />
                      <span class="text-sm text-ink-gray-5">{{ f.label }}<span v-if="f.reqd" class="text-ink-red-5">*</span></span>
                    </div>
                    <FormControl v-else :type="inputType(f)" v-model="previewModel[f.fieldname]" :placeholder="f.placeholder" />
                    <div v-if="f.field_description" class="mt-1 text-sm text-ink-gray-4">{{ f.field_description }}</div>
                  </div>
                </div>
              </div>
            </div>
            <div v-if="!inputFieldCount" class="text-sm text-ink-gray-4">
              {{ __('Add fields to see them here.') }}
            </div>
            <Button
              variant="solid"
              size="md"
              class="mt-1 w-full"
              :label="form.submit_button_label || __('Submit')"
              @click="previewSubmitted = true"
            />
          </div>
          </template>
        </div>
      </div>
    </div>

    <!-- add field dialog -->
    <Dialog v-model="addOpen" :options="{ title: __('Add field') }">
      <template #body-content>
        <div class="mb-3 flex gap-2">
          <Button class="flex-1" :label="__('Section break')" @click="addBreak('Section Break')">
            <template #prefix><LucideRows3 class="h-4 w-4" /></template>
          </Button>
          <Button class="flex-1" :label="__('Column break')" @click="addBreak('Column Break')">
            <template #prefix><LucideColumns3 class="h-4 w-4" /></template>
          </Button>
        </div>
        <div class="mb-2 text-xs font-medium uppercase tracking-wide text-ink-gray-4">{{ __('Fields') }}</div>
        <FormControl type="text" v-model="fieldQuery" :placeholder="__('Search fields…')" class="mb-2">
          <template #prefix><LucideSearch class="h-4 w-4 text-ink-gray-4" /></template>
        </FormControl>
        <div class="flex max-h-72 flex-col gap-0.5 overflow-y-auto">
          <button
            v-for="af in filteredAvailable"
            :key="af.fieldname"
            class="flex flex-col rounded px-2 py-1.5 text-left leading-tight hover:bg-surface-gray-2"
            @click="addField(af)"
          >
            <span class="text-base text-ink-gray-8">{{ af.label }}</span>
            <span class="mt-0.5 text-xs text-ink-gray-4">{{ af.fieldname }} · {{ af.fieldtype }}</span>
          </button>
          <div v-if="!filteredAvailable.length" class="px-2 py-6 text-center text-sm text-ink-gray-4">
            {{ __('No fields left to add') }}
          </div>
        </div>
        <p class="mt-3 border-t pt-3 text-xs text-ink-gray-4">
          {{ __('Only fields on {0} show here. Add a custom field to the DocType first.', [docLabel(form.document_type)]) }}
        </p>
      </template>
    </Dialog>

    <!-- share dialog -->
    <Dialog v-model="shareOpen" :options="{ title: __('Embed this form') }">
      <template #body-content>
        <p v-if="!form.published" class="mb-3 text-sm text-ink-gray-5">
          {{ __('Publish the form to make this embed live.') }}
        </p>
        <div class="mb-3 flex gap-5 border-b text-sm">
          <button
            v-for="t in shareTabs"
            :key="t.key"
            class="-mb-px border-b-2 pb-2 transition-colors focus:outline-none"
            :class="shareTab === t.key ? 'border-ink-gray-9 font-medium text-ink-gray-9' : 'border-transparent text-ink-gray-5 hover:text-ink-gray-7'"
            @click="shareTab = t.key"
          >
            {{ t.label }}
          </button>
        </div>

        <div class="flex min-h-[132px] flex-col">
          <textarea
            readonly
            rows="4"
            class="w-full resize-none rounded-md border border-outline-gray-2 bg-surface-gray-1 px-3 py-2 font-mono text-xs text-ink-gray-7 outline-none"
            :value="shareSnippet"
          />
          <div class="mt-2 flex items-center justify-between">
            <p class="text-xs text-ink-gray-4">
              {{ shareTab === 'iframe' ? __('Paste into any HTML page.') : __('Drop this script where the form should appear.') }}
            </p>
            <Button :label="copied ? __('Copied') : __('Copy')" @click="copy(shareSnippet)" />
          </div>
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import {
  Button,
  Badge,
  Switch,
  TextInput,
  FormControl,
  Dialog,
  call,
  toast,
  createResource,
} from 'frappe-ui'
import LucideCopy from '~icons/lucide/copy'
import Draggable from 'vuedraggable'
import LucideChevronDown from '~icons/lucide/chevron-down'
import LucideGripVertical from '~icons/lucide/grip-vertical'
import LucideX from '~icons/lucide/x'
import LucideShare2 from '~icons/lucide/share-2'
import LucideEye from '~icons/lucide/eye'
import LucidePencil from '~icons/lucide/pencil'
import LucideSearch from '~icons/lucide/search'
import LucideExternalLink from '~icons/lucide/external-link'
import LucideCheck from '~icons/lucide/check'
import LucideRows3 from '~icons/lucide/rows-3'
import LucideColumns3 from '~icons/lucide/columns-3'
import { ref, reactive, computed } from 'vue'

const BREAK_TYPES = ['Section Break', 'Column Break']

const props = defineProps({ name: { type: String, required: true } })
const emit = defineEmits(['back', 'saved'])

const targetOptions = [
  { label: 'Lead', value: 'CRM Lead' },
  { label: 'Deal', value: 'CRM Deal' },
]
const docLabel = (dt) => targetOptions.find((o) => o.value === dt)?.label || dt

const loaded = ref(false)
const saving = ref(false)
const dirty = ref(false)
const mode = ref('edit') // edit | preview
const expanded = ref(null)
const addOpen = ref(false)
const shareOpen = ref(false)
const fieldQuery = ref('')
const copied = ref(false)
const previewModel = reactive({}) // throwaway values so the preview is interactive
const previewSubmitted = ref(false)

function resetPreview() {
  previewSubmitted.value = false
  Object.keys(previewModel).forEach((k) => delete previewModel[k])
}

const form = reactive({
  name: props.name,
  title: '',
  route: '',
  document_type: 'CRM Lead',
  description: '',
  submit_button_label: 'Submit',
  success_message: '',
  published: 0,
  fields: [],
})

const publishedModel = computed({
  get: () => !!form.published,
  set: (v) => {
    form.published = v ? 1 : 0
    markDirty()
  },
})
const publicUrl = computed(() => `${window.location.origin}/crm-form/${form.route}`)

const shareTab = ref('iframe')
const shareTabs = [
  { key: 'iframe', label: 'iframe' },
  { key: 'javascript', label: 'JavaScript' },
]
const shareSnippet = computed(() => {
  const url = publicUrl.value
  const id = `crm-web-form-${form.route || 'form'}`
  if (shareTab.value === 'iframe') {
    return `<iframe src="${url}" width="100%" height="640" style="border:0" title="${form.title || 'Web form'}"></iframe>`
  }
  if (shareTab.value === 'javascript') {
    return (
      `<div id="${id}"></div>\n` +
      `<script>\n` +
      `  (function () {\n` +
      `    var f = document.createElement('iframe');\n` +
      `    f.src = '${url}';\n` +
      `    f.width = '100%'; f.height = '640'; f.style.border = '0';\n` +
      `    document.getElementById('${id}').appendChild(f);\n` +
      `  })();\n` +
      `<\/script>`
    )
  }
  return url
})

function markDirty() {
  dirty.value = true
}
function toggle(i) {
  expanded.value = expanded.value === i ? null : i
}
function optionList(f) {
  return (f.options || '').split('\n').filter(Boolean)
}
function selectOptions(f) {
  const opts = optionList(f).map((o) => ({ label: o, value: o }))
  return [{ label: __('Select an option'), value: '' }, ...opts]
}
function inputType(f) {
  if (f.options === 'Email') return 'email'
  if (['Int', 'Float', 'Currency'].includes(f.fieldtype)) return 'number'
  if (f.fieldtype === 'Date') return 'date'
  if (f.fieldtype === 'Datetime') return 'datetime-local'
  return 'text'
}

const inputFieldCount = computed(
  () => form.fields.filter((f) => !BREAK_TYPES.includes(f.fieldtype)).length,
)

// group fields into sections -> columns for the preview
const layout = computed(() => {
  const sections = []
  let cur = { label: null, columns: [[]] }
  for (const f of form.fields) {
    if (f.fieldtype === 'Section Break') {
      sections.push(cur)
      cur = { label: f.label || null, columns: [[]] }
    } else if (f.fieldtype === 'Column Break') {
      cur.columns.push([])
    } else {
      cur.columns[cur.columns.length - 1].push(f)
    }
  }
  sections.push(cur)
  return sections.filter((s) => s.label || s.columns.some((c) => c.length))
})

function uid(fieldtype) {
  const p = fieldtype === 'Section Break' ? 'section_break_' : 'column_break_'
  return p + Math.random().toString(36).slice(2, 8)
}
function addBreak(fieldtype) {
  form.fields.push({
    fieldname: uid(fieldtype),
    label: '',
    fieldtype,
    options: '',
    reqd: false,
    placeholder: '',
    field_description: '',
  })
  markDirty()
  addOpen.value = false
}

// load
createResource({
  url: 'frappe.client.get',
  params: { doctype: 'CRM Web Form', name: props.name },
  auto: true,
  onSuccess: (doc) => {
    form.title = doc.title || ''
    form.route = doc.route || ''
    form.document_type = doc.document_type || 'CRM Lead'
    form.description = doc.description || ''
    form.submit_button_label = doc.submit_button_label || 'Submit'
    form.success_message = doc.success_message || ''
    form.published = doc.published || 0
    form.fields = (doc.fields || []).map((f) => ({
      name: f.name,
      fieldname: f.fieldname,
      label: f.label,
      fieldtype: f.fieldtype,
      options: f.options,
      reqd: !!f.reqd,
      placeholder: f.placeholder,
      field_description: f.field_description,
    }))
    loaded.value = true
    availableFields.reload()
  },
})

const availableFields = createResource({
  url: 'crm.api.web_form.get_form_fields',
  makeParams: () => ({ document_type: form.document_type }),
})

const filteredAvailable = computed(() => {
  const used = new Set(form.fields.map((f) => f.fieldname))
  const q = fieldQuery.value.toLowerCase()
  return (availableFields.data || [])
    .filter((f) => !used.has(f.fieldname))
    .filter((f) => !q || f.label.toLowerCase().includes(q) || f.fieldname.includes(q))
})

function openAddField() {
  fieldQuery.value = ''
  addOpen.value = true
}
function addField(af) {
  form.fields.push({
    fieldname: af.fieldname,
    label: af.label,
    fieldtype: af.fieldtype,
    options: af.options,
    reqd: !!af.reqd,
    placeholder: '',
    field_description: '',
  })
  markDirty()
  addOpen.value = false
}
function removeField(i) {
  form.fields.splice(i, 1)
  if (expanded.value === i) expanded.value = null
  markDirty()
}

async function onDoctypeChange() {
  markDirty()
  expanded.value = null
  await availableFields.reload()
  const valid = new Set((availableFields.data || []).map((f) => f.fieldname))
  const before = form.fields.length
  form.fields = form.fields.filter(
    (f) => BREAK_TYPES.includes(f.fieldtype) || valid.has(f.fieldname),
  )
  const dropped = before - form.fields.length
  if (dropped) {
    toast.info(__('{0} field(s) removed — not available on {1}', [dropped, docLabel(form.document_type)]))
  }
}

function copy(text) {
  navigator.clipboard?.writeText(text)
  copied.value = true
  toast.success(__('Copied to clipboard'))
  setTimeout(() => (copied.value = false), 1500)
}

async function save() {
  saving.value = true
  try {
    const doc = await call('crm.api.web_form.save_web_form', {
      name: form.name,
      form: {
        title: form.title,
        route: form.route,
        document_type: form.document_type,
        description: form.description,
        submit_button_label: form.submit_button_label,
        success_message: form.success_message,
        published: form.published ? 1 : 0,
        fields: form.fields.map((f) => ({
          fieldname: f.fieldname,
          label: f.label,
          fieldtype: f.fieldtype,
          options: f.options,
          reqd: f.reqd ? 1 : 0,
          placeholder: f.placeholder,
          field_description: f.field_description,
        })),
      },
    })
    form.route = doc.route
    ;(doc.fields || []).forEach((df, i) => {
      if (form.fields[i]) form.fields[i].name = df.name
    })
    dirty.value = false
    toast.success(__('Saved'))
    emit('saved')
  } catch (e) {
    toast.error(e?.messages?.[0] || e?.message || __('Could not save'))
  } finally {
    saving.value = false
  }
}
</script>

<style>
/* Hide Sortable's floating drag clone so reordering stays contained to the
   fields list — only the in-list placeholder moves, never a copy that can
   drift outside the section/modal. */
.wf-drag-fallback {
  opacity: 0 !important;
}
</style>
