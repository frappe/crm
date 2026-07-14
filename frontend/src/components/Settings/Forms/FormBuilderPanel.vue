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
        <Button
          :label="mode === 'edit' ? __('Preview') : __('Edit')"
          @click="(mode = mode === 'edit' ? 'preview' : 'edit'), resetPreview()"
        >
          <template #prefix>
            <LucideEye v-if="mode === 'edit'" class="h-4 w-4" />
            <LucidePencil v-else class="h-4 w-4" />
          </template>
        </Button>
        <Button
          variant="solid"
          :label="form.published ? __('Unpublish') : __('Publish')"
          :loading="publishing"
          @click="togglePublish"
        />
      </div>
    </div>

    <div v-if="loaded" class="flex-1 overflow-y-auto px-6 pb-6">
      <!-- EDIT MODE -->
      <div v-if="mode === 'edit'" class="wf-tabs mx-auto max-w-2xl">
        <Tabs v-model="tabIndex" as="div" :tabs="tabs">
          <template #tab-panel="{ tab }">
            <!-- EDITOR TAB -->
            <div v-if="tab.name === 'editor'" class="pt-5">
              <!-- form masthead (title + description) — typed right on the canvas -->
              <div class="mb-5 px-1">
                <input
                  v-model="form.title"
                  :placeholder="__('Form title')"
                  class="w-full border-0 bg-transparent p-0 text-2xl font-semibold leading-tight text-ink-gray-9 placeholder:text-ink-gray-4 focus:outline-none focus:ring-0"
                  @input="onTitleInput"
                />
                <textarea
                  ref="descInput"
                  v-model="form.description"
                  :placeholder="
                    __('Add a description to help people fill out this form')
                  "
                  rows="1"
                  class="mt-2 w-full resize-none border-0 bg-transparent p-0 text-base leading-relaxed text-ink-gray-6 placeholder:text-ink-gray-4 focus:outline-none focus:ring-0"
                  @input="(e) => (autoGrow(e.target), markDirty())"
                />
                <hr class="mt-5 border-outline-gray-2" />
              </div>

              <!-- native-style layout: draggable section boxes → dashed columns → field cards -->
              <div
                class="flex flex-col gap-3"
                :class="{ 'select-none': dragging }"
              >
                <Draggable
                  :list="sections"
                  :item-key="sectionKey"
                  handle=".section-handle"
                  group="wf-sections"
                  class="flex flex-col gap-3"
                  ghost-class="opacity-40"
                  :force-fallback="true"
                  :fallback-on-body="false"
                  fallback-class="wf-drag-fallback"
                  :animation="120"
                  @start="dragging = true"
                  @end="onSortEnd"
                >
                  <template #item="{ element: sec }">
                    <div
                      class="flex flex-col gap-1.5 rounded bg-surface-gray-2 p-2.5"
                    >
                      <div class="flex h-7 items-center justify-between">
                        <div
                          class="flex items-center gap-2 text-base-medium text-ink-gray-9"
                        >
                          <DragVerticalIcon
                            class="section-handle h-3.5 shrink-0 cursor-grab text-ink-gray-3"
                          />
                          <input
                            v-if="sec.editingLabel"
                            :ref="(el) => el && el.focus()"
                            v-model="sec.secField.label"
                            :placeholder="__('Section title')"
                            class="min-w-0 flex-1 border-0 bg-transparent p-0 text-base-medium text-ink-gray-9 placeholder:font-normal placeholder:italic placeholder:text-ink-gray-4 focus:outline-none focus:ring-0"
                            @blur="sec.editingLabel = false"
                            @keydown.enter="sec.editingLabel = false"
                            @input="markDirty"
                          />
                          <span
                            v-else
                            class="cursor-text truncate"
                            :class="{
                              'italic text-ink-gray-4': !sec.secField.label,
                            }"
                            @click="sec.editingLabel = true"
                          >
                            {{ sec.secField.label || __('Section title') }}
                          </span>
                        </div>
                        <div class="flex items-center gap-1.5">
                          <span
                            v-if="sectionFieldCount(sec)"
                            class="rounded bg-surface-gray-3 px-1.5 py-0.5 text-xs leading-none text-ink-gray-4"
                          >
                            {{ sectionFieldCount(sec) }}
                            {{
                              sectionFieldCount(sec) === 1
                                ? __('field')
                                : __('fields')
                            }}
                          </span>
                          <Dropdown :options="sectionMenu(sec)">
                            <template #default>
                              <Button variant="ghost">
                                <span
                                  class="lucide-more-horizontal h-4"
                                  aria-hidden="true"
                                />
                              </Button>
                            </template>
                          </Dropdown>
                        </div>
                      </div>
                      <div class="flex gap-2">
                        <div
                          v-for="col in sec.columns"
                          :key="columnKey(col)"
                          class="flex flex-1 flex-col gap-1.5 rounded border border-dashed border-outline-gray-2 bg-surface-elevation-2 p-2"
                        >
                          <Draggable
                            :list="col.items"
                            group="wf-fields"
                            item-key="fieldname"
                            handle=".drag-handle"
                            class="flex min-h-[34px] flex-1 flex-col gap-1.5"
                            ghost-class="opacity-40"
                            :force-fallback="true"
                            :fallback-on-body="false"
                            fallback-class="wf-drag-fallback"
                            :animation="120"
                            @start="dragging = true"
                            @end="onSortEnd"
                          >
                            <template #item="{ element: f }">
                              <FieldCard
                                :field="f"
                                :expanded="expanded === f.fieldname"
                                :locked="isMandatory(f.fieldname)"
                                @open="open(f)"
                                @toggle="toggle(f)"
                                @remove="removeField(f)"
                                @update="(patch) => updateField(f, patch)"
                              />
                            </template>
                          </Draggable>
                          <Autocomplete
                            :options="availableFieldOptions"
                            value=""
                            :placeholder="__('Search fields…')"
                            @change="(e) => addFieldToColumn(col, e)"
                          >
                            <template #target="{ togglePopover }">
                              <Button
                                class="!h-8 w-full !bg-surface-elevation-2"
                                variant="outline"
                                :label="__('Add Field')"
                                icon-left="plus"
                                @click="togglePopover()"
                              />
                            </template>
                          </Autocomplete>
                        </div>
                      </div>
                    </div>
                  </template>
                </Draggable>

                <Button
                  class="!h-8 w-full"
                  variant="subtle"
                  :label="__('Add Section')"
                  icon-left="plus"
                  @click="addBreak('Section Break')"
                />
              </div>

              <!-- hidden required fields: kept off the form, a default is applied
                   on submission so the record can still be created -->
              <div v-if="hiddenFields.length" class="mt-6">
                <div
                  class="mb-2 flex items-center gap-1.5 text-base-medium text-ink-gray-7"
                >
                  <LucideEyeOff class="h-3.5 w-3.5 text-ink-gray-5" />
                  {{ __('Hidden required fields') }}
                </div>
                <div class="rounded bg-surface-gray-2 p-2.5">
                  <p class="mb-2.5 text-p-sm text-ink-gray-5">
                    {{
                      __(
                        "These fields aren't shown to users. Default values are used when the form is submitted.",
                      )
                    }}
                  </p>
                  <div class="flex flex-col gap-2">
                    <div
                      v-for="h in hiddenFields"
                      :key="h.fieldname"
                      class="flex items-center gap-2.5 rounded border border-outline-gray-2 bg-surface-elevation-2 px-2.5 py-2"
                    >
                      <component
                        :is="fieldTypeIcon(h)"
                        class="h-4 w-4 shrink-0 text-ink-gray-5"
                      />
                      <span
                        class="flex-1 truncate text-base text-ink-gray-8"
                        :title="h.label"
                        >{{ h.label }}</span
                      >
                      <div class="w-52 shrink-0">
                        <FormControl
                          v-if="hiddenIsSelect(h)"
                          type="select"
                          size="sm"
                          :modelValue="h.default"
                          :options="hiddenSelectOptions(h)"
                          @update:modelValue="
                            (v) => ((h.default = v), markDirty())
                          "
                        />
                        <FormControl
                          v-else
                          type="text"
                          size="sm"
                          :modelValue="h.default"
                          :placeholder="__('Default value')"
                          @update:modelValue="
                            (v) => ((h.default = v), markDirty())
                          "
                        />
                      </div>
                    </div>
                  </div>
                  <ErrorMessage
                    v-if="hiddenMissingDefault"
                    class="mt-2"
                    :message="
                      __(
                        'Set a default value for each field to publish this form.',
                      )
                    "
                  />
                </div>
              </div>
            </div>

            <!-- SETTINGS TAB -->
            <div v-else-if="tab.name === 'settings'" class="flex flex-col pt-5">
              <!-- form details -->
              <div>
                <div class="flex flex-col gap-1">
                  <span class="text-lg-semibold text-ink-gray-8">{{
                    __('Form details')
                  }}</span>
                  <span class="text-p-sm text-ink-gray-6">{{
                    __('Basic settings for this form.')
                  }}</span>
                </div>
                <div class="mt-3.5 flex flex-col gap-4">
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <div class="mb-1.5 text-sm text-ink-gray-5">
                        {{ __('Route') }}
                      </div>
                      <div
                        class="flex h-7 cursor-text items-center rounded border border-transparent bg-surface-gray-2 px-2.5 text-base transition-colors hover:bg-surface-gray-3 focus-within:border-outline-gray-4 focus-within:bg-surface-base focus-within:shadow-sm"
                        @click="focusRouteEnd"
                      >
                        <span class="shrink-0 text-ink-gray-4">/crm-form/</span>
                        <input
                          v-model="form.route"
                          class="min-w-0 flex-1 border-0 bg-transparent p-0 text-base text-ink-gray-8 placeholder:text-ink-gray-4 focus:outline-none focus:ring-0"
                          @input="(routeEdited = true), markDirty()"
                        />
                      </div>
                    </div>
                    <FormControl
                      v-model="doctypeModel"
                      type="select"
                      :label="__('Maps to')"
                      :options="targetOptions"
                    />
                    <FormControl
                      v-model="form.submit_button_label"
                      type="text"
                      :label="__('Submit button label')"
                      @input="markDirty"
                    />
                  </div>
                  <FormControl
                    v-model="form.success_message"
                    type="textarea"
                    :label="__('Success message')"
                    :rows="2"
                    :placeholder="__('Shown after a successful submission')"
                    @input="markDirty"
                  />
                  <div>
                    <FormControl
                      v-model="form.redirect_url"
                      type="text"
                      :label="__('Redirect URL')"
                      :placeholder="__('https://example.com/thank-you')"
                      @input="markDirty"
                    />
                    <p class="mt-1.5 text-p-sm text-ink-gray-5">
                      {{
                        __(
                          'Send visitors here after they submit. Leave blank to show the success message.',
                        )
                      }}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <!-- SHARE TAB -->
            <div v-else class="flex flex-col pt-5">
              <Alert
                v-if="!form.published"
                class="mb-5"
                theme="yellow"
                variant="subtle"
                :dismissible="false"
                :title="
                  __(
                    'This form isn’t published yet — hit Publish to make the link and embeds live.',
                  )
                "
              />

              <!-- link -->
              <div>
                <div class="flex flex-col gap-1">
                  <span class="text-lg-semibold text-ink-gray-8">{{
                    __('Link')
                  }}</span>
                  <span class="text-p-sm text-ink-gray-6">{{
                    __('Send people straight to the hosted form.')
                  }}</span>
                </div>
                <div class="mt-3.5 flex items-center gap-2">
                  <TextInput
                    class="flex-1"
                    size="sm"
                    readonly
                    :modelValue="publicUrl"
                  >
                    <template #suffix>
                      <button
                        class="flex text-ink-gray-5 transition-colors hover:text-ink-gray-8"
                        :title="__('Copy link')"
                        @click="copyToClipboard(publicUrl)"
                      >
                        <LucideCopy class="h-4 w-4" />
                      </button>
                    </template>
                  </TextInput>
                  <a :href="publicUrl" target="_blank">
                    <Button :label="__('Open')">
                      <template #prefix
                        ><LucideExternalLink class="h-4 w-4"
                      /></template>
                    </Button>
                  </a>
                </div>
              </div>

              <hr class="my-8 border-outline-gray-2" />

              <!-- embed -->
              <div>
                <div class="flex flex-col gap-1">
                  <span class="text-lg-semibold text-ink-gray-8">{{
                    __('Embed')
                  }}</span>
                  <span class="text-p-sm text-ink-gray-6">{{
                    __('Drop the form into your own website.')
                  }}</span>
                </div>

                <div class="mt-3.5 flex flex-col gap-5">
                  <!-- inline embed (no iframe) -->
                  <div>
                    <div class="mb-1 text-base text-ink-gray-5">
                      {{ __('Inline embed') }}
                    </div>
                    <p class="mb-2 text-p-sm text-ink-gray-5">
                      {{
                        __(
                          'Renders the form right inside your page — no frame, inherits your site’s width and fonts.',
                        )
                      }}
                    </p>
                    <div class="relative">
                      <textarea
                        readonly
                        rows="3"
                        class="w-full resize-none rounded-md border border-outline-gray-2 bg-surface-gray-1 py-2 pl-3 pr-10 font-mono text-xs text-ink-gray-7 focus:border-outline-gray-4 focus:shadow-sm focus:outline-none focus:ring-0 focus-visible:outline-none"
                        :value="jsSnippet"
                      />
                      <button
                        class="absolute right-2 top-2 flex text-ink-gray-5 transition-colors hover:text-ink-gray-8"
                        :title="__('Copy')"
                        @click="copyToClipboard(jsSnippet)"
                      >
                        <LucideCopy class="h-4 w-4" />
                      </button>
                    </div>
                  </div>

                  <!-- iframe (isolated) -->
                  <div>
                    <div class="mb-1 text-base text-ink-gray-5">
                      {{ __('iframe') }}
                    </div>
                    <p class="mb-2 text-p-sm text-ink-gray-5">
                      {{
                        __(
                          'Sandboxed in a frame — simplest, but a fixed height and its own styling.',
                        )
                      }}
                    </p>
                    <div class="relative">
                      <textarea
                        readonly
                        rows="3"
                        class="w-full resize-none rounded-md border border-outline-gray-2 bg-surface-gray-1 py-2 pl-3 pr-10 font-mono text-xs text-ink-gray-7 focus:border-outline-gray-4 focus:shadow-sm focus:outline-none focus:ring-0 focus-visible:outline-none"
                        :value="iframeSnippet"
                      />
                      <button
                        class="absolute right-2 top-2 flex text-ink-gray-5 transition-colors hover:text-ink-gray-8"
                        :title="__('Copy')"
                        @click="copyToClipboard(iframeSnippet)"
                      >
                        <LucideCopy class="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <hr class="my-8 border-outline-gray-2" />

              <!-- allowed domains -->
              <div>
                <div class="flex flex-col gap-1">
                  <span class="text-lg-semibold text-ink-gray-8">{{
                    __('Allowed domains')
                  }}</span>
                  <span class="text-p-sm text-ink-gray-6">
                    {{
                      __(
                        'Sites where this form may be embedded, one per line. Browsers block the iframe on any site not listed here.',
                      )
                    }}
                  </span>
                </div>
                <textarea
                  v-model="form.allowed_embedding_domains"
                  rows="3"
                  spellcheck="false"
                  placeholder="https://www.example.com"
                  class="mt-3.5 w-full resize-none rounded-md border border-outline-gray-2 px-3 py-2 font-mono text-xs text-ink-gray-8 focus:border-outline-gray-4 focus:shadow-sm focus:outline-none focus:ring-0 focus-visible:outline-none"
                  @input="markDirty"
                />
                <p
                  v-if="!embeddingDomains.length"
                  class="mt-1.5 text-xs text-ink-amber-6"
                >
                  {{
                    __(
                      'No domains added — the embed will only work on this site until you add one.',
                    )
                  }}
                </p>
              </div>
            </div>
          </template>
        </Tabs>
      </div>

      <!-- PREVIEW MODE -->
      <div v-else class="mx-auto max-w-2xl pt-6">
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
          <div
            v-if="previewSubmitted"
            class="flex flex-col items-center gap-3 py-10 text-center"
          >
            <div
              class="flex h-12 w-12 items-center justify-center rounded-full bg-surface-green-2 text-ink-green-3"
            >
              <LucideCheck class="h-6 w-6" />
            </div>
            <div class="text-lg font-semibold text-ink-gray-9">
              {{ form.success_message || __('Thank you!') }}
            </div>
            <Button :label="__('Preview again')" @click="resetPreview" />
          </div>

          <template v-else>
            <div class="text-lg font-semibold text-ink-gray-9">
              {{ form.title || __('Form title') }}
            </div>
            <div v-if="form.description" class="mt-1 text-sm text-ink-gray-6">
              {{ form.description }}
            </div>
            <div class="mt-5 flex flex-col gap-5">
              <div v-for="(section, si) in layout" :key="si">
                <div
                  v-if="section.label"
                  class="mb-3 text-sm font-semibold text-ink-gray-8"
                >
                  {{ section.label }}
                </div>
                <div
                  class="grid gap-x-5"
                  :style="{
                    gridTemplateColumns: `repeat(${section.columns.length}, minmax(0,1fr))`,
                  }"
                >
                  <div
                    v-for="(col, ci) in section.columns"
                    :key="ci"
                    class="flex flex-col gap-4"
                  >
                    <div v-for="f in col" :key="f.fieldname">
                      <div
                        v-if="f.fieldtype !== 'Check'"
                        class="mb-1.5 text-sm text-ink-gray-5"
                      >
                        {{ f.label
                        }}<span v-if="f.reqd" class="text-ink-red-5">*</span>
                      </div>
                      <FormControl
                        v-if="TEXTAREA_TYPES.includes(f.fieldtype)"
                        v-model="previewModel[f.fieldname]"
                        type="textarea"
                        :placeholder="f.placeholder"
                      />
                      <FormControl
                        v-else-if="f.fieldtype === 'Select'"
                        v-model="previewModel[f.fieldname]"
                        type="select"
                        :options="selectOptions(f)"
                        :placeholder="f.placeholder || __('Select an option')"
                      />
                      <div
                        v-else-if="f.fieldtype === 'Check'"
                        class="flex items-center gap-2"
                      >
                        <FormControl
                          v-model="previewModel[f.fieldname]"
                          type="checkbox"
                        />
                        <span class="text-sm text-ink-gray-5"
                          >{{ f.label
                          }}<span v-if="f.reqd" class="text-ink-red-5"
                            >*</span
                          ></span
                        >
                      </div>
                      <FormControl
                        v-else
                        v-model="previewModel[f.fieldname]"
                        :type="inputType(f)"
                        :placeholder="f.placeholder"
                      />
                      <div
                        v-if="f.field_description"
                        class="mt-1 text-sm text-ink-gray-4"
                      >
                        {{ f.field_description }}
                      </div>
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
  </div>
