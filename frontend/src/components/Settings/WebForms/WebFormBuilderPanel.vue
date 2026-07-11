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
        <Badge
          v-if="dirty"
          :label="__('Not Saved')"
          variant="subtle"
          theme="orange"
        />
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
          :label="__('Update')"
          :loading="saving"
          :disabled="!dirty"
          @click="save"
        />
      </div>
    </div>

    <div v-if="loaded" class="flex-1 overflow-y-auto p-6">
      <!-- EDIT MODE -->
      <div v-if="mode === 'edit'" class="mx-auto flex max-w-2xl flex-col">
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
              <FormControl
                v-model="form.title"
                type="text"
                :label="__('Title')"
                @input="markDirty"
              />
              <div>
                <div class="mb-1.5 text-sm text-ink-gray-5">
                  {{ __('Route') }}
                </div>
                <div class="flex items-center gap-1.5">
                  <span class="whitespace-nowrap text-sm text-ink-gray-4"
                    >/crm-form/</span
                  >
                  <TextInput
                    v-model="form.route"
                    class="flex-1"
                    @input="markDirty"
                  />
                </div>
              </div>
              <FormControl
                v-model="form.document_type"
                type="select"
                :label="__('Maps to')"
                :options="targetOptions"
                @update:modelValue="onDoctypeChange"
              />
              <FormControl
                v-model="form.submit_button_label"
                type="text"
                :label="__('Submit button label')"
                @input="markDirty"
              />
            </div>
            <FormControl
              v-model="form.description"
              type="textarea"
              :label="__('Description')"
              :rows="2"
              @input="markDirty"
            />
            <FormControl
              v-model="form.success_message"
              type="textarea"
              :label="__('Success message')"
              :rows="2"
              :placeholder="__('Shown after a successful submission')"
              @input="markDirty"
            />
          </div>
        </div>

        <hr class="my-8 border-outline-gray-2" />

        <!-- fields -->
        <div>
          <div class="flex flex-col gap-1">
            <span class="text-lg-semibold text-ink-gray-8">{{
              __('Fields')
            }}</span>
            <span class="text-p-sm text-ink-gray-6">
              {{
                inputFieldCount
                  ? __('{0} fields · drag to reorder.', [inputFieldCount])
                  : __('Add the fields people fill in.')
              }}
            </span>
          </div>

          <div
            v-if="!form.fields.length"
            class="mt-4 rounded-lg border border-dashed py-8 text-center text-sm text-ink-gray-4"
          >
            {{ __('No fields yet — add one below.') }}
          </div>

          <!-- grouped, side-by-side layout (sections -> columns), draggable at every level -->
          <div
            v-else
            class="mt-4 flex flex-col gap-3"
            :class="{ 'select-none': dragging }"
          >
            <!-- root section (fields before any section break; pinned first) -->
            <div class="rounded-lg border border-dashed p-2">
              <Draggable
                :list="rootColumns"
                :item-key="columnKey"
                handle=".column-handle"
                group="wf-cols-root"
                class="flex items-stretch gap-2"
                ghost-class="opacity-40"
                :force-fallback="true"
                :fallback-on-body="false"
                fallback-class="wf-drag-fallback"
                :animation="120"
                @start="dragging = true"
                @end="onSortEnd"
              >
                <template #item="{ element: col, index: ci }">
                  <div class="flex min-w-0 flex-1 items-stretch">
                    <div
                      v-if="ci > 0"
                      class="mr-2 flex w-7 shrink-0 flex-col items-center gap-1 self-stretch pt-1"
                    >
                      <LucideGripVertical
                        class="column-handle h-4 w-4 shrink-0 cursor-grab text-ink-gray-4"
                        :title="__('Move column')"
                      />
                      <Button
                        variant="ghost"
                        size="sm"
                        :tooltip="__('Remove column break')"
                        @click="removeBreak(col.colField)"
                      >
                        <template #icon
                          ><LucideX class="h-3.5 w-3.5 text-ink-gray-5"
                        /></template>
                      </Button>
                      <div class="w-px flex-1 bg-outline-gray-3"></div>
                    </div>
                    <div class="min-w-[150px] flex-1">
                      <Draggable
                        :list="col.items"
                        group="wf-fields"
                        item-key="fieldname"
                        class="flex min-h-[48px] flex-col gap-2 rounded-md"
                        :class="[
                          col.items.length ? '' : 'border border-dashed',
                        ]"
                        ghost-class="opacity-40"
                        :force-fallback="true"
                        :fallback-on-body="false"
                        fallback-class="wf-drag-fallback"
                        :animation="120"
                        @start="dragging = true"
                        @end="onSortEnd"
                      >
                        <template #item="{ element: f }">
                          <div
                            class="flex items-center gap-2 rounded-lg border bg-surface-white px-3 py-2.5"
                            :class="
                              expanded === f.fieldname
                                ? 'ring-1 ring-ink-gray-4'
                                : ''
                            "
                          >
                            <LucideGripVertical
                              class="drag-handle h-4 w-4 shrink-0 cursor-grab text-ink-gray-4"
                            />
                            <div
                              class="min-w-0 flex-1 cursor-pointer"
                              @click="toggle(f)"
                            >
                              <div class="truncate text-base text-ink-gray-8">
                                {{ f.label
                                }}<span v-if="f.reqd" class="text-ink-red-5"
                                  >*</span
                                >
                              </div>
                              <div
                                class="mt-1 truncate text-xs text-ink-gray-4"
                              >
                                {{ f.fieldname }} · {{ f.fieldtype }}
                              </div>
                            </div>
                            <Button variant="ghost" @click="removeField(f)">
                              <template #icon
                                ><LucideX class="h-4 w-4 text-ink-gray-5"
                              /></template>
                            </Button>
                          </div>
                        </template>
                      </Draggable>
                    </div>
                  </div>
                </template>
              </Draggable>
            </div>

            <!-- sections (draggable) -->
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
                <div class="rounded-lg border border-dashed p-2">
                  <div class="mb-2 flex items-center gap-2 px-1">
                    <LucideGripVertical
                      class="section-handle h-4 w-4 shrink-0 cursor-grab text-ink-gray-4"
                      :title="__('Move section')"
                    />
                    <TextInput
                      v-model="sec.secField.label"
                      class="flex-1"
                      size="sm"
                      :placeholder="__('Section title (optional)')"
                      @input="markDirty"
                    />
                    <Button variant="ghost" @click="removeBreak(sec.secField)">
                      <template #icon
                        ><LucideX class="h-4 w-4 text-ink-gray-5"
                      /></template>
                    </Button>
                  </div>

                  <Draggable
                    :list="sec.columns"
                    :item-key="columnKey"
                    handle=".column-handle"
                    :group="'wf-cols-' + sec.secField.fieldname"
                    class="flex items-stretch gap-2"
                    ghost-class="opacity-40"
                    :force-fallback="true"
                    :fallback-on-body="false"
                    fallback-class="wf-drag-fallback"
                    :animation="120"
                    @start="dragging = true"
                    @end="onSortEnd"
                  >
                    <template #item="{ element: col, index: ci }">
                      <div class="flex min-w-0 flex-1 items-stretch">
                        <div
                          v-if="ci > 0"
                          class="mr-2 flex w-7 shrink-0 flex-col items-center gap-1 self-stretch pt-1"
                        >
                          <LucideGripVertical
                            class="column-handle h-4 w-4 shrink-0 cursor-grab text-ink-gray-4"
                            :title="__('Move column')"
                          />
                          <Button
                            variant="ghost"
                            size="sm"
                            :tooltip="__('Remove column break')"
                            @click="removeBreak(col.colField)"
                          >
                            <template #icon
                              ><LucideX class="h-3.5 w-3.5 text-ink-gray-5"
                            /></template>
                          </Button>
                          <div class="w-px flex-1 bg-outline-gray-3"></div>
                        </div>
                        <div class="min-w-[150px] flex-1">
                          <Draggable
                            :list="col.items"
                            group="wf-fields"
                            item-key="fieldname"
                            class="flex min-h-[48px] flex-col gap-2 rounded-md"
                            :class="[
                              col.items.length ? '' : 'border border-dashed',
                            ]"
                            ghost-class="opacity-40"
                            :force-fallback="true"
                            :fallback-on-body="false"
                            fallback-class="wf-drag-fallback"
                            :animation="120"
                            @start="dragging = true"
                            @end="onSortEnd"
                          >
                            <template #item="{ element: f }">
                              <div
                                class="flex items-center gap-2 rounded-lg border bg-surface-white px-3 py-2.5"
                                :class="
                                  expanded === f.fieldname
                                    ? 'ring-1 ring-ink-gray-4'
                                    : ''
                                "
                              >
                                <LucideGripVertical
                                  class="drag-handle h-4 w-4 shrink-0 cursor-grab text-ink-gray-4"
                                />
                                <div
                                  class="min-w-0 flex-1 cursor-pointer"
                                  @click="toggle(f)"
                                >
                                  <div
                                    class="truncate text-base text-ink-gray-8"
                                  >
                                    {{ f.label
                                    }}<span v-if="f.reqd" class="text-ink-red-5"
                                      >*</span
                                    >
                                  </div>
                                  <div
                                    class="mt-1 truncate text-xs text-ink-gray-4"
                                  >
                                    {{ f.fieldname }} · {{ f.fieldtype }}
                                  </div>
                                </div>
                                <Button variant="ghost" @click="removeField(f)">
                                  <template #icon
                                    ><LucideX class="h-4 w-4 text-ink-gray-5"
                                  /></template>
                                </Button>
                              </div>
                            </template>
                          </Draggable>
                        </div>
                      </div>
                    </template>
                  </Draggable>
                </div>
              </template>
            </Draggable>

            <!-- field editor (full width, for the selected field) -->
            <div
              v-if="editingField"
              class="rounded-lg border bg-surface-white px-3 py-3"
            >
              <div class="mb-2 flex items-center justify-between">
                <span class="text-sm-medium text-ink-gray-8"
                  >{{ editingField.label || editingField.fieldname }}
                  <span class="text-ink-gray-4"
                    >· {{ editingField.fieldtype }}</span
                  ></span
                >
                <Button variant="ghost" size="sm" @click="expanded = null">
                  <template #icon
                    ><LucideX class="h-4 w-4 text-ink-gray-5"
                  /></template>
                </Button>
              </div>
              <div class="flex items-center justify-between py-1">
                <span class="text-sm text-ink-gray-7">{{
                  __('Required')
                }}</span>
                <Switch
                  v-model="editingField.reqd"
                  @update:modelValue="markDirty"
                />
              </div>
              <div class="mt-2 grid grid-cols-2 gap-3">
                <FormControl
                  v-model="editingField.label"
                  type="text"
                  :label="__('Label')"
                  @input="markDirty"
                />
                <FormControl
                  v-model="editingField.placeholder"
                  type="text"
                  :label="__('Placeholder')"
                  @input="markDirty"
                />
              </div>
              <FormControl
                v-model="editingField.field_description"
                type="text"
                class="mt-3"
                :label="__('Description')"
                :placeholder="__('Helper text under the field')"
                @input="markDirty"
              />
              <div
                v-if="
                  editingField.fieldtype === 'Select' &&
                  optionList(editingField).length
                "
                class="mt-3"
              >
                <div class="mb-1.5 text-sm text-ink-gray-5">
                  {{ __('Options') }}
                </div>
                <div class="flex flex-wrap gap-1.5">
                  <span
                    v-for="o in optionList(editingField)"
                    :key="o"
                    class="rounded bg-surface-gray-2 px-2 py-1 text-xs text-ink-gray-7 ring-1 ring-outline-gray-2"
                  >
                    {{ o }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- inline add controls -->
          <div class="mt-3 flex items-center gap-2">
            <Autocomplete
              :options="availableFieldOptions"
              :value="''"
              :placeholder="__('Search fields…')"
              @change="onPickField"
            >
              <template #target="{ togglePopover }">
                <Button
                  :label="__('Add field')"
                  icon-left="plus"
                  @click="togglePopover"
                />
              </template>
            </Autocomplete>
            <Button
              variant="ghost"
              :label="__('Section break')"
              @click="addBreak('Section Break')"
            >
              <template #prefix><LucideRows3 class="h-4 w-4" /></template>
            </Button>
            <Button
              variant="ghost"
              :label="__('Column break')"
              :disabled="columnBreakDisabled"
              :tooltip="
                columnBreakDisabled
                  ? __('A section can have up to {0} columns', [MAX_COLUMNS])
                  : ''
              "
              @click="addBreak('Column Break')"
            >
              <template #prefix><LucideColumns3 class="h-4 w-4" /></template>
            </Button>
          </div>
        </div>

        <hr class="my-8 border-outline-gray-2" />

        <!-- publish -->
        <div>
          <div class="flex items-center justify-between">
            <div class="flex flex-col gap-1 pr-4">
              <span class="text-lg-semibold text-ink-gray-8">{{
                __('Publish')
              }}</span>
              <span class="text-p-sm text-ink-gray-6">
                {{
                  form.published
                    ? __('This form is live and accepting submissions.')
                    : __('Turn on to make this form public.')
                }}
              </span>
            </div>
            <Switch v-model="publishedModel" />
          </div>
          <div v-if="form.published" class="mt-4 flex items-center gap-2">
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
                  @click="copy(publicUrl)"
                >
                  <LucideCopy class="h-4 w-4" />
                </button>
              </template>
            </TextInput>
            <Button
              :label="__('Embed')"
              @click="(shareTab = 'iframe'), (shareOpen = true)"
            >
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
                        v-if="
                          ['Small Text', 'Text', 'Long Text'].includes(
                            f.fieldtype,
                          )
                        "
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
            :class="
              shareTab === t.key
                ? 'border-ink-gray-9 font-medium text-ink-gray-9'
                : 'border-transparent text-ink-gray-5 hover:text-ink-gray-7'
            "
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
              {{
                shareTab === 'iframe'
                  ? __('Paste into any HTML page.')
                  : __('Drop this script where the form should appear.')
              }}
            </p>
            <Button
              :label="copied ? __('Copied') : __('Copy')"
              @click="copy(shareSnippet)"
            />
          </div>
        </div>

        <div class="mt-4 border-t pt-4">
          <div class="text-sm text-ink-gray-7">{{ __('Allowed domains') }}</div>
          <p class="mt-0.5 text-xs text-ink-gray-4">
            {{
              __(
                'Sites where this form may be embedded, one per line. Browsers block the iframe on any site not listed here.',
              )
            }}
          </p>
          <textarea
            v-model="form.allowed_embedding_domains"
            rows="2"
            spellcheck="false"
            placeholder="https://www.example.com"
            class="mt-2 w-full resize-none rounded-md border border-outline-gray-2 px-3 py-2 font-mono text-xs text-ink-gray-8 outline-none focus:border-outline-gray-4"
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
          <p v-if="dirty" class="mt-1.5 text-xs text-ink-gray-4">
            {{ __('Click Update to apply domain changes.') }}
          </p>
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
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
import LucideCopy from '~icons/lucide/copy'
import Draggable from 'vuedraggable'
import LucideGripVertical from '~icons/lucide/grip-vertical'
import LucideX from '~icons/lucide/x'
import LucideShare2 from '~icons/lucide/share-2'
import LucideEye from '~icons/lucide/eye'
import LucidePencil from '~icons/lucide/pencil'
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
const expanded = ref(null) // fieldname of the expanded field editor
const shareOpen = ref(false)
const copied = ref(false)
const dragging = ref(false)

// Editing model: form.fields (flat) is the source of truth. It's derived into a
// pinned root section (fields before any section break) + a draggable list of
// sections, each holding draggable columns of draggable field items. After any
// drag / structural change we re-flatten back to form.fields.
const rootColumns = ref([{ colField: null, items: [] }])
const sections = ref([])

function newColumn(colField = null) {
  return { colField, items: [] }
}

function rebuildModel() {
  const root = [newColumn()]
  const secs = []
  let cols = root
  for (const f of form.fields || []) {
    if (f.fieldtype === 'Section Break') {
      const sec = { secField: f, columns: [newColumn()] }
      secs.push(sec)
      cols = sec.columns
    } else if (f.fieldtype === 'Column Break') {
      cols.push(newColumn(f))
    } else {
      cols[cols.length - 1].items.push(f)
    }
  }
  rootColumns.value = root
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
  emitColumns(out, rootColumns.value)
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
  allowed_embedding_domains: '',
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
const publicUrl = computed(
  () => `${window.location.origin}/crm-form/${form.route}`,
)
const embeddingDomains = computed(() =>
  (form.allowed_embedding_domains || '').split(/\s+/).filter(Boolean),
)

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
      `</` +
      `script>`
    )
  }
  return url
})

