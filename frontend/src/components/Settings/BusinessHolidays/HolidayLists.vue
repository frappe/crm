<template>
  <SettingsLayoutBase
    :title="__('Business Holidays')"
    :description="
      __(
        'Set your team’s working days and holidays. SLA policies skip these when counting time.',
      )
    "
  >
    <template #header-actions>
      <Button
        :label="__('New')"
        variant="solid"
        icon-left="lucide-plus"
        @click="openHolidayList(null)"
      />
    </template>
    <template
      v-if="
        (holidayListResource.data?.length ?? 0) > 9 || holidaySearchQuery.length
      "
      #header-bottom
    >
      <div class="relative">
        <TextInput
          v-model="holidaySearchQuery"
          :placeholder="__('Search')"
          type="text"
          class="bg-surface-gray-2 hover:bg-surface-gray-2 focus:ring-0 border-outline-gray-2 rounded-4"
          :debounce="300"
        >
          <template #prefix>
            <span class="lucide-search size-4" aria-hidden="true" />
          </template>
        </TextInput>
        <Button
          v-if="holidaySearchQuery"
          icon="lucide-x"
          variant="ghost"
          class="absolute right-1 top-1/2 -translate-y-1/2"
          @click="holidaySearchQuery = ''"
        />
      </div>
    </template>
    <template #content>
      <div
        v-if="
          holidayListResource.list.loading && !holidayListResource.list.data
        "
        class="flex items-center justify-center mt-12"
      >
        <LoadingIndicator class="w-4" />
      </div>
      <div v-else class="h-full">
        <EmptyState
          v-if="!holidayListResource.data?.length"
          name="Holiday Lists"
          :title="__('No Holiday Lists Found')"
          :description="__('Add one to get started.')"
          :icon="LucideBriefcase"
        />
        <div v-else class="-ml-2">
          <div :class="[gridCols, 'px-2 text-sm text-ink-gray-5']">
            <div>{{ __('Schedule name') }}</div>
            <div>{{ __('Valid From') }}</div>
            <div>{{ __('Valid To') }}</div>
            <div class="text-right">{{ __('Holidays') }}</div>
            <div />
          </div>
          <hr class="mt-2 mx-2 border-outline-gray-2" />
          <div
            v-for="(holidayList, index) in holidayListResource.data"
            :key="holidayList.name"
          >
            <div
              :class="[
                gridCols,
                'h-14 px-2 cursor-pointer hover:bg-surface-sidebar rounded-4',
              ]"
              @click="openHolidayList(holidayList.name)"
            >
              <div class="text-base-medium text-ink-gray-7 truncate">
                {{ holidayList.name }}
              </div>
              <div class="text-base text-ink-gray-7 tabular-nums">
                {{ formatHolidayDate(holidayList.from_date) }}
              </div>
              <div class="text-base text-ink-gray-7 tabular-nums">
                {{ formatHolidayDate(holidayList.to_date) }}
              </div>
              <div class="text-base text-ink-gray-7 text-right tabular-nums">
                {{ holidayList.total_holidays }}
              </div>
              <div class="flex justify-end" @click.stop>
                <Dropdown
                  align="end"
                  :options="dropdownOptions(holidayList)"
                  @update:open="
                    (open: boolean) => open && (isConfirmingDelete = false)
                  "
                >
                  <Button icon="lucide-more-horizontal" variant="ghost" />
                </Dropdown>
              </div>
            </div>
            <hr
              v-if="index !== holidayListResource.data.length - 1"
              class="mx-2 border-outline-gray-2"
            />
          </div>
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
  <Dialog
    v-model:open="duplicateDialog.show"
    :title="__('Duplicate Holiday List')"
  >
    <template #default>
      <FormControl
        v-model="duplicateDialog.newName"
        :label="__('New Holiday List Name')"
        type="text"
        maxlength="140"
      />
    </template>
    <template #actions>
      <div class="flex gap-2 justify-end">
        <Button
          variant="subtle"
          :label="__('Close')"
          @click="duplicateDialog.show = false"
        />
        <Button
          variant="solid"
          :label="__('Duplicate')"
          :loading="duplicating"
          @click="duplicate()"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import LucideBriefcase from '~icons/lucide/briefcase'
import {
  Button,
  call,
  Dialog,
  Dropdown,
  FormControl,
  LoadingIndicator,
  TextInput,
  toast,
  type FrappeResourceError,
} from 'frappe-ui'
import { ConfirmDelete, htmlToText } from '@/utils'
import { formatHolidayDate, openHolidayList } from './store'
import type {
  HolidayListDoc,
  HolidayListResource,
  HolidayListRow,
} from './types'
import { inject, ref, watch, type Ref } from 'vue'

const holidayListResource = inject('holidayListResource') as HolidayListResource
const holidaySearchQuery = inject('holidaySearchQuery') as Ref<string>

// Header and rows share one grid so the columns line up.
const gridCols =
  'grid grid-cols-[minmax(0,1fr)_7rem_7rem_4.5rem_2.5rem] items-center gap-4'

const duplicateDialog = ref({ show: false, name: '', newName: '' })
const duplicating = ref(false)
const isConfirmingDelete = ref(false)

const dropdownOptions = (holidayList: HolidayListRow) => [
  {
    label: __('Duplicate'),
    icon: 'lucide-copy',
    onClick: () => {
      duplicateDialog.value = {
        show: true,
        name: holidayList.name,
        newName: __('{0} (Copy)', [holidayList.name]),
      }
    },
  },
  ...ConfirmDelete({
    onConfirmDelete: () => deleteHolidayList(holidayList),
    isConfirmingDelete,
  }),
]

function errorMessage(err: unknown, fallback: string) {
  const message = (err as FrappeResourceError | undefined)?.messages?.[0]
  return message ? htmlToText(message) : fallback
}

async function duplicate() {
  const { name, newName } = duplicateDialog.value
  if (!newName.trim()) {
    toast.error(__('Holiday list name is required'))
    return
  }
  duplicating.value = true
  try {
    const source = await call<HolidayListDoc>('frappe.client.get', {
      doctype: 'CRM Holiday List',
      name,
    })
    const copy = await call<HolidayListDoc>('frappe.client.insert', {
      doc: {
        doctype: 'CRM Holiday List',
        holiday_list_name: newName.trim(),
        description: source.description,
        from_date: source.from_date,
        to_date: source.to_date,
        recurring_holidays: source.recurring_holidays,
        holidays: source.holidays.map(({ date, description, weekly_off }) => ({
          date,
          description,
          weekly_off,
        })),
      },
    })
    duplicateDialog.value.show = false
    toast.success(__('Holiday list duplicated'))
    holidayListResource.reload()
    openHolidayList(copy.name)
  } catch (err) {
    toast.error(errorMessage(err, __('Could not duplicate holiday list')))
  } finally {
    duplicating.value = false
  }
}

function deleteHolidayList(holidayList: HolidayListRow) {
  holidayListResource.delete.submit(holidayList.name, {
    onSuccess: () => toast.success(__('Holiday list deleted')),
    onError: (err: unknown) =>
      toast.error(errorMessage(err, __('Could not delete holiday list'))),
  })
}

watch(holidaySearchQuery, (value) => {
  holidayListResource.filters = { name: ['like', `%${value}%`] }
  if (!value) holidayListResource.start = 0
  holidayListResource.reload()
})
</script>