</template>

<script setup>
import {
  Alert,
  Button,
  Tabs,
  TextInput,
  FormControl,
  Dropdown,
  ErrorMessage,
  call,
  toast,
  createResource,
} from 'frappe-ui'
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
import FieldCard from '@/components/Settings/Forms/FieldCard.vue'
import { fieldTypeIcon } from '@/components/Settings/Forms/fieldTypeIcon'
import DragVerticalIcon from '@/components/Icons/DragVerticalIcon.vue'
import LucideCopy from '~icons/lucide/copy'
import Draggable from 'vuedraggable'
import LucideShare2 from '~icons/lucide/share-2'
import LucideEye from '~icons/lucide/eye'
import LucideEyeOff from '~icons/lucide/eye-off'
import LucidePencil from '~icons/lucide/pencil'
import LucideExternalLink from '~icons/lucide/external-link'
import LucideCheck from '~icons/lucide/check'
import LucideLayoutList from '~icons/lucide/layout-list'
import LucideSettings from '~icons/lucide/settings'
import { globalStore } from '@/stores/global'
import { copyToClipboard } from '@/utils'
import { ref, reactive, computed, nextTick } from 'vue'

const { $dialog } = globalStore()

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
const publishing = ref(false)
const dirty = ref(false)
const mode = ref('edit') // edit | preview
const tabIndex = ref(0)
const tabs = [
  { name: 'editor', label: __('Editor'), icon: LucideLayoutList },
  { name: 'settings', label: __('Settings'), icon: LucideSettings },
  { name: 'share', label: __('Share'), icon: LucideShare2 },
]
const expanded = ref(null) // fieldname of the expanded field editor
const descInput = ref(null)
// while a draft still has an auto-generated route, keep it in sync with the
// title; once the user edits the route (or the form is published) we stop
const routeEdited = ref(false)

