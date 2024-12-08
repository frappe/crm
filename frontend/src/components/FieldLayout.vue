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
                gridClass(section.columns),
                { 'px-3 sm:px-5': hasTabs },
                { 'mt-6': !section.hideLabel },
              ]"
            >
              <div v-for="field in section.fields" :key="field.name">
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
                    v-else-if="field.type === 'Select'"
                    type="select"
                    class="form-control"
                    :class="field.prefix ? 'prefix' : ''"
                    :options="field.options"
                    v-model="data[field.name]"
                    :placeholder="getPlaceholder(field)"
                  >
                    <template v-if="field.prefix" #prefix>
                      <IndicatorIcon :class="field.prefix" />
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
                    <Link
                      class="form-control flex-1 truncate"
                      :value="data[field.name]"
                      :doctype="field.options"
                      :filters="field.filters"
                      @change="(v) => (data[field.name] = v)"
                      :placeholder="getPlaceholder(field)"
                      :onCreate="field.create"
                    />
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

                  <Link
                    v-else-if="field.type === 'User'"
                    class="form-control"
                    :value="getUser(data[field.name]).full_name"
                    :doctype="field.options"
                    :filters="field.filters"
                    @change="(v) => (data[field.name] = v)"
                    :placeholder="getPlaceholder(field)"
                    :hideMe="true"
                  >
                    <template #prefix>
                      <UserAvatar
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
                        <div class="cursor-pointer">
                          {{ getUser(option.value).full_name }}
                        </div>
                      </Tooltip>
                    </template>
                  </Link>
                  <DateTimePicker
                    v-else-if="field.type === 'Datetime'"
                    v-model="data[field.name]"
                    icon-left=""
                    :formatter="(date) => getFormat(date, '', true, true)"
                    :placeholder="getPlaceholder(field)"
                    input-class="border-none"
                  />
                  <DatePicker
                    v-else-if="field.type === 'Date'"
                    icon-left=""
                    v-model="data[field.name]"
                    :formatter="(date) => getFormat(date, '', true)"
                    :placeholder="getPlaceholder(field)"
                    input-class="border-none"
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
import { usersStore } from '@/stores/users'
import { getFormat } from '@/utils'
import { Tabs, Tooltip, DatePicker, DateTimePicker } from 'frappe-ui'
import { ref, computed } from 'vue'

const { getUser } = usersStore()

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

const getPlaceholder = (field) => {
  if (field.placeholder) {
    return __(field.placeholder)
  }
  if (['Select', 'Link'].includes(field.type)) {
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

.section {
  display: none;
}

.section:has(.settings-field) {
  display: block;
}
</style>
