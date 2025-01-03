<template>
  <div
    class="flex flex-col"
    :class="{
      'border border-outline-gray-1 rounded-lg': hasTabs,
      'border-outline-gray-modals': modal && hasTabs,
    }"
  >
    <Tabs
      v-model="tabIndex"
      class="!h-full"
      :tabs="_tabs"
      v-slot="{ tab }"
      :tablistClass="
        !hasTabs ? 'hidden' : modal ? 'border-outline-gray-modals' : ''
      "
    >
      <div
        class="sections overflow-hidden"
        :class="{ 'my-4 sm:my-6': hasTabs }"
      >
        <template v-for="(section, i) in tab.sections" :key="section.name">
          <div v-if="section.visible" class="section" :data-name="section.name">
            <div
              v-if="i !== firstVisibleIndex(tab.sections)"
              class="w-full section-border"
              :class="[section.hideBorder ? 'mt-4' : 'h-px border-t my-5']"
            />
            <Section
              class="flex sm:flex-row flex-col gap-4 text-lg font-medium"
              :class="{
                'px-3 sm:px-5': hasTabs,
                'mt-6': section.label && !section.hideLabel,
              }"
              :labelClass="['text-lg font-medium', { 'px-3 sm:px-5': hasTabs }]"
              :label="section.label"
              :hideLabel="section.hideLabel || !section.label"
              :opened="section.opened"
              :collapsible="section.collapsible"
              collapseIconPosition="right"
            >
              <div
                class="column flex flex-col gap-4 w-full"
                v-for="column in section.columns"
                :key="column.name"
                :data-name="column.name"
              >
                <div
                  v-if="column.label && !column.hideLabel"
                  class="text-ink-gray-9 max-w-fit text-base"
                >
                  {{ column.label }}
                </div>
                <template v-for="field in column.fields" :key="field.fieldname">
                  <div v-if="field.visible" class="field">
                    <div
                      v-if="field.fieldtype != 'Check'"
                      class="mb-2 text-sm text-ink-gray-5"
                    >
                      {{ __(field.label) }}
                      <span
                        v-if="
                          field.reqd ||
                          (field.mandatory_depends_on &&
                            field.mandatory_via_depends_on)
                        "
                        class="text-ink-red-3"
                        >*</span
                      >
                    </div>
                    <FormControl
                      v-if="field.read_only && field.fieldtype !== 'Check'"
                      type="text"
                      :placeholder="getPlaceholder(field)"
                      v-model="data[field.fieldname]"
                      :disabled="true"
                    />
                    <Grid
                      v-else-if="field.fieldtype === 'Table'"
                      v-model="data[field.fieldname]"
                      :doctype="field.options"
                      :parentDoctype="doctype"
                    />
                    <FormControl
                      v-else-if="field.fieldtype === 'Select'"
                      type="select"
                      class="form-control"
                      :class="field.prefix ? 'prefix' : ''"
                      :options="field.options"
                      v-model="data[field.fieldname]"
                      :placeholder="getPlaceholder(field)"
                    >
                      <template v-if="field.prefix" #prefix>
                        <IndicatorIcon :class="field.prefix" />
                      </template>
                    </FormControl>
                    <div
                      v-else-if="field.fieldtype == 'Check'"
                      class="flex items-center gap-2"
                    >
                      <FormControl
                        class="form-control"
                        type="checkbox"
                        v-model="data[field.fieldname]"
                        @change="
                          (e) => (data[field.fieldname] = e.target.checked)
                        "
                        :disabled="Boolean(field.read_only)"
                      />
                      <label
                        class="text-sm text-ink-gray-5"
                        @click="
                          () => {
                            if (!Boolean(field.read_only)) {
                              data[field.fieldname] = !data[field.fieldname]
                            }
                          }
                        "
                      >
                        {{ __(field.label) }}
                        <span class="text-ink-red-3" v-if="field.mandatory"
                          >*</span
                        >
                      </label>
                    </div>
                    <div
                      class="flex gap-1"
                      v-else-if="field.fieldtype === 'Link'"
                    >
                      <Link
                        class="form-control flex-1 truncate"
                        :value="data[field.fieldname]"
                        :doctype="field.options"
                        :filters="field.filters"
                        @change="(v) => (data[field.fieldname] = v)"
                        :placeholder="getPlaceholder(field)"
                        :onCreate="field.create"
                      />
                      <Button
                        v-if="data[field.fieldname] && field.edit"
                        class="shrink-0"
                        :label="__('Edit')"
                        @click="field.edit(data[field.fieldname])"
                      >
                        <template #prefix>
                          <EditIcon class="h-4 w-4" />
                        </template>
                      </Button>
                    </div>

                    <Link
                      v-else-if="field.fieldtype === 'User'"
                      class="form-control"
                      :value="
                        data[field.fieldname] &&
                        getUser(data[field.fieldname]).full_name
                      "
                      :doctype="field.options"
                      :filters="field.filters"
                      @change="(v) => (data[field.fieldname] = v)"
                      :placeholder="getPlaceholder(field)"
                      :hideMe="true"
                    >
                      <template #prefix>
                        <UserAvatar
                          v-if="data[field.fieldname]"
                          class="mr-2"
                          :user="data[field.fieldname]"
                          size="sm"
                        />
                      </template>
                      <template #item-prefix="{ option }">
                        <UserAvatar
                          class="mr-2"
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
                    <DateTimePicker
                      v-else-if="field.fieldtype === 'Datetime'"
                      v-model="data[field.fieldname]"
                      icon-left=""
                      :formatter="(date) => getFormat(date, '', true, true)"
                      :placeholder="getPlaceholder(field)"
                      input-class="border-none"
                    />
                    <DatePicker
                      v-else-if="field.fieldtype === 'Date'"
                      icon-left=""
                      v-model="data[field.fieldname]"
                      :formatter="(date) => getFormat(date, '', true)"
                      :placeholder="getPlaceholder(field)"
                      input-class="border-none"
                    />
                    <FormControl
                      v-else-if="
                        ['Small Text', 'Text', 'Long Text', 'Code'].includes(
                          field.fieldtype,
                        )
                      "
                      type="textarea"
                      :placeholder="getPlaceholder(field)"
                      v-model="data[field.fieldname]"
                    />
                    <FormControl
                      v-else-if="['Int'].includes(field.fieldtype)"
                      type="number"
                      :placeholder="getPlaceholder(field)"
                      v-model="data[field.fieldname]"
                    />
                    <FormControl
                      v-else-if="field.fieldtype === 'Percent'"
                      type="text"
                      :value="getFormattedPercent(field.fieldname, data)"
                      :placeholder="getPlaceholder(field)"
                      :disabled="Boolean(field.read_only)"
                      @change="data[field.fieldname] = flt($event.target.value)"
                    />
                    <FormControl
                      v-else-if="field.fieldtype === 'Float'"
                      type="text"
                      :value="getFormattedFloat(field.fieldname, data)"
                      :placeholder="getPlaceholder(field)"
                      :disabled="Boolean(field.read_only)"
                      @change="data[field.fieldname] = flt($event.target.value)"
                    />
                    <FormControl
                      v-else-if="field.fieldtype === 'Currency'"
                      type="text"
                      :value="getFormattedCurrency(field.fieldname, data)"
                      :placeholder="getPlaceholder(field)"
                      :disabled="Boolean(field.read_only)"
                      @change="data[field.fieldname] = flt($event.target.value)"
                    />
                    <FormControl
                      v-else
                      type="text"
                      :placeholder="getPlaceholder(field)"
                      v-model="data[field.fieldname]"
                      :disabled="Boolean(field.read_only)"
                    />
                  </div>
                </template>
              </div>
            </Section>
          </div>
        </template>
      </div>
    </Tabs>
  </div>
