<template>
  <FadedScrollableDiv
    class="flex flex-col gap-1.5 overflow-y-auto dark-scrollbar"
    :class="[isLastSection ? '' : 'max-h-[300px]']"
  >
    <div
      v-for="field in _fields"
      :key="field.label"
      :class="[field.hidden && 'hidden']"
      class="section-field flex items-center gap-2 px-3 leading-5 first:mt-3"
    >
      <Tooltip :text="__(field.label)" :hoverDelay="1">
        <div class="w-[35%] min-w-20 shrink-0 truncate text-sm text-ink-gray-5">
          <span>{{ __(field.label) }}</span>
          <span class="text-ink-red-3">{{ field.reqd ? ' *' : '' }}</span>
        </div>
      </Tooltip>
      <div class="flex items-center justify-between w-[65%]">
        <div
          class="grid min-h-[28px] flex-1 items-center overflow-hidden text-base"
        >
          <div
            v-if="
              field.read_only && !['checkbox', 'dropdown'].includes(field.type)
            "
            class="flex h-7 cursor-pointer items-center px-2 py-1 text-ink-gray-5"
          >
            <Tooltip :text="__(field.tooltip)">
              <div>{{ localData[field.name] }}</div>
            </Tooltip>
          </div>
          <div v-else-if="field.type === 'dropdown'">
            <NestedPopover>
              <template #target="{ open }">
                <Button
                  :label="data[field.name]"
                  class="dropdown-button flex w-full items-center justify-between rounded border border-gray-100 bg-surface-gray-2 px-2 py-1.5 text-base text-ink-gray-8 placeholder-ink-gray-4 transition-colors hover:border-outline-gray-modals hover:bg-surface-gray-3 focus:border-outline-gray-4 focus:bg-surface-white focus:shadow-sm focus:outline-none focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3"
                >
                  <div v-if="data[field.name]" class="truncate">
                    {{ data[field.name] }}
                  </div>
                  <div
                    v-else
                    class="text-base leading-5 text-ink-gray-4 truncate"
                  >
                    {{ field.placeholder }}
                  </div>
                  <template #suffix>
                    <FeatherIcon
                      :name="open ? 'chevron-up' : 'chevron-down'"
                      class="h-4 text-ink-gray-5"
                    />
                  </template>
                </Button>
              </template>
              <template #body>
                <div
                  class="my-2 p-1.5 min-w-40 space-y-1.5 divide-y divide-outline-gray-1 rounded-lg bg-surface-modal shadow-2xl ring-1 ring-black ring-opacity-5 focus:outline-none"
                >
                  <div>
                    <DropdownItem
                      v-if="field.options?.length"
                      v-for="option in field.options"
                      :key="option.name"
                      :option="option"
                    />
                    <div v-else>
                      <div class="p-1.5 px-7 text-base text-ink-gray-4">
                        {{ __('No {0} Available', [field.label]) }}
                      </div>
                    </div>
                  </div>
                  <div class="pt-1.5">
                    <Button
                      variant="ghost"
                      class="w-full !justify-start"
                      :label="__('Create New')"
                      @click="field.create()"
                    >
                      <template #prefix>
                        <FeatherIcon name="plus" class="h-4" />
                      </template>
                    </Button>
                  </div>
                </div>
              </template>
            </NestedPopover>
          </div>
          <FormControl
            v-else-if="field.type == 'checkbox'"
            class="form-control"
            :type="field.type"
            v-model="data[field.name]"
            @change.stop="handleChange(field.name, $event.target.checked)"
            :disabled="Boolean(field.read_only)"
          />
          <FormControl
            v-else-if="
              ['email', 'number', 'password', 'textarea'].includes(field.type)
            "
            class="form-control"
            :type="field.type"
            :value="data[field.name]"
            :placeholder="field.placeholder"
            :debounce="500"
            @change.stop="handleChange(field.name, $event.target.value)"
          />
          <FormControl
            v-else-if="field.type === 'select'"
            class="form-control cursor-pointer [&_select]:cursor-pointer truncate"
            type="select"
            v-model="data[field.name]"
            :options="field.options"
            :placeholder="field.placeholder"
            @change.stop="handleChange(field.name, $event.target.value)"
          >
            <template v-if="field.prefix" #prefix>
              <IndicatorIcon :class="field.prefix" />
            </template>
          </FormControl>
          <Link
            v-else-if="['lead_owner', 'deal_owner'].includes(field.name)"
            class="form-control"
            :value="data[field.name] && getUser(data[field.name]).full_name"
            doctype="User"
            :filters="field.filters"
            @change="(data) => handleChange(field.name, data)"
            :placeholder="'Select' + ' ' + field.label + '...'"
            :hideMe="true"
          >
            <template v-if="data[field.name]" #prefix>
              <UserAvatar class="mr-1.5" :user="data[field.name]" size="sm" />
            </template>
            <template #item-prefix="{ option }">
              <UserAvatar class="mr-1.5" :user="option.value" size="sm" />
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
            v-else-if="field.type === 'link'"
            class="form-control select-text"
            :value="data[field.name]"
            :doctype="field.doctype"
            :filters="field.filters"
            :placeholder="field.placeholder"
            @change="(data) => handleChange(field.name, data)"
            :onCreate="field.create"
          />
          <input
            v-else-if="field.type === 'Date'"
            type="date"
            :class="field.class"
            :value="data[field.name]"
            @input="handleChange(field.name, $event.target.value)"
            :placeholder="field.placeholder"
          />
          <input
            v-else-if="field.type === 'Datetime'"
            type="datetime-local"
            :class="field.class"
            :value="data[field.name]"
            @input="handleChange(field.name, $event.target.value)"
            :placeholder="field.placeholder"
          />
          <FormControl
            v-else
            class="form-control"
            type="text"
            :value="data[field.name]"
            :placeholder="field.placeholder"
            :debounce="500"
            @change.stop="handleChange(field.name, $event.target.value)"
          />
        </div>
        <div class="ml-1">
          <ArrowUpRightIcon
            v-if="field.type === 'link' && field.link && data[field.name]"
            class="h-4 w-4 shrink-0 cursor-pointer text-ink-gray-5 hover:text-ink-gray-8"
            @click.stop="field.link(data[field.name])"
          />
          <EditIcon
            v-if="field.type === 'link' && field.edit && data[field.name]"
            class="size-3.5 shrink-0 cursor-pointer text-ink-gray-5 hover:text-ink-gray-8"
            @click.stop="field.edit(data[field.name])"
          />
        </div>
      </div>
    </div>
  </FadedScrollableDiv>
