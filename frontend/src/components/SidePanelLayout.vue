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
                    class="field flex items-center gap-2 px-3 leading-5 first:mt-3"
                  >
                    <Tooltip :text="__(field.label)" :hoverDelay="1">
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
                    <div class="flex items-center justify-between w-[65%]">
                      <div
                        class="grid min-h-[28px] flex-1 items-center overflow-hidden text-base"
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
                        <FormControl
                          v-else-if="field.fieldtype == 'Check'"
                          class="form-control"
                          type="checkbox"
                          v-model="doc[field.fieldname]"
                          @change.stop="
                            fieldChange($event.target.checked, field)
                          "
                          :disabled="Boolean(field.read_only)"
                        />
                        <FormControl
                          v-else-if="
                            [
                              'Small Text',
                              'Text',
                              'Long Text',
                              'Code',
                            ].includes(field.fieldtype)
                          "
                          class="form-control"
                          type="textarea"
                          :value="doc[field.fieldname]"
                          :placeholder="field.placeholder"
                          :debounce="500"
                          @change.stop="fieldChange($event.target.value, field)"
                        />
                        <FormControl
                          v-else-if="field.fieldtype === 'Select'"
                          class="form-control cursor-pointer [&_select]:cursor-pointer truncate"
                          type="select"
                          v-model="doc[field.fieldname]"
                          :options="field.options"
                          :placeholder="field.placeholder"
                          @change.stop="fieldChange($event.target.value, field)"
                        />
                        <Link
                          v-else-if="field.fieldtype === 'User'"
                          class="form-control"
                          :value="
                            doc[field.fieldname] &&
                            getUser(doc[field.fieldname]).full_name
                          "
                          doctype="User"
                          :filters="field.filters"
                          @change="(v) => fieldChange(v, field)"
                          :placeholder="'Select' + ' ' + field.label + '...'"
                          :hideMe="true"
                        >
                          <template v-if="doc[field.fieldname]" #prefix>
                            <UserAvatar
                              class="mr-1.5"
                              :user="doc[field.fieldname]"
                              size="sm"
                            />
                          </template>
                          <template #item-prefix="{ option }">
                            <UserAvatar
                              class="mr-1.5"
                              :user="option.value"
                              size="sm"
                            />
                          </template>
                          <template #item-label="{ option }">
                            <Tooltip :text="option.value">
                              <div class="cursor-pointer">
                                {{ getUser(option.value).full_name }}
                              </div>
                            </Tooltip>
                          </template>
                        </Link>
                        <Link
                          v-else-if="
                            ['Link', 'Dynamic Link'].includes(field.fieldtype)
                          "
                          class="form-control select-text"
                          :value="doc[field.fieldname]"
                          :doctype="
                            field.fieldtype == 'Link'
                              ? field.options
                              : doc[field.options]
                          "
                          :filters="field.filters"
                          :placeholder="field.placeholder"
                          @change="(v) => fieldChange(v, field)"
                          :onCreate="field.create"
                        />
                        <div
                          v-else-if="field.fieldtype === 'Time'"
                          class="form-control"
                        >
                          <TimePicker
                            :value="doc[field.fieldname]"
                            :format="getFormat('', '', false, true, false)"
                            :placeholder="field.placeholder"
                            @change="(v) => fieldChange(v, field)"
                          />
                        </div>
                        <div
                          v-else-if="field.fieldtype === 'Datetime'"
                          class="form-control"
                        >
                          <DateTimePicker
                            :value="doc[field.fieldname]"
                            :format="getFormat('', '', true, true, false)"
                            :placeholder="field.placeholder"
                            placement="left-start"
                            @change="(v) => fieldChange(v, field)"
                          />
                        </div>
                        <div
                          v-else-if="field.fieldtype === 'Date'"
                          class="form-control"
                        >
                          <DatePicker
                            :value="doc[field.fieldname]"
                            :format="getFormat('', '', true, false, false)"
                            :placeholder="field.placeholder"
                            placement="left-start"
                            @change="(v) => fieldChange(v, field)"
                          />
                        </div>
                        <FormattedInput
                          v-else-if="field.fieldtype === 'Percent'"
                          class="form-control"
                          type="text"
                          :value="getFormattedPercent(field.fieldname, doc)"
                          :placeholder="field.placeholder"
                          :debounce="500"
                          @change.stop="
                            fieldChange(flt($event.target.value), field)
                          "
                          :disabled="Boolean(field.read_only)"
                        />
                        <Password
                          v-else-if="field.fieldtype === 'Password'"
                          class="form-control"
                          :value="doc[field.fieldname]"
                          :placeholder="field.placeholder"
                          :debounce="500"
                          @change.stop="fieldChange($event.target.value, field)"
                          :disabled="Boolean(field.read_only)"
                        />
                        <FormattedInput
                          v-else-if="field.fieldtype === 'Int'"
                          class="form-control"
                          type="text"
                          :value="doc[field.fieldname] || '0'"
                          :placeholder="field.placeholder"
                          :debounce="500"
                          @change.stop="fieldChange($event.target.value, field)"
                          :disabled="Boolean(field.read_only)"
                        />
                        <FormattedInput
                          v-else-if="field.fieldtype === 'Float'"
                          class="form-control"
                          type="text"
                          :value="getFormattedFloat(field.fieldname, doc)"
                          :placeholder="field.placeholder"
                          :debounce="500"
                          @change.stop="
                            fieldChange(flt($event.target.value), field)
                          "
                          :disabled="Boolean(field.read_only)"
                        />
                        <FormattedInput
                          v-else-if="field.fieldtype === 'Currency'"
                          class="form-control"
                          type="text"
                          :value="getFormattedCurrency(field.fieldname, doc)"
                          :placeholder="field.placeholder"
                          :debounce="500"
                          @change.stop="
                            fieldChange(flt($event.target.value), field)
                          "
                          :disabled="Boolean(field.read_only)"
                        />
                        <FormControl
                          v-else
                          class="form-control"
                          type="text"
                          :value="doc[field.fieldname]"
                          :placeholder="field.placeholder"
                          :debounce="500"
                          @change.stop="fieldChange($event.target.value, field)"
                        />
                      </div>
                      <div class="ml-1">
                        <ArrowUpRightIcon
                          v-if="
                            field.fieldtype === 'Link' &&
                            field.link &&
                            doc[field.fieldname]
                          "
                          class="h-4 w-4 shrink-0 cursor-pointer text-ink-gray-5 hover:text-ink-gray-8"
                          @click.stop="field.link(doc[field.fieldname])"
                        />
                        <EditIcon
                          v-if="
                            field.fieldtype === 'Link' &&
                            field.edit &&
                            doc[field.fieldname]
                          "
                          class="size-3.5 shrink-0 cursor-pointer text-ink-gray-5 hover:text-ink-gray-8"
                          @click.stop="field.edit(doc[field.fieldname])"
                        />
                      </div>
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
import Password from '@/components/Controls/Password.vue'
import FormattedInput from '@/components/Controls/FormattedInput.vue'
import CollapsibleSection from '@/components/CollapsibleSection.vue'
import PrimaryDropdown from '@/components/PrimaryDropdown.vue'
import FadedScrollableDiv from '@/components/FadedScrollableDiv.vue'
import ArrowUpRightIcon from '@/components/Icons/ArrowUpRightIcon.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import Link from '@/components/Controls/Link.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import SidePanelModal from '@/components/Modals/SidePanelModal.vue'
import { getMeta } from '@/stores/meta'
import { usersStore } from '@/stores/users'
import { isMobileView } from '@/composables/settings'
import { getFormat, evaluateDependsOnValue } from '@/utils'
import { flt } from '@/utils/numberFormat.js'
import { Tooltip, DateTimePicker, DatePicker, TimePicker } from 'frappe-ui'
import { useDocument } from '@/data/document'
import { ref, computed, getCurrentInstance } from 'vue'

