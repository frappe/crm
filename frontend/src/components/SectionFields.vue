<template>
  <FadedScrollableDiv
    class="flex flex-col gap-1.5 overflow-y-auto"
    :class="[isLastSection ? '' : 'max-h-[300px]']"
  >
    <div
      v-for="field in _fields"
      :key="field.label"
      :class="[field.hidden && 'hidden']"
      class="section-field flex items-center gap-2 px-3 leading-5 first:mt-3"
    >
      <Tooltip :text="__(field.label)" :hoverDelay="1">
        <div class="w-[35%] min-w-20 shrink-0 truncate text-sm text-gray-600">
          <span>{{ __(field.label) }}</span>
          <span class="text-red-500">{{ field.reqd ? ' *' : '' }}</span>
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
            class="flex h-7 cursor-pointer items-center px-2 py-1 text-gray-600"
          >
            <Tooltip :text="__(field.tooltip)">
              <div>{{ data[field.name] }}</div>
            </Tooltip>
          </div>
          <div v-else-if="field.type === 'dropdown'">
            <NestedPopover>
              <template #target="{ open }">
                <Button
                  :label="data[field.name]"
                  class="dropdown-button flex w-full items-center justify-between rounded border border-gray-100 bg-gray-100 px-2 py-1.5 text-base text-gray-800 placeholder-gray-500 transition-colors hover:border-gray-200 hover:bg-gray-200 focus:border-gray-500 focus:bg-white focus:shadow-sm focus:outline-none focus:ring-0 focus-visible:ring-2 focus-visible:ring-gray-400"
                >
                  <div v-if="data[field.name]" class="truncate">
                    {{ data[field.name] }}
                  </div>
                  <div v-else class="text-base leading-5 text-gray-500 truncate">
                    {{ field.placeholder }}
                  </div>
                  <template #suffix>
                    <FeatherIcon
                      :name="open ? 'chevron-up' : 'chevron-down'"
                      class="h-4 text-gray-600"
                    />
                  </template>
                </Button>
              </template>
              <template #body>
                <div
                  class="my-2 space-y-1.5 divide-y rounded-lg border border-gray-100 bg-white p-1.5 shadow-xl"
                >
                  <div>
                    <DropdownItem
                      v-if="field.options?.length"
                      v-for="option in field.options"
                      :key="option.name"
                      :option="option"
                    />
                    <div v-else>
                      <div class="p-1.5 px-7 text-base text-gray-500">
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
            @change.stop="emit('update', field.name, $event.target.checked)"
            :disabled="Boolean(field.read_only)"
          />
          <FormControl
            v-else-if="
              ['email', 'number', 'date', 'password', 'textarea'].includes(
                field.type,
              )
            "
            class="form-control"
            :class="{
              '[&_input]:text-gray-500':
                field.type === 'date' && !data[field.name],
            }"
            :type="field.type"
            :value="data[field.name]"
            :placeholder="field.placeholder"
            :debounce="500"
            @change.stop="emit('update', field.name, $event.target.value)"
          />
          <FormControl
            v-else-if="field.type === 'select'"
            class="form-control cursor-pointer [&_select]:cursor-pointer truncate"
            type="select"
            v-model="data[field.name]"
            :options="field.options"
            :placeholder="field.placeholder"
            @change.stop="emit('update', field.name, $event.target.value)"
          />
          <Link
            v-else-if="['lead_owner', 'deal_owner'].includes(field.name)"
            class="form-control"
            :value="data[field.name] && getUser(data[field.name]).full_name"
            doctype="User"
            :filters="field.filters"
            @change="(data) => emit('update', field.name, data)"
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
            @change="(data) => emit('update', field.name, data)"
            :onCreate="field.create"
          />
          <FormControl
            v-else
            class="form-control"
            type="text"
            :value="data[field.name]"
            :placeholder="field.placeholder"
            :debounce="500"
            @change.stop="emit('update', field.name, $event.target.value)"
          />
        </div>
        <ArrowUpRightIcon
          v-if="field.type === 'link' && field.link && data[field.name]"
          class="h-4 w-4 shrink-0 cursor-pointer text-gray-600 hover:text-gray-800"
          @click="field.link(data[field.name])"
        />
        <EditIcon
          v-if="field.type === 'link' && field.edit && data[field.name]"
          class="size-3.5 shrink-0 cursor-pointer text-gray-600 hover:text-gray-800"
          @click="field.edit(data[field.name])"
        />
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
import { usersStore } from '@/stores/users'
import { Tooltip } from 'frappe-ui'
import { computed } from 'vue'

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

const emit = defineEmits(['update'])

const data = defineModel()

const _fields = computed(() => {
  let all_fields = []
  props.fields?.forEach((field) => {
    let df = field?.all_properties
    if (df?.depends_on) evaluate_depends_on(df.depends_on, field)
    all_fields.push({
      ...field,
      filters: df?.link_filters && JSON.parse(df.link_filters),
      placeholder: field.placeholder || field.label,
    })
  })
  return all_fields
})

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
  background: white;
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