function slugify(v) {
  return (v || '')
    .toString()
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

function onTitleInput() {
  if (!routeEdited.value && !form.published) form.route = slugify(form.title)
  markDirty()
}

// clicking the /crm-form/ prefix or the box padding focuses the slug input with
// the caret at the end (not the start)
function focusRouteEnd(e) {
  if (e.target.tagName === 'INPUT') return
  const input = e.currentTarget.querySelector('input')
  if (!input) return
  input.focus()
  input.setSelectionRange(input.value.length, input.value.length)
}

// keep the description textarea sized to its content
function autoGrow(el) {
  if (!el) return
  el.style.height = 'auto'
  el.style.height = el.scrollHeight + 'px'
}
const dragging = ref(false)

// Editing model: form.fields (flat) is the source of truth, derived into a
// draggable list of sections, each holding columns of field items. Every
// section (including the first) is a real Section Break, so they all behave
// identically. After any drag / structural change we re-flatten to form.fields.
const sections = ref([])

// doctype-mandatory fields removed from the visible form. Each carries a default
// value that's applied on submission so the record can still be created.
const hiddenFields = ref([])

// fieldnames the target doctype marks mandatory (from the field catalog). These
// stay required in the form and, when removed, drop into hiddenFields.
const mandatorySet = computed(
  () =>
    new Set(
      (availableFields.data || [])
        .filter((f) => f.reqd)
        .map((f) => f.fieldname),
    ),
)
function isMandatory(fieldname) {
  return mandatorySet.value.has(fieldname)
}
function catalogDefault(fieldname) {
  const c = (availableFields.data || []).find((f) => f.fieldname === fieldname)
  return c?.default || ''
}
// true while any hidden required field is missing its default (blocks publish)
const hiddenMissingDefault = computed(() =>
  hiddenFields.value.some((h) => !String(h.default || '').trim()),
)
function hiddenIsSelect(h) {
  return h.fieldtype === 'Select' || h.fieldtype === 'Link'
}
function hiddenSelectOptions(h) {
  let opts = []
  if (h.fieldtype === 'Select') {
    opts = (h.options || '').split('\n').filter(Boolean)
  } else if (h.fieldtype === 'Link') {
    opts = linkOptions[h.options] || []
  }
  opts = opts.slice()
  if (h.default && !opts.includes(h.default)) opts.unshift(h.default)
  return opts.map((o) => ({ label: o, value: o }))
}

// cache of Link option lists (e.g. CRM Lead Status names) for hidden Link fields
const linkOptions = reactive({})
async function ensureLinkOptions(doctype) {
  if (!doctype || linkOptions[doctype]) return
  linkOptions[doctype] = []
  try {
    const rows = await call('frappe.client.get_list', {
      doctype,
      fields: ['name'],
      limit_page_length: 0,
      order_by: 'name asc',
    })
    linkOptions[doctype] = (rows || []).map((r) => r.name)
  } catch {
    linkOptions[doctype] = []
  }
}

function newColumn(colField = null) {
  return { colField, items: [] }
}

function newSection(secField = null) {
  return {
    secField: secField || makeMarker('Section Break'),
    columns: [newColumn()],
    editingLabel: false,
  }
}

function rebuildModel() {
  const secs = []
  let cur = null
  const ensureSection = () => {
    // fields before the first explicit Section Break get a synthesized one so
    // the first section is a normal, draggable section like the rest
    if (!cur) {
      cur = newSection()
      secs.push(cur)
    }
    return cur
  }
  for (const f of form.fields || []) {
    if (f.fieldtype === 'Section Break') {
      cur = newSection(f)
      secs.push(cur)
    } else if (f.fieldtype === 'Column Break') {
      ensureSection().columns.push(newColumn(f))
    } else {
      const sec = ensureSection()
      sec.columns[sec.columns.length - 1].items.push(f)
    }
  }
  if (!secs.length) secs.push(newSection()) // empty form → one empty section
  sections.value = secs
}

// emit a container's columns, normalising column-break markers to position
function emitColumns(out, cols) {
  cols.forEach((col, i) => {
    if (i === 0) {
      col.colField = null
    } else if (!col.colField) {
      col.colField = makeMarker('Column Break')
    }
    if (col.colField) out.push(col.colField)
    for (const f of col.items) out.push(f)
  })
}

function flattenModel() {
  const out = []
  for (const sec of sections.value) {
    out.push(sec.secField)
    emitColumns(out, sec.columns)
  }
  return out
}

function syncFromModel() {
  form.fields = flattenModel()
  markDirty()
}

function onSortEnd() {
  dragging.value = false
  syncFromModel()
}

// vuedraggable item-keys
const sectionKey = (sec) => sec.secField?.fieldname || 'sec'
const columnKey = (col) => col.colField?.fieldname || 'col0'
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
  redirect_url: '',
  allowed_embedding_domains: '',
  published: 0,
  fields: [],
})