const props = defineProps({
  sections: {
    type: Object,
  },
  doctype: {
    type: String,
    default: 'CRM Lead',
    required: true,
  },
  docname: {
    type: String,
    required: true,
  },
  preview: {
    type: Boolean,
    default: false,
  },
  addContact: {
    type: Function,
  },
})

const emit = defineEmits(['beforeFieldChange', 'afterFieldChange', 'reload'])

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
  getMeta(props.doctype)

const { users, isManager, getUser } = usersStore()

const showSidePanelModal = ref(false)

let document = { doc: {} }
let triggerOnChange

if (props.docname) {
  let d = useDocument(props.doctype, props.docname)
  document = d.document
  triggerOnChange = d.triggerOnChange
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
  if (field.fieldtype == 'Select' && typeof field.options === 'string') {
    field.options = field.options.split('\n').map((option) => {
      return { label: option, value: option }
    })

    if (field.options[0].value !== '') {
      field.options.unshift({ label: '', value: '' })
    }
  }

  if (field.fieldtype === 'Link' && field.options === 'User') {
    field.fieldtype = 'User'
    field.link_filters = JSON.stringify({
      ...(field.link_filters ? JSON.parse(field.link_filters) : {}),
      name: ['in', users.data?.crmUsers?.map((user) => user.name)],
    })
  }

  let _field = {
    ...field,
    filters: field.link_filters && JSON.parse(field.link_filters),
    placeholder: field.placeholder || field.label,
    display_via_depends_on: evaluateDependsOnValue(field.depends_on, doc.value),
    mandatory_via_depends_on: evaluateDependsOnValue(
      field.mandatory_depends_on,
      doc.value,
    ),
  }

  _field.visible = isFieldVisible(_field)
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
  let isContactSection = section.name == 'contacts_section'
  section.showEditButton = !(
    isMobileView.value ||
    !isManager() ||
    isContactSection ||
    editButtonAdded
  )

  section.visible =
    isContactSection ||
    section.columns?.[0].fields.filter((f) => f.visible).length

  return section
}

function isFieldVisible(field) {
  if (props.preview) return true

  const hideEmptyReadOnly = Number(window.sysdefaults?.hide_empty_read_only_fields ?? 1)

  const shouldShowReadOnly = field.read_only && (
    doc.value?.[field.fieldname] ||
    !hideEmptyReadOnly
  )

  return (
    (field.fieldtype == 'Check' ||
      shouldShowReadOnly ||
      !field.read_only) &&
    (!field.depends_on || field.display_via_depends_on) &&
    !field.hidden
  )
}

function firstVisibleIndex() {
  return _sections.value.findIndex((section) => section.visible)
}
</script>

<style scoped>
.form-control {
  margin: 2px;
}

:deep(.form-control input:not([type='checkbox'])),
:deep(.form-control select),
:deep(.form-control textarea),
:deep(.form-control button),
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
