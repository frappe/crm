<template>
  <div class="flex flex-col gap-5.5">
    <div
      class="flex items-center justify-between gap-2 text-base bg-surface-gray-2 rounded py-2 px-2.5 overflow-x-auto max-w-full"
    >
      <Draggable
        v-if="tabs.length && tabs[tabIndex].label"
        :list="tabs"
        item-key="name"
        class="flex items-center gap-2 w-full overflow-auto py-1 [&::-webkit-scrollbar]:h-0"
        @end="(e) => (tabIndex = e.newIndex)"
      >
        <template #item="{ element: tab, index: i }">
          <div
            :ref="
              (el) => {
                if (el) tabItemRefs[i] = el
              }
            "
            class="flex items-center gap-2 cursor-pointer rounded shrink-0"
            :class="[
              tabIndex == i
                ? 'text-ink-gray-9 bg-surface-white shadow-sm'
                : 'text-ink-gray-5 hover:text-ink-gray-9 hover:bg-surface-white hover:shadow-sm',
              tab.editingLabel ? 'p-1' : 'px-2 py-1',
            ]"
            @click="tabIndex = i"
            @dragenter.prevent="isDragging && (tabIndex = i)"
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
        :label="__('Add Tab')"
        @click="addTab"
      >
        <template #[slotName]>
          <FeatherIcon name="plus" class="h-4" />
        </template>
      </Button>
    </div>
    <div
      v-for="(tab, i) in tabs"
      v-show="tabIndex == i"
      :key="tab.name"
      class="min-h-[34rem]"
    >
      <Draggable
        :list="tab.sections"
        item-key="name"
        :group="
          tab.sections.length === 0
            ? { name: 'sections', put: ['sections', 'columns', 'fields'] }
            : 'sections'
        "
        handle=".section-drag-handle"
        :class="
          tab.sections.length === 0
            ? 'rounded border-2 border-dashed border-outline-gray-2 mb-5.5 p-3'
            : 'flex flex-col gap-5.5'
        "
        @start="isDragging = true"
        @end="isDragging = false"
        @add="(evt) => onFieldDroppedToEmptyTab(tab)"
      >
        <template #item="{ element: section }">
          <div
            v-if="Array.isArray(section.columns)"
            class="section flex flex-col gap-1.5 p-2.5 bg-surface-gray-2 rounded"
          >
            <div class="flex items-center justify-between">
              <div
                class="flex h-7 max-w-fit items-center gap-2 text-base font-medium leading-4 text-ink-gray-9"
              >
                <DragVerticalIcon
                  class="section-drag-handle h-3.5 cursor-grab shrink-0 text-ink-gray-3"
                />
                <div
                  class="flex items-center gap-2 cursor-pointer"
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
                    {{ __(section.label) || __('No Label') }}
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
              </div>
              <div class="flex items-center gap-1.5">
                <span
                  v-if="
                    section.columns.reduce((n, c) => n + c.fields.length, 0) > 0
                  "
                  class="text-xs text-ink-gray-4 bg-surface-gray-3 rounded px-1.5 py-0.5 leading-none"
                >
                  {{ section.columns.reduce((n, c) => n + c.fields.length, 0) }}
                  {{
                    section.columns.reduce((n, c) => n + c.fields.length, 0) ===
                    1
                      ? __('field')
                      : __('fields')
                  }}
                </span>
                <Dropdown :options="getSectionOptions(i, section, tab)">
                  <template #default>
                    <Button variant="ghost">
                      <FeatherIcon name="more-horizontal" class="h-4" />
                    </Button>
                  </template>
                </Dropdown>
              </div>
            </div>
            <Draggable
              class="flex gap-2"
              :list="section.columns"
              group="columns"
              item-key="name"
              @start="isDragging = true"
              @end="isDragging = false"
            >
              <template #item="{ element: column }">
                <div
                  class="flex flex-col gap-1.5 flex-1 p-2 border border-dashed border-outline-gray-2 rounded bg-surface-modal cursor-grab"
                >
                  <Draggable
                    :list="column.fields"
                    group="fields"
                    item-key="fieldname"
                    class="flex flex-col gap-1.5 flex-1 min-h-8.5"
                    handle=".field-drag-handle"
                    @start="isDragging = true"
                    @end="isDragging = false"
                  >
                    <template #item="{ element: field }">
                      <div
                        class="field px-2.5 py-2 border border-outline-gray-2 rounded text-base bg-surface-modal text-ink-gray-8 flex items-center leading-4 justify-between gap-2 cursor-auto"
                      >
                        <div class="flex items-center gap-2 truncate">
                          <DragVerticalIcon
                            class="field-drag-handle h-3.5 cursor-grab"
                          />
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
                    value=""
                    :options="fields"
                    @change="(e) => addField(column, e)"
                  >
                    <template #target="{ togglePopover }">
                      <div class="gap-2 w-full">
                        <Button
                          class="w-full !h-8 !bg-surface-modal"
                          variant="outline"
                          :label="__('Add Field')"
                          iconLeft="plus"
                          @click="togglePopover()"
                        />
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
        <template #footer>
          <div
            v-if="tab.sections.length === 0"
            class="flex items-center justify-center min-h-20 text-sm text-ink-gray-4 pointer-events-none select-none"
          >
            {{ __('Drag a section or a field here to get started') }}
          </div>
        </template>
      </Draggable>
      <div class="mt-5.5">
        <Button
          class="w-full h-8"
          variant="subtle"
          :label="__('Add Section')"
          iconLeft="plus"
          @click="
            tabs[tabIndex].sections.push({
              label: '',
              name: 'section_' + getRandom(),
              opened: true,
              columns: [{ name: 'column_' + getRandom(), fields: [] }],
            })
          "
        />
      </div>
    </div>
  </div>
