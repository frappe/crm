<template>
  <div class="sections flex flex-col overflow-y-auto">
    <template v-for="(section, i) in _sections" :key="section.name">
      <div v-if="section.visible" class="section flex flex-col">
        <div
          v-if="i !== firstVisibleIndex()"
          class="w-full section-border h-px border-t"
        />
        <div class="p-3">
          <Section
            labelClass="px-2 font-semibold"
            :label="section.label"
            :hideLabel="!section.label"
            :opened="section.opened"
          >
            <template v-if="!preview" #actions>
              <div v-if="section.name == 'contacts_section'" class="pr-2">
                <Link
                  value=""
                  doctype="Contact"
                  @change="(e) => addContact(e)"
                  :onCreate="
                    (value, close) => {
                      _contact = {
                        first_name: value,
                        company_name: deal.data.organization,
                      }
                      showContactModal = true
                      close()
                    }
                  "
                >
                  <template #target="{ togglePopover }">
                    <Button
                      class="h-7 px-3"
                      variant="ghost"
                      icon="plus"
                      @click="togglePopover()"
                    />
                  </template>
                </Link>
              </div>
              <Button
                v-else-if="section.showEditButton"
                variant="ghost"
                class="w-7 mr-2"
                @click="showSidePanelModal = true"
              >
                <EditIcon class="h-4 w-4" />
              </Button>
            </template>
            <slot v-bind="{ section }">
              <FadedScrollableDiv
                v-if="section.columns?.[0].fields.length"
                class="column flex flex-col gap-1.5 overflow-y-auto"
              >
                <template
                  v-for="field in section.columns[0].fields || []"
                  :key="field.name"
                >
                  <div
                    v-if="field.visible"
                    class="field flex items-center gap-2 px-3 leading-5 first:mt-3"
                  >
                    <Tooltip :text="__(field.label)" :hoverDelay="1">
                      <div
                        class="w-[35%] min-w-20 shrink-0 truncate text-sm text-ink-gray-5"
                      >
                        <span>{{ __(field.label) }}</span>
                        <span class="text-ink-red-3">{{
                          field.reqd ? ' *' : ''
                        }}</span>
                      </div>
                    </Tooltip>
                    <div class="flex items-center justify-between w-[65%]">
                      <div
                        class="grid min-h-[28px] flex-1 items-center overflow-hidden text-base"
                      >
                        <div
                          v-if="
                            field.read_only &&
                            !['checkbox', 'dropdown'].includes(field.type)
                          "
                          class="flex h-7 cursor-pointer items-center px-2 py-1 text-ink-gray-5"
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
                                    <div
                                      class="p-1.5 px-7 text-base text-ink-gray-4"
                                    >
                                      {{
                                        __('No {0} Available', [field.label])
                                      }}
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
                          @change.stop="
                            emit('update', field.name, $event.target.checked)
                          "
                          :disabled="Boolean(field.read_only)"
                        />
                        <FormControl
                          v-else-if="
                            [
                              'email',
                              'number',
                              'password',
                              'textarea',
                            ].includes(field.type)
                          "
                          class="form-control"
                          :type="field.type"
                          :value="data[field.name]"
                          :placeholder="field.placeholder"
                          :debounce="500"
                          @change.stop="
                            emit('update', field.name, $event.target.value)
                          "
                        />
                        <FormControl
                          v-else-if="field.type === 'select'"
                          class="form-control cursor-pointer [&_select]:cursor-pointer truncate"
                          type="select"
                          v-model="data[field.name]"
                          :options="field.options"
                          :placeholder="field.placeholder"
                          @change.stop="
                            emit('update', field.name, $event.target.value)
                          "
                        />
                        <Link
                          v-else-if="
                            ['lead_owner', 'deal_owner'].includes(field.name)
                          "
                          class="form-control"
                          :value="
                            data[field.name] &&
                            getUser(data[field.name]).full_name
                          "
                          doctype="User"
                          :filters="field.filters"
                          @change="(data) => emit('update', field.name, data)"
                          :placeholder="'Select' + ' ' + field.label + '...'"
                          :hideMe="true"
                        >
                          <template v-if="data[field.name]" #prefix>
                            <UserAvatar
                              class="mr-1.5"
                              :user="data[field.name]"
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
                          v-else-if="field.type === 'link'"
                          class="form-control select-text"
                          :value="data[field.name]"
                          :doctype="field.doctype"
                          :filters="field.filters"
                          :placeholder="field.placeholder"
                          @change="(data) => emit('update', field.name, data)"
                          :onCreate="field.create"
                        />
                        <div
                          v-else-if="field.type === 'datetime'"
                          class="form-control"
                        >
                          <DateTimePicker
                            icon-left=""
                            :value="data[field.name]"
                            :formatter="
                              (date) => getFormat(date, '', true, true)
                            "
                            :placeholder="field.placeholder"
                            placement="left-start"
                            @change="(data) => emit('update', field.name, data)"
                          />
                        </div>
                        <div
                          v-else-if="field.type === 'date'"
                          class="form-control"
                        >
                          <DatePicker
                            icon-left=""
                            :value="data[field.name]"
                            :formatter="(date) => getFormat(date, '', true)"
                            :placeholder="field.placeholder"
                            placement="left-start"
                            @change="(data) => emit('update', field.name, data)"
                          />
                        </div>
                        <FormControl
                          v-else-if="field.type === 'percent'"
                          class="form-control"
                          type="text"
                          :value="getFormattedPercent(field.name, data)"
                          :placeholder="field.placeholder"
                          :debounce="500"
                          @change.stop="
                            emit('update', field.name, flt($event.target.value))
                          "
                        />
                        <FormControl
                          v-else-if="field.type === 'float'"
                          class="form-control"
                          type="text"
                          :value="getFormattedFloat(field.name, data)"
                          :placeholder="field.placeholder"
                          :debounce="500"
                          @change.stop="
                            emit('update', field.name, flt($event.target.value))
                          "
                        />
                        <FormControl
                          v-else-if="field.type === 'currency'"
                          class="form-control"
                          type="text"
                          :value="getFormattedCurrency(field.name, data)"
                          :placeholder="field.placeholder"
                          :debounce="500"
                          @change.stop="
                            emit('update', field.name, flt($event.target.value))
                          "
                        />
                        <FormControl
                          v-else
                          class="form-control"
                          type="text"
                          :value="data[field.name]"
                          :placeholder="field.placeholder"
                          :debounce="500"
                          @change.stop="
                            emit('update', field.name, $event.target.value)
                          "
                        />
                      </div>
                      <div class="ml-1">
                        <ArrowUpRightIcon
                          v-if="
                            field.type === 'link' &&
                            field.link &&
                            data[field.name]
                          "
                          class="h-4 w-4 shrink-0 cursor-pointer text-ink-gray-5 hover:text-ink-gray-8"
                          @click.stop="field.link(data[field.name])"
                        />
                        <EditIcon
                          v-if="
                            field.type === 'link' &&
                            field.edit &&
                            data[field.name]
                          "
                          class="size-3.5 shrink-0 cursor-pointer text-ink-gray-5 hover:text-ink-gray-8"
                          @click.stop="field.edit(data[field.name])"
                        />
                      </div>
                    </div>
                  </div>
                </template>
              </FadedScrollableDiv>
            </slot>
          </Section>
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
import Section from '@/components/Section.vue'
import NestedPopover from '@/components/NestedPopover.vue'
import DropdownItem from '@/components/DropdownItem.vue'
import FadedScrollableDiv from '@/components/FadedScrollableDiv.vue'
import ArrowUpRightIcon from '@/components/Icons/ArrowUpRightIcon.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import Link from '@/components/Controls/Link.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import SidePanelModal from '@/components/Modals/SidePanelModal.vue'
import { getMeta } from '@/stores/meta'
import { usersStore } from '@/stores/users'
import { getFormat, evaluateDependsOnValue } from '@/utils'
import { flt } from '@/utils/numberFormat.js'
import { Tooltip, DateTimePicker, DatePicker } from 'frappe-ui'
import { ref, computed } from 'vue'

