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
      :tabs="tabs"
      v-slot="{ tab }"
      :tablistClass="
        !hasTabs ? 'hidden' : modal ? 'border-outline-gray-modals' : ''
      "
    >
      <div :class="{ 'my-4 sm:my-6': hasTabs }">
        <div
          v-for="(section, i) in tab.sections"
          :key="section.label"
          class="section"
        >
          <div
            v-if="i != 0"
            class="w-full"
            :class="[section.hideBorder ? 'mt-4' : 'h-px border-t my-5']"
          />
          <Section
            class="text-lg font-medium"
            :class="{ 'px-3 sm:px-5': hasTabs }"
            :label="section.label"
            :hideLabel="section.hideLabel"
            :opened="section.opened"
            :collapsible="section.collapsible"
            collapseIconPosition="right"
          >
            <div
              class="grid gap-4"
              :class="[
                gridClass(section.columns, section),
                { 'px-3 sm:px-5': hasTabs },
                { 'mt-6': !section.hideLabel },
              ]"
            >
              <div 
                v-for="field in section.fields" 
                :key="field.name"
                :class="{
                  'col-start-1 sm:col-start-2 lg:col-start-3 justify-self-end': field.name === 'status' || field.name === 'lead_owner' || field.name === 'deal_owner',
                  'w-[180px]': field.name === 'status' || field.name === 'lead_owner' || field.name === 'deal_owner'
                }"
              >
                <div
                  class="settings-field"
                  v-if="
                    (field.type == 'Check' ||
                      (field.read_only && data[field.name]) ||
                      !field.read_only ||
                      !field.hidden) &&
                    (!field.depends_on || field.display_via_depends_on)
                  "
                >
                  <div
                    v-if="field.type != 'Check'"
                    class="mb-2 text-sm text-ink-gray-5"
                  >
                    {{ __(field.label) }}
                    <span
                      class="text-ink-red-3"
                      v-if="
                        field.mandatory ||
                        (field.mandatory_depends_on &&
                          field.mandatory_via_depends_on)
                      "
                      >*</span
                    >
                  </div>
                  <FormControl
                    v-if="field.read_only && field.type !== 'Check'"
                    type="text"
                    :placeholder="getPlaceholder(field)"
                    v-model="data[field.name]"
                    :disabled="true"
                  />
                  <FormControl
                    v-else-if="field.type === 'Select' || field.name === 'gender'"
                    type="select"
                    class="form-control"
                    :class="[
                      field.prefix || field.prefixFn ? 'prefix' : '',
                      field.name === 'status' ? 'status-select' : ''
                    ]"
                    :options="field.name === 'gender' ? [
                      { label: __('Male'), value: 'Male' },
                      { label: __('Female'), value: 'Female' }
                    ] : field.name === 'status' ? field.options.map(status => ({
                      label: getTranslatedStatus(field, status.value),
                      value: status.value
                    })) : field.options"
                    v-model="data[field.name]"
                    :placeholder="getPlaceholder(field)"
                  >
                    <template v-if="field.prefix || field.prefixFn || field.name === 'status'" #prefix>
                      <IndicatorIcon :class="field.name === 'status' ? getStatusPrefix(field, data[field.name]) : field.prefixFn ? field.prefixFn(data[field.name]) : field.prefix" />
                    </template>
                    <template v-if="field.prefixFn || field.name === 'status'" #option="{ option }">
                      <div class="flex items-center gap-2">
                        <IndicatorIcon :class="field.name === 'status' ? getStatusPrefix(field, option.value) : field.prefixFn(option.value)" />
                        {{ option.label }}
                      </div>
                    </template>
                  </FormControl>
                  <div
                    v-else-if="field.type == 'Check'"
                    class="flex items-center gap-2"
                  >
                    <FormControl
                      class="form-control"
                      type="checkbox"
                      v-model="data[field.name]"
                      @change="(e) => (data[field.name] = e.target.checked)"
                      :disabled="Boolean(field.read_only)"
                    />
                    <label
                      class="text-sm text-ink-gray-5"
                      @click="data[field.name] = !data[field.name]"
                    >
                      {{ __(field.label) }}
                      <span class="text-ink-red-3" v-if="field.mandatory"
                        >*</span
                      >
                    </label>
                  </div>
                  <div class="flex gap-1" v-else-if="field.type === 'Link'">
                    <template v-if="field.options === 'Country'">
                      <CountryLink
                        class="form-control flex-1 truncate"
                        :value="data[field.name]"
                        :doctype="field.options"
                        :filters="field.filters"
                        @change="(v) => (data[field.name] = v)"
                        :placeholder="getPlaceholder(field)"
                        :onCreate="field.create"
                      />
                    </template>
                    <template v-else-if="field.options === 'User'">
                      <Link
                        class="form-control flex-1 truncate"
                        :value="data[field.name] ? getUser(data[field.name]).full_name : ''"
                        :doctype="field.options"
                        :filters="field.filters"
                        @change="(v) => (data[field.name] = v)"
                        :placeholder="getPlaceholder(field)"
                        :hideMe="true"
                      >
                        <template #prefix>
                          <UserAvatar
                            v-if="data[field.name]"
                            class="mr-2"
                            :user="data[field.name]"
                            size="sm"
                          />
                        </template>
                        <template #item-prefix="{ option }">
                          <UserAvatar class="mr-2" :user="option.value" size="sm" />
                        </template>
                        <template #item-label="{ option }">
                          <Tooltip :text="option.value">
                            <div class="cursor-pointer text-ink-gray-8 dark:text-gray-500">
                              {{ getUser(option.value).full_name }}
                            </div>
                          </Tooltip>
                        </template>
                      </Link>
                    </template>
                    <template v-else>
                      <Link
                        class="form-control flex-1 truncate"
                        :value="data[field.name]"
                        :doctype="field.options"
                        :filters="field.filters"
                        @change="(v) => (data[field.name] = v)"
                        :placeholder="getPlaceholder(field)"
                        :onCreate="field.create"
                      />
                    </template>
                    <Button
                      v-if="data[field.name] && field.edit"
                      class="shrink-0"
                      :label="__('Edit')"
                      @click="field.edit(data[field.name])"
                    >
                      <template #prefix>
                        <EditIcon class="h-4 w-4" />
                      </template>
                    </Button>
                  </div>
                  <input
                    v-else-if="field.type === 'Date'"
                    type="date"
                    class="form-input w-full"
                    v-model="data[field.name]"
                    :placeholder="__('Set date')"
                  />
                  <input
                    v-else-if="field.type === 'Datetime'"
                    type="datetime-local"
                    class="form-input w-full"
                    v-model="data[field.name]"
                    :placeholder="__('Set date and time')"
                  />
                  <FormControl
                    v-else-if="
                      ['Small Text', 'Text', 'Long Text'].includes(field.type)
                    "
                    type="textarea"
                    :placeholder="getPlaceholder(field)"
                    v-model="data[field.name]"
                  />
                  <FormControl
                    v-else-if="['Int'].includes(field.type)"
                    type="number"
                    :placeholder="getPlaceholder(field)"
                    v-model="data[field.name]"
                  />
                  <FormControl
                    v-else
                    type="text"
                    :placeholder="getPlaceholder(field)"
                    v-model="data[field.name]"
                    :disabled="Boolean(field.read_only)"
                  />
                </div>
              </div>
            </div>
          </Section>
        </div>
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
import CountryLink from '@/components/Controls/CountryLink.vue'
import { usersStore } from '@/stores/users'
import { statusesStore } from '@/stores/statuses'
import { getFormat } from '@/utils'
import { translateLeadStatus } from '@/utils/leadStatusTranslations'
import { translateDealStatus } from '@/utils/dealStatusTranslations'
import { Tabs, Tooltip, DatePicker, DateTimePicker, Dropdown, Button } from 'frappe-ui'
import { ref, computed } from 'vue'
import { FeatherIcon } from 'frappe-ui'