</template>
<script setup>
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
import DragVerticalIcon from '@/components/Icons/DragVerticalIcon.vue'
import Draggable from 'vuedraggable'
import { getRandom } from '@/utils'
import { getMeta } from '@/stores/meta'
import { globalStore } from '@/stores/global'
import { Dropdown } from 'frappe-ui'
import { ref, computed, watch, nextTick } from 'vue'

const props = defineProps({
  doctype: { type: String, default: 'CRM Lead' },
  onlyRequired: { type: Boolean, default: false },
})

const tabs = defineModel({ type: Array, default: () => [] })

const { $dialog } = globalStore()

const tabIndex = ref(0)
const isDragging = ref(false)
const tabItemRefs = ref([])

watch(tabIndex, (idx) => {
  nextTick(() => {
    tabItemRefs.value[idx]?.scrollIntoView({
      behavior: 'smooth',
      inline: 'nearest',
      block: 'nearest',
    })
  })
})

const slotName = computed(() => {
  if (tabs.value.length == 1 && !tabs.value[0].label) {
    return 'prefix'
  }
  return 'default'
})

const restrictedFieldTypes = [
  'Tab Break',
  'Section Break',
  'Column Break',
  'Signature',
]

const { getFields } = getMeta(props.doctype)

const fields = computed(() => {
  const _fields =
    getFields({ restrictNoValueFields: false, restrictedFieldTypes }) || []
  if (!_fields.length) return []

  let existingFields = []

  tabs.value?.forEach((tab) => {
    tab.sections?.forEach((section) => {
      section.columns?.forEach((column) => {
        existingFields = existingFields.concat(column.fields)
      })
    })
  })

  return _fields
    .filter((field) => {
      return (
        !existingFields.find((f) => f.fieldname === field.fieldname) &&
        (props.onlyRequired ? field.reqd : true)
      )
    })
    .map((field) => {
      return {
        label: field.label,
        value: field.fieldname,
        fieldname: field.fieldname,
        fieldtype: field.fieldtype,
      }
    })
})

function addTab() {
  if (tabs.value.length == 1 && !tabs.value[0].label) {
    tabs.value[0].label = __('New Tab')
    tabIndex.value = 0
    nextTick(() => {
      tabItemRefs.value[0]?.scrollIntoView({
        behavior: 'smooth',
        inline: 'nearest',
        block: 'nearest',
      })
    })
    return
  }

  tabs.value.push({
    label: __('New Tab'),
    name: 'tab_' + getRandom(),
    sections: [],
  })
  tabIndex.value = tabs.value.length ? tabs.value.length - 1 : 0
  nextTick(() => {
    tabItemRefs.value[tabIndex.value]?.scrollIntoView({
      behavior: 'smooth',
      inline: 'nearest',
      block: 'nearest',
    })
  })
}

function addField(column, field) {
  if (!field) return
  column.fields.push(field)
}

function onFieldDroppedToEmptyTab(tab) {
  const droppedItem = tab.sections[0]
  if (!droppedItem) return

  let columns = []

  if (Object.hasOwn(droppedItem, 'fields')) {
    columns = [droppedItem]
  } else if (Object.hasOwn(droppedItem, 'fieldname')) {
    columns = [{ name: 'column_' + getRandom(), fields: [droppedItem] }]
  }

  if (!columns.length) return

  tab.sections.splice(0, 1)
  tab.sections.push({
    label: '',
    name: 'section_' + getRandom(),
    opened: true,
    columns,
  })
}