const props = defineProps({
  sections: {
    type: Object,
  },
  doctype: {
    type: String,
    default: 'CRM Lead',
  },
  preview: {
    type: Boolean,
    default: false,
  },
})

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
  getMeta(props.doctype)
const { isManager, getUser } = usersStore()

const emit = defineEmits(['update', 'reload'])

const data = defineModel()
const showSidePanelModal = ref(false)

const _sections = computed(() => {
  if (!props.sections?.length) return []
  let editButtonAdded = false
  return props.sections.map((section) => {
    let isContactSection = section.name == 'contacts_section'

    if (section.columns?.length) {
      section.columns[0].fields = section.columns[0].fields.map((field) => {
        let df = field?.all_properties || {}
        let _field = {
          ...field,
          depends_on: df.depends_on,
          mandatory_depends_on: df.mandatory_depends_on,
          display_via_depends_on: evaluateDependsOnValue(
            df.depends_on,
            data.value,
          ),
          mandatory_via_depends_on: evaluateDependsOnValue(
            df.mandatory_depends_on,
            data.value,
          ),
          filters: df.link_filters && JSON.parse(df.link_filters),
          placeholder: field.placeholder || field.label,
        }
        _field.visible = isFieldVisible(_field)
        return _field
      })
    }

    section.showEditButton = !(
      !isManager() ||
      isContactSection ||
      editButtonAdded
    )
    if (section.showEditButton) {
      editButtonAdded = true
    }

    section.visible =
      isContactSection ||
      section.columns?.[0].fields.filter((f) => f.visible).length

    return section
  })
})

function isFieldVisible(field) {
  return (
    (field.type == 'Check' ||
      (field.read_only && data.value[field.name]) ||
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
