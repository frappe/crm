<template>
  <div class="flex h-full flex-col">
    <header
      class="flex h-[42px] shrink-0 items-center justify-between border-b border-outline-gray-1 px-5"
    >
      <div class="flex items-center gap-1 text-lg">
        <span class="text-ink-gray-5">{{ __('Leads') }}</span>
        <span class="text-ink-gray-4">/</span>
        <span class="lucide-align-justify ms-1 size-4 text-ink-gray-7" />
        <span class="text-ink-gray-9">{{ __('List') }}</span>
        <span class="lucide-chevron-down ms-1 size-4 text-ink-gray-6" />
      </div>
      <Button
        variant="solid"
        icon-left="lucide-plus"
        :label="__('Create')"
        tabindex="-1"
      />
    </header>

    <div class="flex items-center gap-2 px-5 py-4">
      <span
        v-for="q in [__('Name'), __('Organization')]"
        :key="q"
        class="flex h-7 w-36 items-center rounded-4 bg-surface-gray-2 px-2 text-base text-ink-gray-4"
      >
        {{ q }}
      </span>
      <span
        class="flex h-7 w-36 items-center justify-between rounded-4 bg-surface-gray-2 px-2 text-base text-ink-gray-4"
      >
        {{ __('Status') }}
        <span class="lucide-chevron-down size-4 text-ink-gray-5" />
      </span>
      <div
        class="ms-auto flex items-center gap-2 border-l border-outline-gray-2 ps-2"
      >
        <Button icon="lucide-refresh-cw" tabindex="-1" />
        <Button
          :label="__('Filter')"
          icon-left="lucide-list-filter"
          tabindex="-1"
        />
        <Button
          :label="__('Sort')"
          icon-left="lucide-arrow-down-up"
          tabindex="-1"
        />
      </div>
    </div>

    <div class="min-h-0 flex-1 px-5">
      <List
        :columns="COLUMNS"
        :row-height="40"
        selectable
        class="[--list-row-padding-x:0.75rem]"
      >
        <ListHeader class="rounded-4 bg-surface-gray-2">
          <ListHeaderCell>{{ __('Name') }}</ListHeaderCell>
          <ListHeaderCell>{{ __('Status') }}</ListHeaderCell>
          <ListHeaderCell>{{ __('Lead owner') }}</ListHeaderCell>
          <ListHeaderCell>{{ __('Organization') }}</ListHeaderCell>
          <ListHeaderCell>{{ __('Email') }}</ListHeaderCell>
          <ListHeaderCell>{{ __('Last modified') }}</ListHeaderCell>
        </ListHeader>
        <TransitionGroup v-bind="fade">
          <div v-for="r in rows" :key="r.name">
            <ListRows v-slot="{ item, value }" :items="[r]" row-key="name">
              <ListRow :value="value">
                <ListCell>
                  <span
                    class="flex min-w-0 items-center gap-2 text-base text-ink-gray-9"
                  >
                    <Avatar :label="item.name" size="sm" />
                    <span class="truncate">{{ item.name }}</span>
                  </span>
                </ListCell>
                <ListCell>
                  <span
                    class="flex items-center gap-1.5 text-base text-ink-gray-8"
                  >
                    <StatusDot :class="STATUS_COLOR[item.status]" />
                    {{ __(item.status) }}
                  </span>
                </ListCell>
                <ListCell>
                  <Transition
                    mode="out-in"
                    enter-active-class="transition duration-500 motion-reduce:transition-none"
                    enter-from-class="opacity-0 scale-75"
                  >
                    <span
                      v-if="item.owner"
                      :key="item.owner"
                      class="flex min-w-0 items-center gap-1.5 text-base text-ink-gray-8"
                    >
                      <Avatar
                        :label="item.owner"
                        :image="avatarUrl(item.owner)"
                        size="sm"
                      />
                      <span class="truncate">{{ nameOf(item.owner) }}</span>
                    </span>
                  </Transition>
                </ListCell>
                <ListCell>
                  <span class="truncate text-base text-ink-gray-8">
                    {{ item.organization }}
                  </span>
                </ListCell>
                <ListCell>
                  <span class="truncate text-base text-ink-gray-8">
                    {{ item.email }}
                  </span>
                </ListCell>
                <ListCell>
                  <span class="text-base tabular-nums text-ink-gray-6">
                    {{ item.modified }}
                  </span>
                </ListCell>
              </ListRow>
            </ListRows>
          </div>
        </TransitionGroup>
      </List>
    </div>

    <Transition
      enter-active-class="transition duration-300 ease-out motion-reduce:transition-none"
      enter-from-class="opacity-0 translate-y-2"
      leave-active-class="transition duration-150 motion-reduce:transition-none"
      leave-to-class="opacity-0"
    >
      <div
        v-if="toast"
        class="absolute bottom-6 left-6 flex items-center gap-2 rounded-6 border border-outline-gray-2 bg-surface-base px-3 py-2 text-base text-ink-gray-8 shadow-lg"
      >
        <span
          :class="[
            toast.done ? 'lucide-circle-check' : 'lucide-file-spreadsheet',
            'size-4 text-ink-gray-6',
          ]"
        />
        {{ toast.label }}
      </div>
    </Transition>
  </div>
</template>

<script setup>
import {
  IMPORTED_LEADS,
  SAMPLE_LEADS,
  STATUS_COLOR,
  StatusDot,
  avatarUrl,
  nameOf,
} from '@/components/Setup/setupPreviewData'
import { Avatar, Button } from 'frappe-ui'
import {
  List,
  ListCell,
  ListHeader,
  ListHeaderCell,
  ListRow,
  ListRows,
} from 'frappe-ui/list'
import { computed } from 'vue'

const props = defineProps({
  state: { type: Object, required: true },
})

const COLUMNS = ['11rem', '7.5rem', '8rem', '8rem', '12rem', '6rem']

const importedCount = computed(() => {
  const { importResult, importProgress } = props.state
  const max = IMPORTED_LEADS.length
  if (importResult) return Math.min(importResult.imported, max)
  if (!importProgress?.total) return 0
  return Math.round((importProgress.current / importProgress.total) * max)
})

const invitees = computed(() => props.state.invites || [])
const ownerAt = (lead, i) =>
  invitees.value.length
    ? invitees.value[i % invitees.value.length].email
    : lead.owner

const rows = computed(() => {
  const imported = IMPORTED_LEADS.slice(0, importedCount.value)
  return [...imported, ...SAMPLE_LEADS].map((l, i) => ({
    ...l,
    owner: ownerAt(l, i),
  }))
})

const toast = computed(() => {
  const { importStage, importFile, importProgress, importResult } = props.state
  if (importResult)
    return {
      done: true,
      label: __('{0} leads imported', [importResult.imported]),
    }
  if (importStage !== 'importing') return null
  const count = importProgress
    ? ` · ${importProgress.current} / ${importProgress.total}`
    : ''
  return { done: false, label: `${importFile || __('Importing')}${count}` }
})

const fade = {
  enterActiveClass:
    'transition duration-700 ease-[cubic-bezier(.22,1,.36,1)] motion-reduce:transition-none',
  enterFromClass: 'opacity-0 -translate-y-3',
  moveClass:
    'transition-transform duration-700 ease-[cubic-bezier(.22,1,.36,1)] motion-reduce:transition-none',
}
</script>