function getTabOptions(tab) {
  return [
    {
      label: __('Edit'),
      icon: 'edit',
      onClick: () => (tab.editingLabel = true),
    },
    {
      label: __('Remove Tab'),
      icon: 'trash-2',
      onClick: () => {
        if (tabs.value.length == 1) {
          tabs.value[0].label = ''
          return
        }
        $dialog({
          title: __('Remove Tab'),
          message: __(
            'Are you sure you want to remove this tab and all its content?',
          ),
          variant: 'danger',
          actions: [
            {
              label: __('Remove'),
              variant: 'solid',
              theme: 'red',
              onClick: (close) => {
                tabs.value.splice(tabIndex.value, 1)
                tabIndex.value = tabIndex.value ? tabIndex.value - 1 : 0
                close()
              },
            },
          ],
        })
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
          label: section.hideLabel ? __('Show Label') : __('Hide Label'),
          icon: section.hideLabel ? 'eye' : 'eye-off',
          onClick: () => (section.hideLabel = !section.hideLabel),
        },
        {
          label: section.hideBorder ? __('Show Border') : __('Hide Border'),
          icon: 'minus',
          onClick: () => (section.hideBorder = !section.hideBorder),
        },
        {
          label: __('Remove Section'),
          icon: 'trash-2',
          onClick: () => {
            const hasFields = section.columns.some((c) => c.fields.length)
            const doRemove = () =>
              tab.sections.splice(tab.sections.indexOf(section), 1)
            if (hasFields) {
              $dialog({
                title: __('Remove Section'),
                message: __(
                  'This section contains fields. Are you sure you want to remove it?',
                ),
                variant: 'danger',
                actions: [
                  {
                    label: __('Remove'),
                    variant: 'solid',
                    theme: 'red',
                    onClick: (close) => {
                      doRemove()
                      close()
                    },
                  },
                ],
              })
            } else {
              doRemove()
            }
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
          label: __('Move to Previous Tab'),
          icon: 'corner-up-left',
          onClick: () => {
            let previousTab = tabs.value[tabIndex.value - 1]
            previousTab.sections.push(section)
            tabs.value[tabIndex.value].sections.splice(
              tabs.value[tabIndex.value].sections.indexOf(section),
              1,
            )
            tabIndex.value -= 1
          },
          condition: () => tabs.value[tabIndex.value - 1],
        },
        {
          label: __('Move to Next Tab'),
          icon: 'corner-up-right',
          onClick: () => {
            let nextTab = tabs.value[tabIndex.value + 1]
            nextTab.sections.push(section)
            tabs.value[tabIndex.value].sections.splice(
              tabs.value[tabIndex.value].sections.indexOf(section),
              1,
            )
            tabIndex.value += 1
          },
          condition: () => tabs.value[tabIndex.value + 1],
        },
      ],
    },
    {
      group: __('Column'),
      items: [
        {
          label: __('Add Column'),
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
          label: __('Remove Last Column'),
          icon: 'trash-2',
          onClick: () => {
            const doRemove = () => section.columns.pop()
            if (column.fields.length) {
              $dialog({
                title: __('Remove Last Column'),
                message: __(
                  'This column contains fields. Are you sure you want to remove it?',
                ),
                variant: 'danger',
                actions: [
                  {
                    label: __('Remove'),
                    variant: 'solid',
                    theme: 'red',
                    onClick: (close) => {
                      doRemove()
                      close()
                    },
                  },
                ],
              })
            } else {
              doRemove()
            }
          },
          condition: () => section.columns.length > 1,
        },
        {
          label: __('Remove Last Column (move fields to previous)'),
          icon: 'trash-2',
          onClick: () => {
            let previousColumn = section.columns[section.columns.length - 2]
            previousColumn.fields = previousColumn.fields.concat(column.fields)
            section.columns.pop()
          },
          condition: () => section.columns.length > 1 && column.fields.length,
        },
        {
          label: __('Move Last Column to Next Section'),
          icon: 'corner-up-right',
          onClick: () => {
            let nextSection = tab.sections[i + 1]
            nextSection.columns.push(column)
            section.columns.pop()
          },
          condition: () => tab.sections[i + 1],
        },
        {
          label: __('Move Last Column to Previous Section'),
          icon: 'corner-up-left',
          onClick: () => {
            let previousSection = tab.sections[i - 1]
            previousSection.columns.push(column)
            section.columns.pop()
          },
          condition: () => tab.sections[i - 1],
        },
        {
          label: __('Move Last Column to Previous Tab'),
          icon: 'corner-up-left',
          onClick: () => {
            let targetTab = tabs.value[tabIndex.value - 1]
            if (!targetTab.sections.length) {
              targetTab.sections.push({
                label: '',
                name: 'section_' + getRandom(),
                opened: true,
                columns: [],
              })
            }
            targetTab.sections[targetTab.sections.length - 1].columns.push(
              column,
            )
            section.columns.pop()
          },
          condition: () => tabs.value[tabIndex.value - 1],
        },
        {
          label: __('Move Last Column to Next Tab'),
          icon: 'corner-up-right',
          onClick: () => {
            let targetTab = tabs.value[tabIndex.value + 1]
            if (!targetTab.sections.length) {
              targetTab.sections.push({
                label: '',
                name: 'section_' + getRandom(),
                opened: true,
                columns: [],
              })
            }
            targetTab.sections[targetTab.sections.length - 1].columns.push(
              column,
            )
            section.columns.pop()
          },
          condition: () => tabs.value[tabIndex.value + 1],
        },
      ],
    },
  ]
}
</script>
