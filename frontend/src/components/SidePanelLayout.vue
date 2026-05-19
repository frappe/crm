<template>
  <div class="sections flex flex-col overflow-y-auto">
    <template v-for="(section, i) in _sections" :key="section.name">
      <div v-if="section.visible" class="section flex flex-col">
        <div
          v-if="i !== firstVisibleIndex()"
          class="w-full section-border h-px border-t"
        />
        <div class="p-1 sm:p-3">
          <CollapsibleSection
            labelClass="px-2 font-semibold"
            headerClass="h-8"
            :label="section.label"
            :hideLabel="!section.label"
            :opened="section.opened"
          >
            <template v-if="!preview" #actions>
              <slot name="actions" v-bind="{ section }">
                <Button
                  v-if="section.showEditButton"
                  variant="ghost"
                  class="w-7 mr-2"
                  :icon="EditIcon"
                  @click="showSidePanelModal = true"
                />
              </slot>
            </template>
            <slot v-bind="{ section }">
              <FadedScrollableDiv
                v-if="section.columns?.[0].fields.length"
                class="column flex flex-col gap-1.5 overflow-y-auto"
              >
                <template
                  v-for="field in section.columns[0].fields || []"
                  :key="field.fieldname"
                >
                  <div
                    v-if="field.visible"
                    class="field flex gap-2 px-3 leading-5 first:mt-3"
                    :class="
                      ['Small Text', 'Text', 'Long Text', 'Code'].includes(
                        field.fieldtype,
                      )
                        ? 'items-baseline'
                        : 'items-center'
                    "
                  >
                    <Tooltip
                      v-if="!['Button', 'HTML'].includes(field.fieldtype)"
                      :text="__(field.label)"
                      :hoverDelay="1"
                    >
                      <div
                        class="w-[35%] min-w-20 shrink-0 flex items-center gap-0.5"
                      >
                        <div class="truncate text-sm text-ink-gray-5">
                          {{ __(field.label) }}
                        </div>
                        <div
                          v-if="
                            field.reqd ||
                            (field.mandatory_depends_on &&
                              field.mandatory_via_depends_on)
                          "
                          class="text-ink-red-2"
                        >
                          *
                        </div>
                      </div>
                    </Tooltip>
                    <div
                      class="flex min-h-[28px] flex-1 items-center overflow-hidden text-base p-0.5"
                    >
                      <div
                        v-if="
                          field.read_only &&
                          ![
                            'Int',
                            'Float',
                            'Currency',
                            'Percent',
                            'Check',
                            'Dropdown',
                            'Duration',
                            'Rating',
                            'Button',
                            'Attach',
                            'Attach Image',
                            'HTML',
                            'Geolocation',
                            'Text Editor',
                          ].includes(field.fieldtype)
                        "
                        class="flex h-7 cursor-pointer items-center px-2 py-1 text-ink-gray-5"
                      >
                        <Tooltip :text="__(field.tooltip)">
                          <div>{{ doc[field.fieldname] }}</div>
                        </Tooltip>
                      </div>
                      <PrimaryDropdown
                        v-else-if="field.fieldtype === 'Dropdown'"
                        :value="doc[field.fieldname]"
                        :placeholder="field.placeholder"
                        :options="field.options"
                        :create="field.create"
                        :label="field.label"
                      />
                      <Checkbox
                        v-else-if="field.fieldtype == 'Check'"
                        v-model="doc[field.fieldname]"
                        class="form-control"
                        :disabled="Boolean(field.read_only)"
                        @change.stop="fieldChange($event.target.checked, field)"
                      />
                      <Textarea
                        v-else-if="
                          ['Small Text', 'Text', 'Long Text', 'Code'].includes(
                            field.fieldtype,
                          )
                        "
                        v-model="doc[field.fieldname]"
                        class="form-control"
                        :rows="1"
                        :placeholder="field.placeholder"
                        :debounce="500"
                        @change.stop="fieldChange($event.target.value, field)"
                      />
                      <Select
                        v-else-if="field.fieldtype === 'Select'"
                        v-model="doc[field.fieldname]"
                        class="form-control truncate w-full"
                        :options="field.options"
                        :placeholder="field.placeholder"
                        @update:modelValue="(v) => fieldChange(v, field)"
                      />
                      <Link
                        v-else-if="field.fieldtype === 'User'"
                        v-model="doc[field.fieldname]"
                        class="combobox w-full"
                        doctype="User"
                        :filters="field.filters"
                        :placeholder="field.placeholder"
                        @update:modelValue="(v) => fieldChange(v, field)"
                      >
                        <template #item-prefix="{ item }">
                          <UserAvatar
                            class="mr-1"
                            :user="item.value"
                            size="sm"
                          />
                        </template>
                      </Link>
                      <Link
                        v-else-if="
                          ['Link', 'Dynamic Link'].includes(field.fieldtype)
                        "
                        v-model="doc[field.fieldname]"
                        class="combobox w-full"
                        :doctype="
                          field.fieldtype == 'Link'
                            ? field.options
                            : doc[field.options]
                        "
                        :filters="field.filters"
                        :placeholder="field.placeholder"
                        :allowCreate="true"
                        :allowRedirect="true"
                        @create="field.create"
                        @redirect="field.redirect"
                        @update:modelValue="(v) => fieldChange(v, field)"
                      />
                      <div
                        v-else-if="field.fieldtype === 'Time'"
                        class="form-control w-full"
                      >
                        <TimePicker
                          v-model="doc[field.fieldname]"
                          :format="getFormat('', '', false, true, false)"
                          :placeholder="field.placeholder"
                          @change="(v) => fieldChange(v, field)"
                        />
                      </div>
                      <div
                        v-else-if="field.fieldtype === 'Datetime'"
                        class="form-control w-full"
                      >
                        <DateTimePicker
                          v-model="doc[field.fieldname]"
                          :format="getFormat('', '', true, true, false)"
                          :placeholder="field.placeholder"
                          side="left"
                          align="start"
                          @change="(v) => fieldChange(v, field)"
                        />
                      </div>
                      <div
                        v-else-if="field.fieldtype === 'Date'"
                        class="form-control w-full"
                      >
                        <DatePicker
                          v-model="doc[field.fieldname]"
                          :format="getFormat('', '', true, false, false)"
                          :placeholder="field.placeholder"
                          side="left"
                          align="start"
                          @change="(v) => fieldChange(v, field)"
                        />
                      </div>
                      <Password
                        v-else-if="field.fieldtype === 'Password'"
                        v-model="doc[field.fieldname]"
                        class="form-control w-full"
                        :placeholder="field.placeholder"
                        :debounce="500"
                        :disabled="Boolean(field.read_only)"
                        @change.stop="fieldChange($event.target.value, field)"
                      />
                      <FormattedInput
                        v-else-if="field.fieldtype === 'Percent'"
                        class="form-control w-full"
                        :value="getFormattedPercent(field.fieldname, doc)"
                        :placeholder="field.placeholder"
                        :debounce="500"
                        :disabled="Boolean(field.read_only)"
                        @change.stop="
                          fieldChange(flt($event.target.value), field)
                        "
                      />
                      <FormattedInput
                        v-else-if="field.fieldtype === 'Int'"
                        class="form-control w-full"
                        :value="doc[field.fieldname] || '0'"
                        :placeholder="field.placeholder"
                        :debounce="500"
                        :disabled="Boolean(field.read_only)"
                        @change.stop="fieldChange($event.target.value, field)"
                      />
                      <FormattedInput
                        v-else-if="field.fieldtype === 'Float'"
                        class="form-control w-full"
                        :value="getFormattedFloat(field.fieldname, doc)"
                        :placeholder="field.placeholder"
                        :debounce="500"
                        :disabled="Boolean(field.read_only)"
                        @change.stop="
                          fieldChange(flt($event.target.value), field)
                        "
                      />
                      <FormattedInput
                        v-else-if="field.fieldtype === 'Currency'"
                        class="form-control w-full"
                        :value="getFormattedCurrency(field.fieldname, doc)"
                        :placeholder="field.placeholder"
                        :debounce="500"
                        :disabled="Boolean(field.read_only)"
                        @change.stop="
                          fieldChange(flt($event.target.value), field)
                        "
                      />
                      <DurationInput
                        v-else-if="field.fieldtype === 'Duration'"
                        class="form-control"
                        :value="doc[field.fieldname]"
                        :placeholder="field.placeholder"
                        :disabled="Boolean(field.read_only)"
                        @change="(v) => fieldChange(v, field)"
                      />
                      <div
                        v-else-if="field.fieldtype === 'Rating'"
                        class="ml-2 overflow-auto [&::-webkit-scrollbar]:h-0"
                      >
                        <RatingInput
                          v-model="doc[field.fieldname]"
                          :max="field.options || 5"
                          :disabled="Boolean(field.read_only)"
                          @update:modelValue="(v) => fieldChange(v, field)"
                        />
                      </div>
                      <ButtonControl
                        v-else-if="field.fieldtype === 'Button'"
                        :label="field.label"
                        :icon="field.icon"
                        :theme="getButtonTheme(field.button_color)"
                        :variant="getButtonVariant(field.button_color)"
                        :disabled="Boolean(field.read_only)"
                        @click="handleButtonClick(field)"
                      />
                      <AttachControl
                        v-else-if="
                          ['Attach', 'Attach Image'].includes(field.fieldtype)
                        "
                        class="attach-control"
                        :value="doc[field.fieldname]"
                        :doctype="doctype"
                        :docname="doc.name"
                        :fieldname="field.fieldname"
                        :imageOnly="field.fieldtype === 'Attach Image'"
                        :disabled="Boolean(field.read_only)"
                        @change="(v) => fieldChange(v, field)"
                      />
                      <HtmlControl
                        v-else-if="field.fieldtype === 'HTML'"
                        :html="
                          document.fieldHtmlMap?.[field.fieldname] !== undefined
                            ? document.fieldHtmlMap[field.fieldname]
                            : interpolateTemplate(field.options || '', doc)
                        "
                      />
                      <GeolocationControl
                        v-else-if="field.fieldtype === 'Geolocation'"
                        class="geolocation-control"
                        :value="doc[field.fieldname]"
                        :disabled="Boolean(field.read_only)"
                        @change="(v) => fieldChange(v, field)"
                      />
                      <TextEditorControl
                        v-else-if="field.fieldtype === 'Text Editor'"
                        variant="ghost"
                        :fixed-menu="false"
                        :bubble-menu="true"
                        editorClass="w-full !min-h-[38px] !h-[38px] ml-1"
                        :value="doc[field.fieldname]"
                        :placeholder="field.placeholder"
                        :disabled="Boolean(field.read_only)"
                        @change="(v) => fieldChange(v, field)"
                      />
                      <TextInput
                        v-else
                        v-model="doc[field.fieldname]"
                        class="form-control w-full"
                        :placeholder="field.placeholder"
                        :debounce="500"
                        @change.stop="fieldChange($event.target.value, field)"
                      />
                    </div>
                  </div>
                </template>
              </FadedScrollableDiv>
            </slot>
          </CollapsibleSection>
        </div>
      </div>
    </template>
  </div>
  <SidePanelModal
    v-if="showSidePanelModal"
    v-model="showSidePanelModal"
    :doctype="doctype"
    @reload="() => emit('reload')"
  />
