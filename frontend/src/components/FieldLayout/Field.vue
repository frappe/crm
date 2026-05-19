<template>
  <div v-if="field.visible" class="field">
    <div
      v-if="
        field.fieldtype != 'Check' &&
        field.fieldtype != 'Button' &&
        field.fieldtype != 'HTML'
      "
      class="mb-2 text-sm text-ink-gray-5"
    >
      {{ __(field.label) }}
      <span
        v-if="
          field.reqd ||
          (field.mandatory_depends_on && field.mandatory_via_depends_on)
        "
        class="text-ink-red-2"
        >*</span
      >
    </div>
    <TextInput
      v-if="
        (field.read_only || field.fieldtype === 'Read Only') &&
        ![
          'Int',
          'Float',
          'Currency',
          'Percent',
          'Check',
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
      v-model="data[field.fieldname]"
      :placeholder="field.placeholder"
      :disabled="true"
      :description="field.description"
    />
    <Grid
      v-else-if="field.fieldtype === 'Table'"
      v-model="data[field.fieldname]"
      v-model:parent="data"
      :doctype="field.options"
      :parentDoctype="doctype"
      :parentFieldname="field.fieldname"
    />
    <Select
      v-else-if="field.fieldtype === 'Select'"
      v-model="data[field.fieldname]"
      class="form-control w-full"
      :class="field.prefix ? 'prefix' : ''"
      :options="field.options"
      :placeholder="field.placeholder"
      :description="field.description"
      @update:modelValue="(e) => fieldChange(e, field)"
    >
      <template v-if="field.prefix" #prefix>
        <IndicatorIcon :class="field.prefix" />
      </template>
    </Select>

    <Checkbox
      v-else-if="field.fieldtype == 'Check'"
      v-model="data[field.fieldname]"
      :label="field.label"
      class="form-control"
      :disabled="Boolean(field.read_only)"
      :description="field.description"
      :required="field.mandatory"
      @change="(e) => fieldChange(e.target.checked, field)"
    />

    <div
      v-else-if="['Link', 'Dynamic Link'].includes(field.fieldtype)"
      class="flex gap-1"
    >
      <Link
        v-model="data[field.fieldname]"
        class="form-control flex-1 truncate"
        :doctype="
          field.fieldtype == 'Link' ? field.options : data[field.options]
        "
        :filters="field.filters"
        :placeholder="field.placeholder"
        :allowCreate="true"
        :allowRedirect="true"
        @redirect="field.redirect"
        @create="field.create"
        @update:modelValue="(v) => fieldChange(v, field)"
      />
      <Button
        v-if="data[field.fieldname] && field.edit"
        class="shrink-0"
        :label="__('Edit')"
        :iconLeft="EditIcon"
        @click="field.edit(data[field.fieldname])"
      />
    </div>

    <TableMultiselectInput
      v-else-if="field.fieldtype === 'Table MultiSelect'"
      v-model="data[field.fieldname]"
      :doctype="field.options"
      @change="(v) => fieldChange(v, field)"
    />

    <Link
      v-else-if="field.fieldtype === 'User'"
      v-model="data[field.fieldname]"
      class="form-control w-full"
      :doctype="field.options"
      :filters="field.filters"
      :placeholder="field.placeholder"
      :hideMe="true"
      @update:modelValue="(v) => fieldChange(v, field)"
    >
      <template #item-prefix="{ item }">
        <UserAvatar class="mr-1" :user="item.value" size="sm" />
      </template>
    </Link>
    <Combobox
      v-else-if="field.fieldtype === 'Autocomplete'"
      v-model="data[field.fieldname]"
      class="w-full"
      :options="getOptions(field.options)"
      :placeholder="field.placeholder"
      :disabled="Boolean(field.read_only)"
      :openOnClick="true"
      @update:modelValue="(v) => fieldChange(v, field, data)"
    />
    <TimePicker
      v-else-if="field.fieldtype === 'Time'"
      v-model="data[field.fieldname]"
      :format="getFormat('', '', false, true, false)"
      :placeholder="field.placeholder"
      @change="(v) => fieldChange(v, field)"
    />
    <DateTimePicker
      v-else-if="field.fieldtype === 'Datetime'"
      v-model="data[field.fieldname]"
      :format="getFormat('', '', true, true, false)"
      :placeholder="field.placeholder"
      @change="(v) => fieldChange(v, field)"
    />
    <DatePicker
      v-else-if="field.fieldtype === 'Date'"
      v-model="data[field.fieldname]"
      :format="getFormat('', '', true, false, false)"
      :placeholder="field.placeholder"
      @change="(v) => fieldChange(v, field)"
    />
    <Textarea
      v-else-if="
        ['Small Text', 'Text', 'Long Text', 'Code'].includes(field.fieldtype)
      "
      v-model="data[field.fieldname]"
      :placeholder="field.placeholder"
      :description="field.description"
      @change="fieldChange($event.target.value, field)"
    />
    <Password
      v-else-if="field.fieldtype === 'Password'"
      v-model="data[field.fieldname]"
      :placeholder="field.placeholder"
      :description="field.description"
      @change="fieldChange($event.target.value, field)"
    />
    <FormattedInput
      v-else-if="field.fieldtype === 'Int'"
      :value="data[field.fieldname] || '0'"
      :placeholder="field.placeholder"
      :disabled="Boolean(field.read_only)"
      :description="field.description"
      @change="fieldChange($event.target.value, field)"
    />
    <FormattedInput
      v-else-if="field.fieldtype === 'Percent'"
      :value="getFormattedPercent(field.fieldname, data)"
      :placeholder="field.placeholder"
      :disabled="Boolean(field.read_only)"
      :description="field.description"
      @change="fieldChange(flt($event.target.value), field)"
    />
    <FormattedInput
      v-else-if="field.fieldtype === 'Float'"
      :value="getFormattedFloat(field.fieldname, data)"
      :placeholder="field.placeholder"
      :disabled="Boolean(field.read_only)"
      :description="field.description"
      @change="fieldChange(flt($event.target.value), field)"
    />
    <FormattedInput
      v-else-if="field.fieldtype === 'Currency'"
      :value="getFormattedCurrency(field.fieldname, data, parentDoc)"
      :placeholder="field.placeholder"
      :disabled="Boolean(field.read_only)"
      :description="field.description"
      @change="fieldChange(flt($event.target.value), field)"
    />
    <DurationInput
      v-else-if="field.fieldtype === 'Duration'"
      :value="data[field.fieldname]"
      :placeholder="field.placeholder"
      :disabled="Boolean(field.read_only)"
      :description="field.description"
      @change="(v) => fieldChange(v, field)"
    />
    <div
      v-else-if="field.fieldtype === 'Rating'"
      class="overflow-auto [&::-webkit-scrollbar]:h-0"
    >
      <RatingInput
        v-model="data[field.fieldname]"
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
      v-else-if="['Attach', 'Attach Image'].includes(field.fieldtype)"
      :value="data[field.fieldname]"
      :doctype="doctype"
      :docname="data.name"
      :fieldname="field.fieldname"
      :imageOnly="field.fieldtype === 'Attach Image'"
      :disabled="Boolean(field.read_only)"
      @change="(v) => fieldChange(v, field)"
    />
    <HtmlControl v-else-if="field.fieldtype === 'HTML'" :html="resolvedHtml" />
    <TextEditorControl
      v-else-if="field.fieldtype === 'Text Editor'"
      :value="data[field.fieldname]"
      :placeholder="field.placeholder"
      :disabled="Boolean(field.read_only)"
      @change="(v) => fieldChange(v, field)"
    />
    <GeolocationControl
      v-else-if="field.fieldtype === 'Geolocation'"
      :value="data[field.fieldname]"
      :disabled="Boolean(field.read_only)"
      @change="(v) => fieldChange(v, field)"
    />
    <TextInput
      v-else
      v-model="data[field.fieldname]"
      :placeholder="field.placeholder"
      :disabled="Boolean(field.read_only)"
      :description="field.description"
      @change="fieldChange($event.target.value, field)"
    />
  </div>
</template>
<script setup>
import FormattedInput from '@/components/Controls/FormattedInput.vue'
import DurationInput from '@/components/Controls/DurationInput.vue'
import RatingInput from '@/components/Controls/RatingInput.vue'
import AttachControl from '@/components/Controls/AttachControl.vue'
import HtmlControl from '@/components/Controls/HtmlControl.vue'
import TextEditorControl from '@/components/Controls/TextEditorControl.vue'
import GeolocationControl from '@/components/Controls/GeolocationControl.vue'
import ButtonControl, {
  getButtonTheme,
  getButtonVariant,
} from '@/components/Controls/ButtonControl.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import TableMultiselectInput from '@/components/Controls/TableMultiselectInput.vue'
import Grid from '@/components/Controls/Grid.vue'
import { createDocument } from '@/composables/document'
import { useDoctypeModal } from '@/composables/doctypeModal'
import {
  getFormat,
  evaluateDependsOnValue,
  isNull,
  interpolateTemplate,
} from '@/utils'
import { flt, formatNumber, formatCurrency } from '@/utils/numberFormat.js'
import { getMeta } from '@/stores/meta'
import { parseLinkFilters, getPlaceholder } from '@/utils/fieldTransforms'
import { usersStore } from '@/stores/users'
import { useDocument } from '@/data/document'

import {
  Checkbox,
  Combobox,
  Select,
  DatePicker,
  DateTimePicker,
  TimePicker,
  TextInput,
  Textarea,
  Password,
} from 'frappe-ui'
import { Link } from 'frappe-ui/frappe'
import { computed, provide, inject, ref } from 'vue'

const props = defineProps({
  field: { type: Object, required: true },
})

const data = inject('data')
const doctype = inject('doctype')
const preview = inject('preview')
const isGridRow = inject('isGridRow')

// Guard getMeta — skip when doctype is empty (inline/standalone mode)
let getFormattedPercent, getFormattedFloat, getFormattedCurrency
if (doctype) {
  ;({ getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
    getMeta(doctype))
} else {
  getFormattedPercent = (fn, doc) => formatNumber(doc[fn], '', null) + '%'
  getFormattedFloat = (fn, doc) => formatNumber(doc[fn], '', null)
  getFormattedCurrency = (fn, doc) =>
    formatCurrency(doc[fn], '', window.sysdefaults?.currency || 'USD', null)
}

const { users } = usersStore()
const { showModal } = useDoctypeModal()

let triggerOnChange
let triggerButton
let parentDoc
const formDocument = ref(null)

// Standalone mode: context injected from FieldLayout when context prop is set
const standaloneContext = inject('fieldLayoutContext', null)

if (standaloneContext) {
  // Standalone mode — no useDocument, no scripting triggers
  // Field changes update data directly
  triggerOnChange = async (fieldname, value, row) => {
    if (row) {
      row[fieldname] = value
    } else {
      data.value[fieldname] = value
    }
  }
  triggerButton = async () => {}
  formDocument.value = standaloneContext

  // Provide no-op triggers for child Grid components
  provide('triggerOnChange', triggerOnChange)
  provide('triggerButton', triggerButton)
  provide('triggerOnRowAdd', async () => {})
  provide('triggerOnRowRemove', async () => {})
  provide(
    'fieldPropertyOverrides',
    computed(() => standaloneContext?.fieldPropertyOverrides || {}),
  )
} else if (!isGridRow) {
  const {
    triggerOnChange: trigger,
    triggerButton: triggerBtn,
    triggerOnRowAdd,
    triggerOnRowRemove,
    document: doc,
  } = useDocument(doctype, data.value.name)
  triggerOnChange = trigger
  triggerButton = triggerBtn
  formDocument.value = doc

  provide('triggerOnChange', triggerOnChange)
  provide('triggerButton', triggerButton)
  provide('triggerOnRowAdd', triggerOnRowAdd)
  provide('triggerOnRowRemove', triggerOnRowRemove)
  provide(
    'fieldPropertyOverrides',
    computed(() => formDocument.value?.fieldPropertyOverrides || {}),
  )
} else {
  triggerOnChange = inject('triggerOnChange', () => {})
  triggerButton = inject('triggerButton', () => {})
  parentDoc = inject('parentDoc')
}

// For grid rows: inject overrides provided by Grid.vue
const injectedOverrides = inject(
  'fieldPropertyOverrides',
  computed(() => ({})),
)
const injectedParentFieldname = inject('parentFieldname', '')

/**
 * Resolve field property overrides.
 * For grid row fields, uses dot notation (parentfield.childfield)
 * with per-row support (parentfield.childfield:rowName).
 * For normal fields, reads directly from formDocument.
 */
function getFieldOverrides(fieldname) {
  if (isGridRow) {
    const ov = injectedOverrides.value || {}
    const pf = injectedParentFieldname
    if (!pf) return undefined

    const colKey = `${pf}.${fieldname}`
    const rowName = data.value?.name
    const rowKey = rowName ? `${colKey}:${rowName}` : null

    const colOv = ov[colKey]
    const rowOv = rowKey ? ov[rowKey] : null

    if (!colOv && !rowOv) return undefined
    return { ...(colOv || {}), ...(rowOv || {}) }
  }
  return formDocument.value?.fieldPropertyOverrides?.[fieldname]
}

const field = computed(() => {
  let field = { ...props.field }

  // ── Script property overrides ──
  const overrides = getFieldOverrides(field.fieldname)
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
      name: ['in', users.data.crmUsers?.map((user) => user.name)],
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
        showModal({
          name: value,
          doctype: field.options,
        })
      }
    }
  }

  const read_only_via_depends_on = evaluateDependsOnValue(
    field.read_only_depends_on,
    data.value,
  )

  // Script overrides for read_only take priority over depends_on
  const scriptReadOnly = overrides?.read_only
  const effectiveReadOnly =
    scriptReadOnly !== undefined
      ? scriptReadOnly
      : field.read_only ||
        (field.read_only_depends_on && read_only_via_depends_on)

  // Script overrides for depends_on visibility
  const scriptHidden = overrides?.hidden
  const displayViaDependsOn = evaluateDependsOnValue(
    field.depends_on,
    data.value,
  )

  let _field = {
    ...field,
    filters: parseLinkFilters(field.link_filters),
    placeholder: getPlaceholder(field),
    display_via_depends_on: displayViaDependsOn,
    mandatory_via_depends_on: evaluateDependsOnValue(
      field.mandatory_depends_on,
      data.value,
    ),
    read_only: effectiveReadOnly,
  }

  _field.visible = isFieldVisible(_field, scriptHidden)
  return _field
})