const publicUrl = computed(
  () => `${window.location.origin}/crm-form/${form.route}`,
)
const embeddingDomains = computed(() =>
  (form.allowed_embedding_domains || '').split(/\s+/).filter(Boolean),
)

const iframeSnippet = computed(
  () =>
    `<iframe src="${publicUrl.value}" width="100%" height="640" style="border:0" title="${form.title || 'Web form'}"></iframe>`,
)
const jsSnippet = computed(() => {
  const origin = window.location.origin
  return (
    `<div data-crm-form="${form.route || 'form'}"></div>\n` +
    `<script src="${origin}/assets/crm/js/crm_form_embed.js" async></` +
    `script>`
  )
})

// auto-save: every edit funnels through markDirty(), which (re)arms a debounced
// save ~1s after the last change
let autosaveTimer = null
function scheduleAutosave() {
  if (autosaveTimer) clearTimeout(autosaveTimer)
  autosaveTimer = setTimeout(() => {
    autosaveTimer = null
    if (dirty.value && !saving.value && !publishing.value)
      save({ silent: true })
  }, 1000)
}
function markDirty() {
  dirty.value = true
  scheduleAutosave()
}
function toggle(f) {
  expanded.value = expanded.value === f.fieldname ? null : f.fieldname
}
// focusing a field's label selects it (reveals inline editor) without toggling off
function open(f) {
  expanded.value = f.fieldname
}

