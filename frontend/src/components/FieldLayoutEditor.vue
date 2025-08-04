<template>
  <div class="flex flex-col gap-5.5">
    <div
      class="flex items-center gap-2 text-base bg-surface-gray-2 rounded py-2 px-2.5"
    >
      <Draggable
        v-if="tabs.length && tabs[tabIndex].label"
        :list="tabs"
        item-key="name"
        class="flex items-center gap-2"
        @end="(e) => (tabIndex = e.newIndex)"
      >
        <template #item="{ element: tab, index: i }">
          <div
            class="flex items-center gap-2 cursor-pointer rounded"
            :class="[
              tabIndex == i
                ? 'text-ink-gray-9 bg-surface-white shadow-sm'
                : 'text-ink-gray-5 hover:text-ink-gray-9 hover:bg-surface-white hover:shadow-sm',
              tab.editingLabel ? 'p-1' : 'px-2 py-1',
            ]"
            @click="tabIndex = i"
          >
            <div @dblclick="() => (tab.editingLabel = true)">
              <div v-if="!tab.editingLabel" class="flex items-center gap-2">
                {{ __(tab.label) || __('Untitled') }}
              </div>
              <div v-else class="flex gap-1 items-center">
                <Input
                  v-model="tab.label"
                  @keydown.enter="tab.editingLabel = false"
                  @blur="tab.editingLabel = false"
                  @click.stop
                />
                <Button
                  v-if="tab.editingLabel"
                  icon="check"
                  variant="ghost"
                  @click="tab.editingLabel = false"
                />
              </div>
            </div>
            <Dropdown
              v-if="tab.label && tabIndex == i"
              :options="getTabOptions(tab)"
              class="!h-4"
              @click.stop
            >
              <template #default>
                <Button variant="ghost" class="!p-1 !h-4">
                  <FeatherIcon name="more-horizontal" class="h-4" />
                </Button>
              </template>
            </Dropdown>
          </div>
        </template>
      </Draggable>
      <Button
        variant="ghost"
        class="!h-6.5 !text-ink-gray-5 hover:!text-ink-gray-9"
        @click="addTab"
        :label="__('Add Tab')"
      >
        <template v-slot:[slotName]>
          <FeatherIcon name="plus" class="h-4" />
        </template>
      </Button>
    </div>
    <div v-show="tabIndex == i" v-for="(tab, i) in tabs" :key="tab.name">
      <Draggable
        :list="tab.sections"
        item-key="name"
        class="flex flex-col gap-5.5"
      >
        <template #item="{ element: section, index: i }">
          <div
            class="section flex flex-col gap-1.5 p-2.5 bg-surface-gray-2 rounded cursor-grab"
          >
            <div class="flex items-center justify-between">
              <div
                class="flex h-7 max-w-fit cursor-pointer items-center gap-2 text-base font-medium leading-4 text-ink-gray-9"
                @dblclick="() => (section.editingLabel = true)"
              >
                <div
                  v-if="!section.editingLabel"
                  class="flex items-center gap-2"
                  :class="{
                    'text-ink-gray-3': section.hideLabel || !section.label,
                    italic: !section.label,
                  }"
                >
                  {{ __(section.label) || __('No label') }}
                  <FeatherIcon
                    v-if="section.collapsible"
                    name="chevron-down"
                    class="h-4 transition-all duration-300 ease-in-out"
                  />
                </div>
                <div v-else class="flex gap-2 items-center">
                  <Input
                    v-model="section.label"
                    @keydown.enter="section.editingLabel = false"
                    @blur="section.editingLabel = false"
                    @click.stop
                  />
                  <Button
                    v-if="section.editingLabel"
                    icon="check"
                    variant="ghost"
                    @click="section.editingLabel = false"
                  />
                </div>
              </div>
              <Dropdown :options="getSectionOptions(i, section, tab)">
                <template #default>
                  <Button variant="ghost">
                    <FeatherIcon name="more-horizontal" class="h-4" />
                  </Button>
                </template>
              </Dropdown>
            </div>
            <Draggable
              class="flex gap-2"
              :list="section.columns"
              group="columns"
              item-key="name"
            >
              <template #item="{ element: column }">
                <div
                  class="flex flex-col gap-1.5 flex-1 p-2 border border-dashed border-outline-gray-2 rounded bg-surface-modal cursor-grab"
                >
                  <Draggable
                    :list="column.fields"
                    group="fields"
                    item-key="fieldname"
                    class="flex flex-col gap-1.5"
                    handle=".cursor-grab"
                  >
                    <template #item="{ element: field }">
                      <div
                        class="field px-2.5 py-2 border border-outline-gray-2 rounded text-base bg-surface-modal text-ink-gray-8 flex items-center leading-4 justify-between gap-2"
                      >
                        <div class="flex items-center gap-2 truncate">
                          <DragVerticalIcon class="h-3.5 cursor-grab" />
                          <div class="truncate">{{ field.label }}</div>
                        </div>
                        <Button
                          variant="ghost"
                          class="!size-4 rounded-sm"
                          icon="x"
                          @click="
                            column.fields.splice(
                              column.fields.indexOf(field),
                              1,
                            )
                          "
                        />
                      </div>
                    </template>
                  </Draggable>
                  <Autocomplete
                    v-if="fields.data"
                    value=""
                    :options="fields.data"
                    @change="(e) => addField(column, e)"
                  >
                    <template #target="{ togglePopover }">
                      <div class="gap-2 w-full">
                        <Button
                          class="w-full !h-8 !bg-surface-modal"
                          variant="outline"
                          @click="togglePopover()"
                          :label="__('Add Field')"
                        >
                          <template #prefix>
                            <FeatherIcon name="plus" class="h-4" />
                          </template>
                        </Button>
                      </div>
                    </template>
                    <template #item-label="{ option }">
                      <div class="flex flex-col gap-1 text-ink-gray-9">
                        <div>{{ option.label }}</div>
                        <div class="text-ink-gray-4 text-sm">
                          {{ `${option.fieldname} - ${option.fieldtype}` }}
                        </div>
                      </div>
                    </template>
                  </Autocomplete>
                </div>
              </template>
            </Draggable>
          </div>
        </template>
      </Draggable>
      <div class="mt-5.5">
        <Button
          class="w-full h-8"
          variant="subtle"
          :label="__('Add Section')"
          @click="
            tabs[tabIndex].sections.push({
              label: __('New Section'),
              name: 'section_' + getRandom(),
              opened: true,
              columns: [{ name: 'column_' + getRandom(), fields: [] }],
            })
          "
        >
          <template #prefix>
            <FeatherIcon name="plus" class="h-4" />
          </template>
        </Button>
      </div>
    </div>
  </div>