function isFieldVisible(field, scriptHidden) {
  if (preview.value) return true

  // Script override for hidden wins over everything
  if (scriptHidden !== undefined) return !scriptHidden

  let readOnlyField =
    field.read_only || field.fieldtype === 'Read Only' ? true : false

  let hideEmptyReadOnlyField =
    isNull(data.value[field.fieldname]) &&
    Number(window.sysdefaults?.hide_empty_read_only_fields ?? 1)

  let showReadOnlyField = readOnlyField && !hideEmptyReadOnlyField

  return (
    (field.fieldtype == 'Check' || showReadOnlyField || !readOnlyField) &&
    (!field.depends_on || field.display_via_depends_on) &&
    !field.hidden
  )
}

const resolvedHtml = computed(() => {
  if (field.value.fieldtype !== 'HTML') return ''
  const injected = formDocument.value?.fieldHtmlMap?.[field.value.fieldname]
  if (injected !== undefined) return injected
  return interpolateTemplate(field.value.options || '', data.value)
})

const getOptions = (options) => {
  if (Array.isArray(options)) {
    return options
  } else if (typeof options === 'string') {
    return options.split('\n').map((option) => {
      return { label: option, value: option }
    })
  } else {
    return []
  }
}

async function handleButtonClick(field) {
  if (typeof field.click === 'function') {
    return await field.click(data.value)
  } else {
    return await triggerButton(field.fieldname)
  }
}

async function fieldChange(value, df) {
  value = Array.isArray(value)
    ? value
    : typeof value === 'object' && value !== null && 'value' in value
      ? value.value
      : value

  if (isGridRow) {
    await triggerOnChange(df.fieldname, value, data.value)
  } else {
    await triggerOnChange(df.fieldname, value)
  }
}
</script>
<style scoped>
:deep(.form-control.prefix select) {
  padding-left: 2rem;
}
</style>
