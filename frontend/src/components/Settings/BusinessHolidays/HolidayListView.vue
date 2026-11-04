<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex items-center gap-2">
        <Button
          variant="ghost"
          icon-left="lucide-chevron-left"
          :label="holidayData.holiday_list_name || __('New Holiday List')"
          size="md"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 text-ink-gray-7 text-lg-semibold hover:opacity-70 !pr-0 !max-w-96 !justify-start"
          @click="goBack()"
        />
        <Badge
          v-if="isDirty"
          variant="subtle"
          theme="amber"
          size="sm"
          :label="__('Not Saved')"
        />
      </div>
    </template>
    <template #header-actions>
      <Button
        :label="__('Save')"
        variant="solid"
        :disabled="
          Boolean(getHolidayList.error) ||
          (!isDirty && Boolean(holidayScreen.name))
        "
        :loading="saving || getHolidayList.loading"
        @click="saveHolidayList()"
      />
    </template>
    <template #content>
      <div
        v-if="getHolidayList.loading"
        class="flex items-center h-full justify-center"
      >
        <LoadingIndicator class="w-4" />
      </div>
      <div
        v-else-if="getHolidayList.error"
        class="flex items-center h-full justify-center"
      >
        <ErrorMessage :message="__('Could not load this holiday list')" />
      </div>
      <div v-else>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <FormControl
              v-model="holidayData.holiday_list_name"
              type="text"
              size="sm"
              variant="subtle"
              :placeholder="__('Name')"
              :label="__('Name')"
              required
              maxlength="140"
              @change="validateHoliday('holiday_list_name')"
            />
            <ErrorMessage
              :message="holidayDataErrors.holiday_list_name"
              class="mt-2"
            />
          </div>
          <FormControl
            v-model="holidayData.description"
            type="textarea"
            size="sm"
            variant="subtle"
            :placeholder="__('Description')"
            :label="__('Description')"
            :rows="2"
          />
        </div>
        <hr class="my-8 border-outline-gray-2" />
        <div>
          <div class="flex flex-col gap-1">
            <span class="text-lg-semibold text-ink-gray-8">
              {{ __('Valid From') }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{ __('Choose the period this holiday list covers.') }}
            </span>
          </div>
          <div class="mt-3.5 flex gap-5 flex-col md:flex-row">
            <div class="w-full space-y-1.5">
              <DatePicker
                v-model="holidayData.from_date"
                :label="__('From Date')"
                required
                variant="subtle"
                :placeholder="__('Select date')"
                class="w-full"
                :format="dateFormat"
                @update:model-value="onDateChange('from_date')"
              >
                <template #prefix>
                  <LucideCalendar class="size-4" />
                </template>
              </DatePicker>
              <ErrorMessage :message="holidayDataErrors.from_date" />
            </div>
            <div class="w-full space-y-1.5">
              <DatePicker
                v-model="holidayData.to_date"
                :label="__('To Date')"
                required
                variant="subtle"
                :placeholder="__('Select date')"
                class="w-full"
                :format="dateFormat"
                @update:model-value="onDateChange('to_date')"
              >
                <template #prefix>
                  <LucideCalendar class="size-4" />
                </template>
              </DatePicker>
              <ErrorMessage :message="holidayDataErrors.to_date" />
            </div>
          </div>
        </div>
        <hr class="my-8 border-outline-gray-2" />
        <div>
          <div class="flex flex-col gap-1">
            <span class="text-lg-semibold text-ink-gray-8">
              {{ __('Recurring Holidays') }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{ __('Add weekly offs such as weekends.') }}
            </span>
          </div>
          <div class="mt-5">
            <RecurringHolidays />
          </div>
        </div>
        <hr class="my-8 border-outline-gray-2" />
        <div>
          <div class="flex justify-between items-center">
            <div class="flex flex-col gap-1">
              <div class="flex items-center gap-2">
                <span class="text-lg-semibold text-ink-gray-8">
                  {{ __('Holidays') }}
                </span>
                <Badge
                  variant="subtle"
                  size="sm"
                  :label="String(holidayData.holidays.length)"
                />
              </div>
              <span class="text-p-sm text-ink-gray-6">
                {{ __('SLA policies skip these days when counting time.') }}
              </span>
            </div>
            <TabButtons v-model="holidayView" :options="viewOptions" />
          </div>
          <div class="mt-5">
            <HolidaysTable
              v-if="holidayView === 'list'"
              @edit="openEditHoliday"
            />
            <HolidaysCalendar
              v-else
              @add="openAddHoliday"
              @edit="openEditHoliday"
            />
          </div>
          <div class="mt-2.5 flex justify-between items-center gap-4">
            <div class="flex items-center gap-4">
              <Button
                variant="subtle"
                :label="__('Add Holiday')"
                icon-left="lucide-plus"
                @click="openAddHoliday()"
              />
              <ErrorMessage :message="holidayDataErrors.holidays" />
            </div>
            <div v-if="holidayView === 'calendar'" class="flex gap-4">
              <div class="flex items-center gap-1">
                <span class="bg-surface-amber-2 size-4 rounded-1" />
                <span class="text-sm text-ink-gray-6">
                  {{ __('Holidays') }}
                </span>
              </div>
              <div class="flex items-center gap-1">
                <span class="bg-surface-gray-3 size-4 rounded-1" />
                <span class="text-sm text-ink-gray-6">
                  {{ __('Weekly offs') }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
  <HolidayModal v-model="holidayModal" />
</template>

<script setup lang="ts">
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import {
  Badge,
  Button,
  call,
  createResource,
  DatePicker,
  dialog,
  ErrorMessage,
  FormControl,
  LoadingIndicator,
  TabButtons,
  toast,
  type FrappeResourceError,
} from 'frappe-ui'
import { computed, inject, onUnmounted, ref, watch } from 'vue'
import {
  activeSettingsPage,
  disableSettingModalOutsideClick,
} from '@/composables/settings'
import { useUnsavedChangesWarning } from '@/composables/useUnsavedChangesWarning'
import { getFormat, htmlToText } from '@/utils'
import { slaToReopen } from '../Sla/utils'
import HolidayModal from './HolidayModal.vue'
import HolidaysCalendar from './HolidaysCalendar.vue'
import HolidaysTable from './HolidaysTable.vue'
import RecurringHolidays from './RecurringHolidays.vue'
import {
  holidayData,
  holidayDataErrors,
  holidayScreen,
  resetHolidayDataErrors,
  updateWeeklyOffDates,
  validateHoliday,
} from './store'
import type {
  Holiday,
  HolidayListDoc,
  HolidayListForm,
  HolidayListResource,
  HolidayModalState,
  RecurringHoliday,
} from './types'
import { reconcileWeeklyOffs, sortHolidays } from './utils'

const holidayListResource = inject('holidayListResource') as HolidayListResource

const dateFormat = getFormat('', '', true, false, false)
const holidayView = ref<'calendar' | 'list'>('calendar')
const viewOptions = [
  { value: 'calendar', label: __('Calendar'), iconLeft: 'lucide-calendar' },
  { value: 'list', label: __('List'), iconLeft: 'lucide-list' },
]

const holidayModal = ref<HolidayModalState>({
  show: false,
  date: '',
  description: '',
  editing: null,
})

const saving = ref(false)
const initialData = ref('')
const isDirty = computed(
  () =>
    Boolean(initialData.value) &&
    JSON.stringify(holidayData.value) !== initialData.value,
)

function toForm(doc: HolidayListDoc): HolidayListForm {
  // Descriptions are a Text Editor field, so desk may have saved them as HTML.
  const holidays: Holiday[] = sortHolidays(
    doc.holidays.map((holiday) => ({
      date: holiday.date,
      description: htmlToText(holiday.description || ''),
      weekly_off: holiday.weekly_off ? 1 : 0,
    })),
  )
  let rules: RecurringHoliday[]
  try {
    rules = JSON.parse(doc.recurring_holidays || '[]')
  } catch {
    rules = []
  }
  return {
    name: doc.name,
    holiday_list_name: doc.holiday_list_name,
    description: doc.description || '',
    from_date: doc.from_date,
    to_date: doc.to_date,
    ...reconcileWeeklyOffs(holidays, rules, doc.from_date, doc.to_date),
  }
}

const getHolidayList = createResource({
  url: 'frappe.client.get',
  makeParams: () => ({
    doctype: 'CRM Holiday List',
    name: holidayScreen.value.name,
  }),
  onSuccess(doc: HolidayListDoc) {
    holidayData.value = toForm(doc)
    initialData.value = JSON.stringify(holidayData.value)
  },
})

if (holidayScreen.value.name) {
  getHolidayList.fetch()
} else {
  initialData.value = JSON.stringify(holidayData.value)
}

function onDateChange(key: 'from_date' | 'to_date') {
  validateHoliday(key)
  if (!holidayDataErrors.value.to_date) updateWeeklyOffDates()
}

function openAddHoliday(date = '') {
  if (!holidayData.value.from_date || !holidayData.value.to_date) {
    toast.error(__('Choose the from and to dates first'))
    return
  }
  holidayModal.value = { show: true, date, description: '', editing: null }
}

function openEditHoliday(holiday: Holiday) {
  holidayModal.value = {
    show: true,
    date: holiday.date,
    description: holiday.description,
    editing: holiday,
  }
}

function goBack() {
  if (isDirty.value) {
    dialog.confirm({
      title: __('Unsaved Changes'),
      message: __(
        'Are you sure you want to go back? Unsaved changes will be lost.',
      ),
      onConfirm: leave,
    })
    return
  }
  leave()
}

function leave() {
  const returnToSla = holidayScreen.value.returnToSla
  // Workaround fix for settings modal not closing after going back
  setTimeout(() => {
    if (returnToSla) {
      slaToReopen.value = returnToSla
      activeSettingsPage.value = __('SLA Policies')
      return
    }
    holidayScreen.value = { screen: 'list', name: null }
  }, 250)
}

function toDocValues(form: HolidayListForm) {
  return {
    holiday_list_name: form.holiday_list_name.trim(),
    description: form.description,
    from_date: form.from_date,
    to_date: form.to_date,
    holidays: form.holidays.map(({ date, description, weekly_off }) => ({
      date,
      description,
      weekly_off,
    })),
    recurring_holidays: JSON.stringify(form.recurring_holidays),
  }
}

async function saveHolidayList() {
  if (getHolidayList.error) return
  const errors = validateHoliday()
  if (Object.values(errors).some(Boolean)) {
    toast.error(
      __('Invalid fields, check if all are filled in and values are correct.'),
    )
    return
  }

  const values = toDocValues(holidayData.value)
  const oldName = holidayScreen.value.name
  saving.value = true
  try {
    if (!oldName) {
      const doc = await call<HolidayListDoc>('frappe.client.insert', {
        doc: { doctype: 'CRM Holiday List', ...values },
      })
      toast.success(__('Holiday list created'))
      holidayScreen.value = { ...holidayScreen.value, name: doc.name }
    } else {
      const name = await call<string>(
        'crm.fcrm.doctype.crm_holiday_list.crm_holiday_list.save_holiday_list',
        { name: oldName, values },
      )
      if (name !== oldName) {
        holidayScreen.value = { ...holidayScreen.value, name }
      } else {
        await getHolidayList.reload()
      }
      toast.success(__('Holiday list updated'))
    }
  } catch (err) {
    const message = (err as FrappeResourceError | undefined)?.messages?.[0]
    toast.error(
      message
        ? htmlToText(message)
        : __('Some error occurred while saving the holiday list'),
    )
  } finally {
    saving.value = false
    holidayListResource.reload()
  }
}

watch(isDirty, (dirty) => {
  disableSettingModalOutsideClick.value = dirty
})

useUnsavedChangesWarning(() => isDirty.value)

onUnmounted(() => {
  resetHolidayDataErrors()
  disableSettingModalOutsideClick.value = false
})
</script>