</template>

<script setup>
import NestedPopover from '@/components/NestedPopover.vue'
import DropdownItem from '@/components/DropdownItem.vue'
import FadedScrollableDiv from '@/components/FadedScrollableDiv.vue'
import ArrowUpRightIcon from '@/components/Icons/ArrowUpRightIcon.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import Link from '@/components/Controls/Link.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import { usersStore } from '@/stores/users'
import { getFormat } from '@/utils'
import { Tooltip } from 'frappe-ui'
import { computed, watch, ref } from 'vue'

const props = defineProps({
  fields: {
    type: Object,
  },
  isLastSection: {
    type: Boolean,
    default: false,
  },
})

const { getUser } = usersStore()

const emit = defineEmits(['update', 'change'])

const data = defineModel()
const localData = ref({})
const originalData = ref({})
const isInternalChange = ref(false)

// Initialize localData and originalData when modelValue changes
watch(data, (newValue, oldValue) => {
  if (!newValue) return
  
  if (isInternalChange.value) {
    isInternalChange.value = false
    return
  }
  
  localData.value = { ...newValue }
  if (Object.keys(originalData.value).length === 0) {
    originalData.value = { ...newValue }
  }
  checkDirty()
}, { deep: true })

function checkDirty() {
  const hasChanges = Object.keys(localData.value).some(key => {
    if (key === '_organizationObj') {
      const origOrg = originalData.value._organizationObj || {}
      const currentOrg = localData.value._organizationObj || {}
      return Object.keys(currentOrg).some(orgKey => {
        if (orgKey === 'modified' || orgKey === 'modified_by') return false
        return origOrg[orgKey] !== currentOrg[orgKey]
      })
    }
    
    if (key.startsWith('_')) return false
    
    const originalValue = originalData.value[key]
    const currentValue = localData.value[key]
    if (!originalValue && !currentValue) return false
    if (originalValue === '' && currentValue === '') return false
    if (originalValue === currentValue) return false
    return true
  })
  emit('change', hasChanges)
}

function handleChange(fieldName, value) {
  isInternalChange.value = true
  localData.value[fieldName] = value
  emit('update', fieldName, value)
  checkDirty()
}

function resetOriginalData() {
  originalData.value = { ...localData.value }
  checkDirty()
}

defineExpose({
  resetOriginalData
})

const _fields = computed(() => {
  let all_fields = []
  props.fields?.forEach((field) => {
    let df = field?.all_properties

    // Handle special case for gender field
    if (field.name === 'gender') {
      all_fields.push({
        ...field,
        type: 'select',
        options: [
          { label: __('Male'), value: 'Male' },
          { label: __('Female'), value: 'Female' }
        ],
        placeholder: `${__('Select')} ${__(field.label)}`
      })
      return
    }

    if (df?.depends_on) evaluate_depends_on(df.depends_on, field)
    all_fields.push({
      ...field,
      filters: df?.link_filters && JSON.parse(df.link_filters),
      placeholder: getPlaceholder(field),
    })
  })
  return all_fields
})

function getPlaceholder(field) {
  if (field.placeholder) {
    return __(field.placeholder)
  }
  if (['select', 'link'].includes(field.type?.toLowerCase())) {
    return __('Select {0}', [__(field.label)])
  }
  return field.label
}

function evaluate_depends_on(expression, field) {
  if (expression.substr(0, 5) == 'eval:') {
    try {
      let out = evaluate(expression.substr(5), { doc: data.value })
      if (!out) {
        field.hidden = true
      }
    } catch (e) {
      console.error(e)
    }
  }
}

function evaluate(code, context = {}) {
  let variable_names = Object.keys(context)
  let variables = Object.values(context)
  code = `let out = ${code}; return out`
  try {
    let expression_function = new Function(...variable_names, code)
    return expression_function(...variables)
  } catch (error) {
    console.log('Error evaluating the following expression:')
    console.error(code)
    throw error
  }
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
</style>