</template>

<script setup>
import FormattedInput from '@/components/Controls/FormattedInput.vue'
import DurationInput from '@/components/Controls/DurationInput.vue'
import RatingInput from '@/components/Controls/RatingInput.vue'
import AttachControl from '@/components/Controls/AttachControl.vue'
import HtmlControl from '@/components/Controls/HtmlControl.vue'
import GeolocationControl from '@/components/Controls/GeolocationControl.vue'
import TextEditorControl from '@/components/Controls/TextEditorControl.vue'
import ButtonControl, {
  getButtonTheme,
  getButtonVariant,
} from '@/components/Controls/ButtonControl.vue'
import CollapsibleSection from '@/components/CollapsibleSection.vue'
import PrimaryDropdown from '@/components/PrimaryDropdown.vue'
import FadedScrollableDiv from '@/components/FadedScrollableDiv.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import SidePanelModal from '@/components/Modals/SidePanelModal.vue'
import { getMeta } from '@/stores/meta'
import { parseLinkFilters, getPlaceholder } from '@/utils/fieldTransforms'
import { usersStore } from '@/stores/users'
import { isMobileView } from '@/composables/settings'
import { createDocument } from '@/composables/document'
import { useDoctypeModal } from '@/composables/doctypeModal'
import {
  getFormat,
  evaluateDependsOnValue,
  isNull,
  interpolateTemplate,
} from '@/utils'
import { flt } from '@/utils/numberFormat.js'
import {
  TextInput,
  Select,
  Tooltip,
  DateTimePicker,
  DatePicker,
  TimePicker,
  Textarea,
  Checkbox,
  Password,
} from 'frappe-ui'
import { Link } from 'frappe-ui/frappe'
import { useDocument } from '@/data/document'
import { ref, computed, getCurrentInstance } from 'vue'