</template>
<script setup>
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
import DragVerticalIcon from '@/components/Icons/DragVerticalIcon.vue'
import Draggable from 'vuedraggable'
import { getRandom } from '@/utils'
import { Dropdown, createResource } from 'frappe-ui'
import { ref, computed, watch } from 'vue'

const props = defineProps({
  tabs: Object,
  doctype: String,
  onlyRequired: {
    type: Boolean,
    default: false,
  },
})

const tabIndex = ref(0)
const slotName = computed(() => {
  if (props.tabs.length == 1 && !props.tabs[0].label) {
    return 'prefix'
  }
  return 'default'
})

const restrictedFieldTypes = [
  'Geolocation',
  'Attach',
  'Attach Image',
  'HTML',
  'Signature',
]

const params = computed(() => {
  return {
    doctype: props.doctype,
    restricted_fieldtypes: restrictedFieldTypes,
    as_array: true,
    only_required: props.onlyRequired,
  }
})

const fields = createResource({
  url: 'crm.api.doc.get_fields_meta',
  params: params.value,
  cache: ['fieldsMeta', props.doctype],
  auto: true,
  transform: (data) => {
    let restrictedFields = [
      'name',
      'owner',
      'creation',
      'modified',
      'modified_by',
      'docstatus',
      '_comments',
      '_user_tags',
      '_assign',
      '_liked_by',
    ]
    let existingFields = []

    props.tabs?.forEach((tab) => {
      tab.sections?.forEach((section) => {
        section.columns?.forEach((column) => {
          existingFields = existingFields.concat(column.fields)
        })
      })
    })

    return data.filter((field) => {
      return (
        !existingFields.find((f) => f.fieldname === field.fieldname) &&
        !restrictedFields.includes(field.fieldname)
      )
    })
  },
})

function addTab() {
  if (props.tabs.length == 1 && !props.tabs[0].label) {
    props.tabs[0].label = __('New Tab')
    return
  }

  props.tabs.push({
    label: __('New Tab'),
    name: 'tab_' + getRandom(),
    sections: [],
  })
  tabIndex.value = props.tabs.length ? props.tabs.length - 1 : 0
}

function addField(column, field) {
  if (!field) return
  column.fields.push(field)
}