// field counts shown in section headers
function sectionFieldCount(sec) {
  return sec.columns.reduce((n, c) => n + c.items.length, 0)
}

// add a field into a specific column, then re-flatten to form.fields
function addFieldToColumn(col, option) {
  const af = option?.af || option
  if (!af?.fieldname) return
  // re-adding a field that was moved to hidden brings it back onto the form
  hiddenFields.value = hiddenFields.value.filter(
    (h) => h.fieldname !== af.fieldname,
  )
  col.items.push({
    fieldname: af.fieldname,
    label: af.label,
    fieldtype: af.fieldtype,
    options: af.options,
    reqd: !!af.reqd,
    placeholder: '',
    field_description: '',
  })
  syncFromModel()
}

function addColumn(cols) {
  if (cols.length >= MAX_COLUMNS) {
    toast.info(__('A section can have up to {0} columns', [MAX_COLUMNS]))
    return
  }
  cols.push(newColumn())
  syncFromModel()
}

function removeLastColumn(cols) {
  if (cols.length <= 1) return
  const last = cols[cols.length - 1]
  const prev = cols[cols.length - 2]
  if (last.items.length) prev.items.push(...last.items) // keep the fields
  cols.pop()
  syncFromModel()
}

// ⋯ menu: column ops shared by the root section and every section
function columnOps(cols) {
  return [
    {
      label: __('Add Column'),
      icon: 'columns',
      onClick: () => addColumn(cols),
      condition: () => cols.length < MAX_COLUMNS,
    },
    {
      label: __('Remove Last Column'),
      icon: 'trash-2',
      onClick: () => removeLastColumn(cols),
      condition: () => cols.length > 1,
    },
  ]
}

