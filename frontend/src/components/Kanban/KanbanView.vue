<template>
  <Draggable
    v-if="columns"
    :list="columns"
    item-key="column"
    @end="updateColumn"
    class="flex sm:mx-2.5 mx-2 pb-3.5 overflow-x-auto h-full"
  >
    <template #item="{ element: column }">
      <div
        v-if="!column.delete"
        class="flex flex-col gap-2.5 min-w-72 w-72 hover:bg-gray-100 rounded-lg p-2.5"
      >
        <div class="flex gap-2 items-center group justify-between">
          <div class="flex items-center text-base">
            <NestedPopover>
              <template #target>
                <Button variant="ghost" size="sm" class="hover:!bg-gray-100">
                  <IndicatorIcon
                    :class="colorClasses(column.column.color, true)"
                  />
                </Button>
              </template>
              <template #body="{ close }">
                <div
                  class="flex flex-col gap-3 px-3 py-2.5 rounded-lg border border-gray-100 bg-white shadow-xl"
                >
                  <div class="flex gap-1">
                    <Button
                      :class="colorClasses(color)"
                      variant="ghost"
                      v-for="color in colors"
                      :key="color"
                      @click="() => (column.column.color = color)"
                    >
                      <IndicatorIcon />
                    </Button>
                  </div>
                  <div class="flex flex-row-reverse">
                    <Button
                      variant="solid"
                      :label="__('Apply')"
                      @click="updateColumn"
                    />
                  </div>
                </div>
              </template>
            </NestedPopover>
            <div>{{ column.column.name }}</div>
          </div>
          <div class="flex">
            <Dropdown :options="actions(column)">
              <template #default>
                <Button
                  class="hidden group-hover:flex"
                  icon="more-horizontal"
                  variant="ghost"
                />
              </template>
            </Dropdown>
            <Button
              icon="plus"
              variant="ghost"
              @click="options.onNewClick(column)"
            />
          </div>
        </div>
        <div class="overflow-y-auto flex flex-col gap-2">
          <Draggable
            :list="column.data"
            group="fields"
            item-key="name"
            class="flex flex-col gap-3.5"
            @end="updateColumn"
            :data-column="column.column.name"
          >
            <template #item="{ element: fields }">
              <component
                :is="options.getRoute ? 'router-link' : 'div'"
                class="pt-3 px-3.5 pb-2.5 rounded-lg border bg-white text-base flex flex-col"
                :data-name="fields.name"
                v-bind="{
                  to: options.getRoute ? options.getRoute(fields) : undefined,
                  onClick: options.onClick
                    ? () => options.onClick(fields)
                    : undefined,
                }"
              >
                <slot
                  name="title"
                  v-bind="{ fields, titleField, itemName: fields.name }"
                >
                  <div class="h-5 flex items-center">
                    <div v-if="fields[titleField]">
                      {{ fields[titleField] }}
                    </div>
                    <div class="text-gray-500" v-else>{{ __('No Title') }}</div>
                  </div>
                </slot>
                <div class="border-b h-px my-2.5" />

                <div class="flex flex-col gap-3.5">
                  <template v-for="value in column.fields" :key="value">
                    <slot
                      name="fields"
                      v-bind="{
                        fields,
                        fieldName: value,
                        itemName: fields.name,
                      }"
                    >
                      <div v-if="fields[value]" class="truncate">
                        {{ fields[value] }}
                      </div>
                    </slot>
                  </template>
                </div>
                <div class="border-b h-px mt-2.5 mb-2" />
                <slot name="actions" v-bind="{ itemName: fields.name }">
                  <div class="flex gap-2 items-center justify-between">
                    <div></div>
                    <Button icon="plus" variant="ghost" @click.stop.prevent />
                  </div>
                </slot>
              </component>
            </template>
          </Draggable>
          <div
            v-if="column.column.count < column.column.all_count"
            class="flex items-center justify-center"
          >
            <Button
              :label="__('Load More')"
              @click="emit('loadMore', column.column.name)"
            />
          </div>
        </div>
      </div>
    </template>
  </Draggable>
</template>
<script setup>
import NestedPopover from '@/components/NestedPopover.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import Draggable from 'vuedraggable'
import { Dropdown } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  options: {
    type: Object,
    default: () => ({
      getRoute: null,
      onClick: null,
      onNewClick: null,
    }),
  },
})

const emit = defineEmits(['update', 'loadMore'])

const kanban = defineModel()

const titleField = computed(() => {
  return kanban.value?.params?.title_field
})

const columns = computed(() => {
  if (!kanban.value?.data?.data || kanban.value.data.view_type != 'kanban')
    return []
  let _columns = kanban.value.data.data

  let has_color = _columns.some((column) => column.column?.color)
  if (!has_color) {
    _columns.forEach((column, i) => {
      column.column['color'] = colors[i % colors.length]
    })
  }
  return _columns
})

function actions(column) {
  return [
    {
      group: __('Options'),
      hideLabel: true,
      items: [
        {
          label: __('Delete'),
          icon: 'trash-2',
          onClick: () => {
            column['delete'] = true
            updateColumn()
          },
        },
      ],
    },
  ]
}

function updateColumn({ item, from, to }) {
  let toColumn = to?.dataset.column
  let fromColumn = from?.dataset.column
  let itemName = item?.dataset.name

  let _columns = []
  columns.value.forEach((col) => {
    if (col.delete) return
    col.column['order'] = col.data.map((d) => d.name)
    _columns.push(col.column)
  })

  let data = { kanban_columns: _columns }

  if (toColumn != fromColumn) {
    data = { item: itemName, to: toColumn, kanban_columns: _columns }
  }

  emit('update', data)
}

function colorClasses(color, onlyIcon = false) {
  let textColor = `!text-${color}-600`
  if (color == 'black') {
    textColor = '!text-gray-900'
  } else if (['gray', 'green'].includes(color)) {
    textColor = `!text-${color}-700`
  }

  let bgColor = `!bg-${color}-100 hover:!bg-${color}-200 active:!bg-${color}-300`

  return [textColor, onlyIcon ? '' : bgColor]
}

const colors = [
  'gray',
  'blue',
  'green',
  'red',
  'pink',
  'orange',
  'amber',
  'yellow',
  'cyan',
  'teal',
  'violet',
  'purple',
  'black',
]
</script>