function getTabOptions(tab) {
  return [
    {
      label: __('Edit'),
      icon: 'edit',
      onClick: () => (tab.editingLabel = true),
    },
    {
      label: __('Remove tab'),
      icon: 'trash-2',
      onClick: () => {
        if (props.tabs.length == 1) {
          props.tabs[0].label = ''
          return
        }
        props.tabs.splice(tabIndex.value, 1)
        tabIndex.value = tabIndex.value ? tabIndex.value - 1 : 0
      },
    },
  ]
}

function getSectionOptions(i, section, tab) {
  let column = section.columns[section.columns.length - 1]
  return [
    {
      group: __('Section'),
      items: [
        {
          label: __('Edit'),
          icon: 'edit',
          onClick: () => (section.editingLabel = true),
        },
        {
          label: section.collapsible ? __('Uncollapsible') : __('Collapsible'),
          icon: section.collapsible ? 'chevron-up' : 'chevron-down',
          onClick: () => (section.collapsible = !section.collapsible),
        },
        {
          label: section.hideLabel ? __('Show label') : __('Hide label'),
          icon: section.hideLabel ? 'eye' : 'eye-off',
          onClick: () => (section.hideLabel = !section.hideLabel),
        },
        {
          label: section.hideBorder ? __('Show border') : __('Hide border'),
          icon: 'minus',
          onClick: () => (section.hideBorder = !section.hideBorder),
        },
        {
          label: __('Remove section'),
          icon: 'trash-2',
          onClick: () => {
            tab.sections.splice(tab.sections.indexOf(section), 1)
          },
          condition: () => section.editable !== false,
        },
        {
          label: __('Remove and move columns to {0} section', [
            i == 0 ? __('next') : __('previous'),
          ]),
          icon: 'trash-2',
          onClick: () => {
            let targetSection = tab.sections[i == 0 ? i + 1 : i - 1]
            if (i == 0) {
              targetSection.columns = section.columns.concat(
                targetSection.columns,
              )
            } else {
              targetSection.columns = targetSection.columns.concat(
                section.columns,
              )
            }
            tab.sections.splice(tab.sections.indexOf(section), 1)
          },
          condition: () => section.editable !== false && section.columns.length,
        },
        {
          label: __('Move to previous tab'),
          icon: 'corner-up-left',
          onClick: () => {
            let previousTab = props.tabs[tabIndex.value - 1]
            previousTab.sections.push(section)
            props.tabs[tabIndex.value].sections.splice(
              props.tabs[tabIndex.value].sections.indexOf(section),
              1,
            )
            tabIndex.value -= 1
          },
          condition: () => props.tabs[tabIndex.value - 1],
        },
        {
          label: __('Move to next tab'),
          icon: 'corner-up-right',
          onClick: () => {
            let nextTab = props.tabs[tabIndex.value + 1]
            nextTab.sections.push(section)
            props.tabs[tabIndex.value].sections.splice(
              props.tabs[tabIndex.value].sections.indexOf(section),
              1,
            )
            tabIndex.value += 1
          },
          condition: () => props.tabs[tabIndex.value + 1],
        },
      ],
    },
    {
      group: __('Column'),
      items: [
        {
          label: __('Add column'),
          icon: 'columns',
          onClick: () => {
            section.columns.push({
              label: '',
              name: 'column_' + getRandom(),
              fields: [],
            })
          },
          condition: () => section.columns.length < 4,
        },
        {
          label: __('Remove column'),
          icon: 'trash-2',
          onClick: () => section.columns.pop(),
          condition: () => section.columns.length > 1,
        },
        {
          label: __('Remove and move fields to previous column'),
          icon: 'trash-2',
          onClick: () => {
            let previousColumn = section.columns[section.columns.length - 2]
            previousColumn.fields = previousColumn.fields.concat(column.fields)
            section.columns.pop()
          },
          condition: () => section.columns.length > 1 && column.fields.length,
        },
        {
          label: __('Move to next section'),
          icon: 'corner-up-right',
          onClick: () => {
            let nextSection = tab.sections[i + 1]
            nextSection.columns.push(column)
            section.columns.pop()
          },
          condition: () => tab.sections[i + 1],
        },
        {
          label: __('Move to previous section'),
          icon: 'corner-up-left',
          onClick: () => {
            let previousSection = tab.sections[i - 1]
            previousSection.columns.push(column)
            section.columns.pop()
          },
          condition: () => tab.sections[i - 1],
        },
      ],
    },
  ]
}

watch(
  () => props.doctype,
  () => fields.fetch(params.value),
  { immediate: true },
)
</script>