// ⋯ menu for a section: rename / remove + column ops
function sectionMenu(sec) {
  return [
    {
      group: __('Section'),
      items: [
        {
          label: __('Rename'),
          icon: 'edit',
          onClick: () => (sec.editingLabel = true),
        },
        {
          label: __('Remove Section'),
          icon: 'trash-2',
          onClick: () => removeBreak(sec.secField),
        },
      ],
    },
    { group: __('Column'), items: columnOps(sec.columns) },
  ]
}
function optionList(f) {
  return (f.options || '').split('\n').filter(Boolean)
}
function selectOptions(f) {
  const opts = optionList(f).map((o) => ({ label: o, value: o }))
  return [{ label: __('Select an option'), value: '' }, ...opts]
}
const TEXTAREA_TYPES = [
  'Small Text',
  'Text',
  'Long Text',
  'Text Editor',
  'HTML Editor',
  'Markdown Editor',
]
function inputType(f) {
  if (f.options === 'Email') return 'email'
  if (['Int', 'Float', 'Currency', 'Percent'].includes(f.fieldtype))
    return 'number'
  if (f.fieldtype === 'Date') return 'date'
  if (f.fieldtype === 'Datetime') return 'datetime-local'
  if (f.fieldtype === 'Time') return 'time'
  if (f.fieldtype === 'Color') return 'color'
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
function makeMarker(fieldtype) {
  return {
    fieldname: uid(fieldtype),
    label: '',
    fieldtype,
    options: '',
    reqd: false,
    placeholder: '',
    field_description: '',
  }
}
// a section can hold this many columns before it gets too cramped to build/fill
const MAX_COLUMNS = 4

// columns in the last section (where a new Column Break would land)
const lastSectionColumns = computed(() => {
  const secs = sections.value
  return secs.length ? secs[secs.length - 1].columns.length : 1
})
const columnBreakDisabled = computed(
  () => lastSectionColumns.value >= MAX_COLUMNS,
)

function addBreak(fieldtype) {
  if (fieldtype === 'Column Break' && columnBreakDisabled.value) {
    toast.info(__('A section can have up to {0} columns', [MAX_COLUMNS]))
    return
  }
  // append at the end: a Section Break starts a new section, a Column Break
  // adds a new column to the last section
  form.fields.push({
    fieldname: uid(fieldtype),
    label: '',
    fieldtype,
    options: '',
    reqd: false,
    placeholder: '',
    field_description: '',
  })
  rebuildModel()
  markDirty()
}

// load
createResource({
  url: 'crm.api.form.get_form_config',
  params: { name: props.name },
  auto: true,
  onSuccess: (doc) => {
    form.title = doc.title || ''
    form.route = doc.route || ''
    form.document_type = doc.document_type || 'CRM Lead'
    form.description = doc.description || ''
    form.submit_button_label = doc.submit_button_label || 'Submit'
    form.success_message = doc.success_message || ''
    form.redirect_url = doc.redirect_url || ''
    form.allowed_embedding_domains = doc.allowed_embedding_domains || ''
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
    hiddenFields.value = (doc.hidden_fields || []).map((h) => ({
      fieldname: h.fieldname,
      label: h.label,
      fieldtype: h.fieldtype,
      options: h.options || '',
      default: h.default ?? '',
    }))
    hiddenFields.value.forEach((h) => {
      if (h.fieldtype === 'Link') ensureLinkOptions(h.options)
    })
    rebuildModel()
    // only keep auto-syncing the route if it's still an untouched default
    routeEdited.value = !/^untitled-form(-\d+)?$/.test(form.route)
    loaded.value = true
    availableFields.reload()
    nextTick(() => autoGrow(descInput.value))
  },
})

const availableFields = createResource({
  url: 'crm.api.form.get_form_fields',
  makeParams: () => ({ document_type: form.document_type }),
})

// unused (not-yet-added) target fields, as Autocomplete options
const availableFieldOptions = computed(() => {
  // hidden fields intentionally stay in the picker so they can be re-added to
  // the form (which also removes them from the hidden section)
  const used = new Set(form.fields.map((f) => f.fieldname))
  return (availableFields.data || [])
    .filter((f) => !used.has(f.fieldname))
    .map((af) => ({ label: af.label, value: af.fieldname, af }))
})

// apply an edit emitted by a FieldCard to the parent-owned field object
function updateField(f, patch) {
  Object.assign(f, patch)
  markDirty()
}

function removeField(f) {
  form.fields = form.fields.filter((x) => x !== f)
  if (expanded.value === f.fieldname) expanded.value = null
  // a mandatory field isn't deleted — it moves to the hidden section so its
  // value can still be supplied (via a default) on submission
  if (
    isMandatory(f.fieldname) &&
    !BREAK_TYPES.includes(f.fieldtype) &&
    !hiddenFields.value.some((h) => h.fieldname === f.fieldname)
  ) {
    hiddenFields.value.push({
      fieldname: f.fieldname,
      label: f.label,
      fieldtype: f.fieldtype,
      options: f.options || '',
      default: catalogDefault(f.fieldname),
    })
    toast.info(
      __('{0} moved to hidden required fields — set a default value', [
        f.label || f.fieldname,
      ]),
    )
  }
  rebuildModel()
  markDirty()
}
function removeBreak(marker) {
  // dropping a break marker merges its content back into the previous
  // section/column (rebuildGroups normalises the structure)
  form.fields = form.fields.filter((x) => x !== marker)
  rebuildModel()
  markDirty()
}

// select is bound to this so we can intercept the change and confirm before
// dropping incompatible fields; cancelling leaves form.document_type untouched
// so the dropdown snaps back to the current value
const doctypeModel = computed({
  get: () => form.document_type,
  set: (v) => requestDoctypeChange(v),
})

async function requestDoctypeChange(newDt) {
  if (!newDt || newDt === form.document_type) return
  const fields = await call('crm.api.form.get_form_fields', {
    document_type: newDt,
  })
  const valid = new Set((fields || []).map((f) => f.fieldname))
  const wouldDrop = form.fields.filter(
    (f) => !BREAK_TYPES.includes(f.fieldtype) && !valid.has(f.fieldname),
  ).length

  if (!wouldDrop) {
    commitDoctype(newDt, valid)
    return
  }
  $dialog({
    title: __('Change form type?'),
    message: __(
      "Switching to {0} will remove {1} field(s) that don't exist on {0}. This can't be undone.",
      [docLabel(newDt), wouldDrop],
    ),
    variant: 'danger',
    actions: [
      {
        label: __('Change & remove fields'),
        variant: 'solid',
        theme: 'red',
        onClick: (close) => {
          commitDoctype(newDt, valid)
          close()
        },
      },
    ],
  })
}

async function commitDoctype(newDt, valid) {
  form.document_type = newDt
  expanded.value = null
  await availableFields.reload()
  const before = form.fields.length
  form.fields = form.fields.filter(
    (f) => BREAK_TYPES.includes(f.fieldtype) || valid.has(f.fieldname),
  )
  const dropped = before - form.fields.length
  // reconcile the fields we kept against the new doctype's real definitions:
  // pick up its options and enforce its mandatory flags
  const catalog = new Map(
    (availableFields.data || []).map((f) => [f.fieldname, f]),
  )
  form.fields.forEach((f) => {
    const c = catalog.get(f.fieldname)
    if (!c) return
    f.options = c.options
    if (c.reqd) f.reqd = true
  })
  // rebuild hidden fields for the new doctype: its system-hidden fields (Status,
  // with the right options + default), plus any hidden fillable-mandatory field
  // that's still mandatory here (keeping the author's default)
  const newHidden = await call('crm.api.form.get_hidden_seed', {
    document_type: newDt,
  })
  const stillMandatory = hiddenFields.value.filter(
    (h) => catalog.has(h.fieldname) && mandatorySet.value.has(h.fieldname),
  )
  hiddenFields.value = [
    ...(newHidden || []).map((h) => ({
      fieldname: h.fieldname,
      label: h.label,
      fieldtype: h.fieldtype,
      options: h.options || '',
      default: h.default ?? '',
    })),
    ...stillMandatory,
  ]
  hiddenFields.value.forEach((h) => {
    if (h.fieldtype === 'Link') ensureLinkOptions(h.options)
  })
  rebuildModel()
  markDirty()
  if (dropped) {
    toast.info(
      __('{0} field(s) removed — not available on {1}', [
        dropped,
        docLabel(newDt),
      ]),
    )
  }
}

async function save({ silent = false } = {}) {
  // drafts auto-save freely; only a published form requires every hidden field
  // to carry a default (an empty one would break record creation)
  if (form.published) {
    const missing = hiddenFields.value.filter(
      (h) => !String(h.default || '').trim(),
    )
    if (missing.length) {
      if (!silent)
        toast.error(
          __('Set a default value for hidden required field(s): {0}', [
            missing.map((h) => h.label || h.fieldname).join(', '),
          ]),
        )
      return false
    }
  }
  if (saving.value) return false
  saving.value = true
  // normalise from the model so every section break (incl. the first) persists
  form.fields = flattenModel()
  try {
    const doc = await call('crm.api.form.save_form', {
      name: form.name,
      form: {
        title: form.title,
        route: form.route,
        document_type: form.document_type,
        description: form.description,
        submit_button_label: form.submit_button_label,
        success_message: form.success_message,
        redirect_url: form.redirect_url,
        allowed_embedding_domains: form.allowed_embedding_domains,
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
        hidden_fields: hiddenFields.value.map((h) => ({
          fieldname: h.fieldname,
          label: h.label,
          fieldtype: h.fieldtype,
          options: h.options,
          default: h.default,
        })),
      },
    })
    form.route = doc.route
    ;(doc.fields || []).forEach((df, i) => {
      if (form.fields[i]) form.fields[i].name = df.name
    })
    dirty.value = false
    emit('saved')
    return true
  } catch (e) {
    if (!silent)
      toast.error(e?.messages?.[0] || e?.message || __('Could not save'))
    return false
  } finally {
    saving.value = false
  }
}

// header Publish/Unpublish action: flush any pending autosave, flip the flag,
// and persist immediately (reverting if the save is rejected, e.g. missing default)
async function togglePublish() {
  if (autosaveTimer) {
    clearTimeout(autosaveTimer)
    autosaveTimer = null
  }
  const prev = form.published
  form.published = prev ? 0 : 1
  publishing.value = true
  const ok = await save()
  publishing.value = false
  if (!ok) {
    form.published = prev
    return
  }
  toast.success(form.published ? __('Form published') : __('Form unpublished'))
}
</script>

<style>
/* Hide Sortable's floating drag clone so reordering stays contained to the
   fields list — only the in-list placeholder moves, never a copy that can
   drift outside the section/modal. */
.wf-drag-fallback {
  opacity: 0 !important;
}

/* The frappe-ui Tabs root is overflow-hidden, which would trap a sticky child;
   relax it so the tab list can stick to the outer scroll container. */
.wf-tabs > div {
  overflow: visible;
}

/* Keep just the tab bar (Editor / Settings / Share) pinned to the top while the
   panel scrolls. px-0 aligns the labels + underline with the content below
   (frappe-ui bakes px-5 into the list). */
.wf-tabs [role='tablist'] {
  position: sticky;
  top: 0;
  z-index: 10;
  padding-left: 0;
  padding-right: 0;
  background-color: var(--surface-elevation-2);
}
</style>