const props = defineProps({
  sections: { type: Object, default: () => ({}) },
  doctype: { type: String, default: 'CRM Lead' },
  docname: { type: String, required: true },
  preview: { type: Boolean, default: false },
  addContact: { type: Function, default: null },
})

const emit = defineEmits(['beforeFieldChange', 'afterFieldChange', 'reload'])

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
  getMeta(props.doctype)

const { users, isManager } = usersStore()
const { showModal } = useDoctypeModal()

const showSidePanelModal = ref(false)

let document = { doc: {} }
let triggerOnChange
let triggerButton = () => {}

if (props.docname) {
  let d = useDocument(props.doctype, props.docname)
  document = d.document
  triggerOnChange = d.triggerOnChange
  triggerButton = d.triggerButton
}

const doc = computed(() => document.doc || {})

const _sections = computed(() => {
  if (!props.sections?.length) return []
  let editButtonAdded = false
  return props.sections.map((section) => {
    if (section.columns?.length) {
      section.columns[0].fields = section.columns[0].fields.map((field) => {
        return parsedField(field)
      })
    }
    let _section = parsedSection(section, editButtonAdded)
    if (_section.showEditButton) {
      editButtonAdded = true
    }
    return _section
  })
})

function parsedField(field) {
  // Clone to avoid mutating the cached layout data
  field = { ...field }

  // Merge script property overrides
  const overrides = document.fieldPropertyOverrides?.[field.fieldname]
  if (overrides) {
    Object.assign(field, overrides)
  }

  if (field.fieldtype == 'Select' && typeof field.options === 'string') {
    field.options = field.options.split('\n').map((option) => {
      return { label: option, value: option }
    })
  }

  if (field.fieldtype === 'Link' && field.options === 'User') {
    field.fieldtype = 'User'
    field.link_filters = JSON.stringify({
      name: ['in', users.data?.crmUsers?.map((user) => user.name)],
      ignore_user_type: 1,
      ...(parseLinkFilters(field.link_filters) || {}),
    })
  }

  if (field.fieldtype === 'Link' && field.options !== 'User') {
    if (!field.create) {
      field.create = (value) => {
        const callback = (d) => {
          if (d) fieldChange(d.name, field)
        }
        createDocument(field.options, value, callback)
      }
    }
    if (!field.redirect) {
      field.redirect = (value) => {
        if (field.link) return field.link(value)

        showModal({
          name: value,
          doctype: field.options,
        })
      }
    }
  }

  const read_only_via_depends_on = evaluateDependsOnValue(
    field.read_only_depends_on,
    doc.value,
  )

  // Script overrides for read_only take priority over depends_on
  const scriptReadOnly = overrides?.read_only
  const effectiveReadOnly =
    scriptReadOnly !== undefined
      ? scriptReadOnly
      : field.read_only ||
        (field.read_only_depends_on && read_only_via_depends_on)

  let _field = {
    ...field,
    filters: parseLinkFilters(field.link_filters),
    placeholder: getPlaceholder(field),
    display_via_depends_on: evaluateDependsOnValue(field.depends_on, doc.value),
    mandatory_via_depends_on: evaluateDependsOnValue(
      field.mandatory_depends_on,
      doc.value,
    ),
    read_only: effectiveReadOnly,
  }

  _field.visible = isFieldVisible(_field, overrides?.hidden)
  return _field
}