const { getUser } = usersStore()
const { getLeadStatus, getDealStatus } = statusesStore()

const props = defineProps({
  tabs: Array,
  data: Object,
  modal: {
    type: Boolean,
    default: false,
  },
})

const hasTabs = computed(() => !props.tabs[0].no_tabs)

const tabIndex = ref(0)

function gridClass(columns, section) {
  columns = columns || 3
  if (columns === 2 && section?.fields?.length === 2 && 
      section.fields.some(f => f.name === 'status') && 
      (section.fields.some(f => f.name === 'lead_owner') || section.fields.some(f => f.name === 'deal_owner'))) {
    return 'grid-cols-1 sm:grid-cols-2'
  }
  let hasLeadOwner = section?.fields?.some(f => f.name === 'lead_owner')
  let hasDealOwner = section?.fields?.some(f => f.name === 'deal_owner')
  let hasStatus = section?.fields?.some(f => f.name === 'status')
  if (hasLeadOwner || hasDealOwner || hasStatus) {
    return 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 relative'
  }
  let griColsMap = {
    1: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-1',
    2: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-2',
    3: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4',
  }
  return griColsMap[columns]
}

const getPlaceholder = (field) => {
  if (field.placeholder) {
    return __(field.placeholder)
  }
  if (['Select', 'Link'].includes(field.type)) {
    return `${__('Select')} ${__(field.label)}`
  } else {
    return `${__('Enter')} ${__(field.label)}`
  }
}

function getTranslatedStatus(field, status) {
  if (!status) return ''
  if (field.name === 'status') {
    if (field.doctype === 'CRM Lead') {
      return translateLeadStatus(status)
    } else if (field.doctype === 'CRM Deal') {
      return translateDealStatus(status)
    }
  }
  return status
}

function getStatusPrefix(field, status) {
  if (!status) return ''
  if (field.name === 'status') {
    if (field.doctype === 'CRM Lead') {
      const statusInfo = getLeadStatus(status)
      return statusInfo?.iconColorClass[0]
    } else if (field.doctype === 'CRM Deal') {
      const statusInfo = getDealStatus(status)
      return statusInfo?.iconColorClass[0]
    }
  }
  return field.prefixFn ? field.prefixFn(status) : field.prefix
}

</script>

<style scoped>
:deep(.form-control.prefix select) {
  padding-left: 2rem;
}

.section {
  display: none;
}

.section:has(.settings-field) {
  display: block;
}

:deep(:has(> .dropdown-button)) {
  width: 100%;
}

:deep(.flex-col.overflow-y-auto) {
  overflow: visible !important;
}
</style>