function markDirty() {
  dirty.value = true
}
function toggle(f) {
  expanded.value = expanded.value === f.fieldname ? null : f.fieldname
}
// the field whose editor is open (rendered full-width under its section)
const editingField = computed(
  () => form.fields.find((f) => f.fieldname === expanded.value) || null,
)
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

// columns in the last container (where a new Column Break would land)
const lastSectionColumns = computed(() => {
  const secs = sections.value
  return secs.length
    ? secs[secs.length - 1].columns.length
    : rootColumns.value.length
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
  url: 'crm.api.web_form.get_web_form_config',
  params: { name: props.name },
  auto: true,
  onSuccess: (doc) => {
    form.title = doc.title || ''
    form.route = doc.route || ''
    form.document_type = doc.document_type || 'CRM Lead'
    form.description = doc.description || ''
    form.submit_button_label = doc.submit_button_label || 'Submit'
    form.success_message = doc.success_message || ''
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
    rebuildModel()
    loaded.value = true
    availableFields.reload()
  },
})

const availableFields = createResource({
  url: 'crm.api.web_form.get_form_fields',
  makeParams: () => ({ document_type: form.document_type }),
})

// unused (not-yet-added) target fields, as Autocomplete options
const availableFieldOptions = computed(() => {
  const used = new Set(form.fields.map((f) => f.fieldname))
  return (availableFields.data || [])
    .filter((f) => !used.has(f.fieldname))
    .map((af) => ({ label: af.label, value: af.fieldname, af }))
})

function onPickField(option) {
  if (!option?.af) return
  addField(option.af)
}
function addField(af) {
  // append to the last column of the last section
  form.fields.push({
    fieldname: af.fieldname,
    label: af.label,
    fieldtype: af.fieldtype,
    options: af.options,
    reqd: !!af.reqd,
    placeholder: '',
    field_description: '',
  })
  rebuildModel()
  markDirty()
}
function removeField(f) {
  form.fields = form.fields.filter((x) => x !== f)
  if (expanded.value === f.fieldname) expanded.value = null
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
  rebuildModel()
  if (dropped) {
    toast.info(
      __('{0} field(s) removed — not available on {1}', [
        dropped,
        docLabel(form.document_type),
      ]),
    )
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