const instance = getCurrentInstance()
const attrs = instance?.vnode?.props ?? {}

async function fieldChange(value, df) {
  if (props.preview) return

  await triggerOnChange(df.fieldname, value)

  const hasListener = attrs['onBeforeFieldChange'] !== undefined

  if (hasListener) {
    emit('beforeFieldChange', { [df.fieldname]: value })
  } else {
    document.save.submit(null, {
      onSuccess: () => emit('afterFieldChange', { [df.fieldname]: value }),
    })
  }
}

function parsedSection(section, editButtonAdded) {
  // Merge script property overrides for section
  const overrides = document.fieldPropertyOverrides?.[section.name]
  if (overrides) {
    section = { ...section, ...overrides }
  }

  let isContactSection = section.name == 'contacts_section'
  section.showEditButton = !(
    isMobileView.value ||
    !isManager() ||
    isContactSection ||
    editButtonAdded
  )

  // Script hidden override for sections
  if (overrides?.hidden !== undefined) {
    section.visible = !overrides.hidden
  } else {
    section.visible =
      isContactSection ||
      section.columns?.[0].fields.filter((f) => f.visible).length
  }

  return section
}

function isFieldVisible(field, scriptHidden) {
  if (props.preview) return true

  // Script override for hidden wins over everything
  if (scriptHidden !== undefined) return !scriptHidden

  let readOnlyField =
    field.read_only || field.fieldtype === 'Read Only' ? true : false

  let hideEmptyReadOnlyField =
    isNull(doc.value[field.fieldname]) &&
    Number(window.sysdefaults?.hide_empty_read_only_fields ?? 1)

  let showReadOnlyField = readOnlyField && !hideEmptyReadOnlyField

  return (
    (field.fieldtype == 'Check' ||
      field.fieldtype == 'Button' ||
      showReadOnlyField ||
      !readOnlyField) &&
    (!field.depends_on || field.display_via_depends_on) &&
    !field.hidden
  )
}

async function handleButtonClick(field) {
  if (props.preview) return

  if (typeof field.click === 'function') {
    await field.click(doc.value)
  } else {
    await triggerButton(field.fieldname)
  }
}

function firstVisibleIndex() {
  return _sections.value.findIndex((section) => section.visible)
}
</script>

<style scoped>
:deep(.form-control input:not([type='checkbox'])),
:deep(.form-control select),
:deep(textarea.form-control),
:deep(.form-control button),
:deep(button.form-control),
:deep(.attach-control),
:deep(.geolocation-control),
:deep(.combobox),
.dropdown-button {
  border-color: transparent;
  background: transparent;
}

:deep(.form-control button) {
  gap: 0;
}
:deep(.form-control [type='checkbox']) {
  margin-left: 9px;
  cursor: pointer;
}

:deep(.form-control button > div) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:deep(.form-control button svg) {
  color: white;
  width: 0;
}

.sections .section .column {
  max-height: 300px;
}
.sections .section:last-of-type .column {
  max-height: none;
}
</style>
