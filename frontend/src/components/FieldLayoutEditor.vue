<template>
  <div class="flex flex-col gap-5.5">
    <div
      class="flex justify-between items-center gap-1 text-base bg-surface-gray-2 rounded py-2 px-2.5"
    >
      <div class="flex items-center gap-1">
        <Draggable
          v-if="tabs.length && !tabs[tabIndex].no_tabs"
          :list="tabs"
          item-key="label"
          class="flex items-center gap-1"
          @end="(e) => (tabIndex = e.newIndex)"
        >
          <template #item="{ element: tab, index: i }">
            <div
              class="cursor-pointer rounded"
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
            </div>
          </template>
        </Draggable>
        <Button
          variant="ghost"
          class="!h-6.5 !text-ink-gray-5 hover:!text-ink-gray-9"
          @click="addTab"
          :label="__('Add Tab')"
        >
          <template #prefix>
            <FeatherIcon name="plus" class="h-4" />
          </template>
        </Button>
      </div>
      <Dropdown
        v-if="tabs.length && !tabs[tabIndex].no_tabs"
        :options="getTabOptions(tabs[tabIndex])"
      >
        <template #default>
          <Button variant="ghost">
            <FeatherIcon name="more-horizontal" class="h-4" />
          </Button>
        </template>
      </Dropdown>
    </div>
    <div v-show="tabIndex == i" v-for="(tab, i) in tabs" :key="tab.label">
      <Draggable
        :list="tab.sections"
        item-key="label"
        class="flex flex-col gap-5.5"
      >
        <template #item="{ element: section }">
          <div class="flex flex-col gap-1.5 p-2.5 bg-surface-gray-2 rounded">
            <div class="flex items-center justify-between">
              <div
                class="flex h-7 max-w-fit cursor-pointer items-center gap-2 text-base font-medium leading-4 text-ink-gray-9"
                @dblclick="() => (section.editingLabel = true)"
              >
                <div
                  v-if="!section.editingLabel"
                  class="flex items-center gap-2"
                  :class="{ 'text-ink-gray-3': section.hideLabel }"
                >
                  {{ __(section.label) || __('Untitled') }}
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
              <Dropdown :options="getSectionOptions(section)">
                <template #default>
                  <Button variant="ghost">
                    <FeatherIcon name="more-horizontal" class="h-4" />
                  </Button>
                </template>
              </Dropdown>
            </div>
            <Draggable
              :list="section.fields"
              group="fields"
              item-key="label"
              class="grid gap-1.5"
              :class="gridClass(section.columns)"
              handle=".cursor-grab"
            >
              <template #item="{ element: field }">
                <div
                  class="px-2.5 py-2 border border-outline-gray-2 rounded text-base bg-surface-modal text-ink-gray-8 flex items-center leading-4 justify-between gap-2"
                >
                  <div class="flex items-center gap-2">
                    <DragVerticalIcon class="h-3.5 cursor-grab" />
                    <div>{{ field.label }}</div>
                  </div>
                  <Button
                    variant="ghost"
                    class="!size-4 rounded-sm"
                    icon="x"
                    @click="
                      section.fields.splice(section.fields.indexOf(field), 1)
                    "
                  />
                </div>
              </template>
            </Draggable>
            <Autocomplete
              v-if="fields.data"
              value=""
              :options="fields.data"
              @change="(e) => addField(section, e)"
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
      <div class="mt-5.5">
        <Button
          class="w-full h-8"
          variant="subtle"
          :label="__('Add Section')"
          @click="
            tabs[tabIndex].sections.push({
              label: __('New Section'),
              opened: true,
              fields: [],
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
import { Dropdown, createResource } from 'frappe-ui'
import { ref, computed, watch } from 'vue'

const props = defineProps({
  tabs: Object,
  doctype: String,
})

const tabIndex = ref(0)

const restrictedFieldTypes = [
  'Table',
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
  }
})

const fields = createResource({
  url: 'crm.api.doc.get_fields_meta',
  params: params.value,
  cache: ['fieldsMeta', props.doctype],
  auto: true,
})

function addTab() {
  if (props.tabs.length == 1 && props.tabs[0].no_tabs) {
    delete props.tabs[0].no_tabs
    return
  }
  props.tabs.push({ label: __('New Tab'), sections: [] })
  tabIndex.value = props.tabs.length ? props.tabs.length - 1 : 0
}

function addField(section, field) {
  if (!field) return
  section.fields.push(field)
}

function getTabOptions(tab) {
  return [
    {
      label: 'Edit',
      icon: 'edit',
      onClick: () => (tab.editingLabel = true),
    },
    {
      label: 'Remove tab',
      icon: 'trash-2',
      onClick: () => {
        if (props.tabs.length == 1) {
          props.tabs[0].no_tabs = true
          return
        }
        props.tabs.splice(tabIndex.value, 1)
        tabIndex.value = tabIndex.value ? tabIndex.value - 1 : 0
      },
    },
  ]
}

function getSectionOptions(section) {
  return [
    {
      label: 'Edit',
      icon: 'edit',
      onClick: () => (section.editingLabel = true),
      condition: () => section.editable !== false,
    },
    {
      label: section.collapsible ? 'Uncollapsible' : 'Collapsible',
      icon: section.collapsible ? 'chevron-up' : 'chevron-down',
      onClick: () => (section.collapsible = !section.collapsible),
    },
    {
      label: section.hideLabel ? 'Show label' : 'Hide label',
      icon: section.hideLabel ? 'eye' : 'eye-off',
      onClick: () => (section.hideLabel = !section.hideLabel),
    },
    {
      label: section.hideBorder ? 'Show border' : 'Hide border',
      icon: 'minus',
      onClick: () => (section.hideBorder = !section.hideBorder),
    },
    {
      label: 'Add column',
      icon: 'columns',
      onClick: () =>
        (section.columns = section.columns ? section.columns + 1 : 4),
      condition: () => !section.columns || section.columns < 4,
    },
    {
      label: 'Remove column',
      icon: 'columns',
      onClick: () =>
        (section.columns = section.columns ? section.columns - 1 : 2),
      condition: () => !section.columns || section.columns > 1,
    },
    {
      label: 'Remove section',
      icon: 'trash-2',
      onClick: () => {
        let currentTab = props.tabs[tabIndex.value]
        currentTab.sections.splice(currentTab.sections.indexOf(section), 1)
      },
      condition: () => section.editable !== false,
    },
    {
      label: 'Move to previous tab',
      icon: 'trash-2',
      onClick: () => {
        let previousTab = props.tabs[tabIndex.value - 1]
        previousTab.sections.push(section)
        props.tabs[tabIndex.value].sections.splice(
          props.tabs[tabIndex.value].sections.indexOf(section),
          1,
        )
        tabIndex.value -= 1
      },
      condition: () =>
        section.editable !== false && props.tabs[tabIndex.value - 1],
    },
    {
      label: 'Move to next tab',
      icon: 'trash-2',
      onClick: () => {
        let nextTab = props.tabs[tabIndex.value + 1]
        nextTab.sections.push(section)
        props.tabs[tabIndex.value].sections.splice(
          props.tabs[tabIndex.value].sections.indexOf(section),
          1,
        )
        tabIndex.value += 1
      },
      condition: () =>
        section.editable !== false && props.tabs[tabIndex.value + 1],
    },
  ]
}

function gridClass(columns) {
  columns = columns || 3
  let griColsMap = {
    1: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-1',
    2: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-2',
    3: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4',
  }
  return griColsMap[columns]
}

watch(
  () => props.doctype,
  () => fields.fetch(params.value),
  { immediate: true },
)
</script>