</template>

<script setup>
import Section from '@/components/Section.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import Link from '@/components/Controls/Link.vue'
import Grid from '@/components/Controls/Grid.vue'
import { getMeta } from '@/stores/meta'
import { usersStore } from '@/stores/users'
import { getFormat, evaluateDependsOnValue } from '@/utils'
import { flt } from '@/utils/numberFormat.js'
import { Tabs, Tooltip, DatePicker, DateTimePicker } from 'frappe-ui'
import { ref, computed } from 'vue'

const props = defineProps({
  tabs: Array,
  data: Object,
  doctype: {
    type: String,
    default: 'CRM Lead',
  },
  modal: {
    type: Boolean,
    default: false,
  },
  preview: {
    type: Boolean,
    default: false,
  },
})

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
  getMeta(props.doctype)
const { getUser } = usersStore()

const hasTabs = computed(() => {
  return (
    props.tabs.length > 1 || (props.tabs.length == 1 && props.tabs[0].label)
  )
})

const _tabs = computed(() => {
  return props.tabs.map((tab) => {
    tab.sections = tab.sections.map((section) => {
      section.columns = section.columns.map((column) => {
        column.fields = column.fields.map((field) => {
          return parsedField(field)
        })
        return column
      })
      return parsedSection(section)
    })
    return tab
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
    field.options = field.options
    field.fieldtype = 'User'
  }

  let _field = {
    ...field,
    filters: field.link_filters && JSON.parse(field.link_filters),
    placeholder: field.placeholder || field.label,
    display_via_depends_on: evaluateDependsOnValue(
      field.depends_on,
      props.data,
    ),
    mandatory_via_depends_on: evaluateDependsOnValue(
      field.mandatory_depends_on,
      props.data,
    ),
  }

  _field.visible = isFieldVisible(_field)
  return _field
}

function parsedSection(section) {
  section.visible = section.columns.some((column) =>
    column.fields.some((field) => field.visible),
  )

  // to handle special case
  if (section.hidden) {
    section.visible = false
  }
  return section
}

function isFieldVisible(field) {
  if (props.preview) return true
  return (
    (field.fieldtype == 'Check' ||
      (field.read_only && props.data[field.fieldname]) ||
      !field.read_only) &&
    (!field.depends_on || field.display_via_depends_on) &&
    !field.hidden
  )
}

function firstVisibleIndex(sections) {
  return sections.findIndex((section) => section.visible)
}

const tabIndex = ref(0)

const getPlaceholder = (field) => {
  if (field.placeholder) {
    return __(field.placeholder)
  }
  if (['Select', 'Link'].includes(field.fieldtype)) {
    return __('Select {0}', [__(field.label)])
  } else {
    return __('Enter {0}', [__(field.label)])
  }
}
</script>

<style scoped>
:deep(.form-control.prefix select) {
  padding-left: 2rem;
}
</style>
