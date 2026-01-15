<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex items-center gap-2">
        <Button
          variant="ghost"
          icon-left="chevron-left"
          :label="
            holidayListData.holiday_list_name || __('New Business Holiday')
          "
          size="md"
          @click="goBack()"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 font-semibold text-ink-gray-7 text-lg hover:opacity-70 !pr-0 !max-w-96 !justify-start"
        />
        <Badge
          variant="subtle"
          theme="orange"
          size="sm"
          :label="__('Unsaved')"
          v-if="isDirty"
        />
      </div>
    </template>
    <template #header-actions>
      <Button
        :label="__('Save')"
        theme="gray"
        variant="solid"
        @click="saveBusinessHoliday()"
        :disabled="Boolean(!isDirty && holidayListActiveStep.data)"
        :loading="
          holidayListResource.setValue.loading ||
          renameBusinessHolidayResource.loading ||
          getBusinessHolidayResource.loading
        "
      />
    </template>
    <template #content>
      <div
        v-if="getBusinessHolidayResource.loading"
        class="flex items-center h-full justify-center"
      >
        <LoadingIndicator class="w-4" />
      </div>
      <div v-if="!getBusinessHolidayResource.loading">
        <div class="flex items-center gap-2 mt-2">
          <span class="text-sm">
            There are in total
            <b>{{ holidayListData.holidays.length }}</b> holidays in this
            list</span
          >
        </div>
        <hr class="mt-2 mb-8 border-outline-gray-2" />
        <div class="space-y-2">
          <FormControl
            :type="'text'"
            size="sm"
            variant="subtle"
            :placeholder="__('Name')"
            :label="__('Name')"
            v-model="holidayListData.holiday_list_name"
            required
            @change="validateHolidayListData('holiday_list_name')"
            maxlength="100"
          />
          <ErrorMessage :message="holidayListDataErrors.holiday_list_name" />
        </div>
        <hr class="my-8 border-outline-gray-2" />
        <div>
          <div class="flex flex-col gap-1">
            <span class="text-lg font-semibold text-ink-gray-8">{{
              __('Valid from')
            }}</span>
            <span class="text-p-sm text-ink-gray-6">
              {{ __('Choose the duration of this holiday list.') }}
            </span>
          </div>
          <div class="mt-3.5 flex gap-5 flex-col md:flex-row">
            <div class="w-full space-y-1.5">
              <FormLabel :label="__('From date')" for="from_date" required />
              <DatePicker
                v-model="holidayListData.from_date"
                variant="subtle"
                placeholder="11/01/2025"
                class="w-full"
                id="from_date"
                :format="getFormat()"
                :debounce="300"
                @update:model-value="updateDuration('from_date')"
              >
                <template #prefix>
                  <LucideCalendar class="size-4" />
                </template>
              </DatePicker>
              <ErrorMessage
                :message="
                  holidayListDataErrors.from_date ||
                  holidayListDataErrors.dateRange
                "
              />
            </div>
            <div class="w-full space-y-1.5">
              <FormLabel :label="__('To date')" for="to_date" required />
              <DatePicker
                v-model="holidayListData.to_date"
                variant="subtle"
                placeholder="25/12/2025"
                class="w-full"
                id="to_date"
                :format="getFormat()"
                :debounce="300"
                @update:model-value="updateDuration('to_date')"
              >
                <template #prefix>
                  <LucideCalendar class="size-4" />
                </template>
              </DatePicker>
              <ErrorMessage :message="holidayListDataErrors.to_date" />
            </div>
          </div>
        </div>
        <hr class="my-8 border-outline-gray-2" />
        <div>
          <div class="flex flex-col gap-1">
            <div class="text-lg font-semibold text-ink-gray-8">
              {{ __('Recurring holidays') }}
            </div>
            <div class="text-p-sm text-ink-gray-6">
              {{ __('Add recurring holidays such as weekends.') }}
            </div>
          </div>
          <div class="mt-5">
            <RecurringHolidaysList
              :holidayData="holidayListData"
              :holidays="holidayListData.recurring_holidays"
            />
          </div>
        </div>
        <hr class="my-8 border-outline-gray-2" />
        <div>
          <div class="flex justify-between items-center">
            <div class="flex justify-between flex-col gap-1">
              <span class="text-lg font-semibold text-ink-gray-8">
                {{ __('Holidays') }}
              </span>
              <div class="text-p-sm text-ink-gray-6">
                {{
                  __(
                    'Add holidays here to make sure they’re excluded from SLA calculations.',
                  )
                }}
              </div>
            </div>
            <TabButtons
              :buttons="[
                {
                  value: 'calendar',
                  icon: 'calendar',
                },
                {
                  value: 'list',
                  icon: 'list',
                },
              ]"
              v-model="holidayListView"
            />
          </div>
          <div class="mt-5">
            <HolidaysTableView v-if="holidayListView === 'list'" />
            <HolidaysCalendarView v-else />
          </div>
          <div class="mt-2.5 flex justify-between items-center">
            <div class="flex items-center gap-2">
              <Button
                variant="subtle"
                :label="__('Add Holiday')"
                @click="dialog.show = true"
                icon-left="plus"
              />
              <input
                ref="csvInputRef"
                type="file"
                accept=".csv"
                class="hidden"
                @change="handleFileSelect"
              />
              <Dropdown :options="importOptions">
                <Button variant="subtle" class="flex items-center gap-2">
                  <div class="flex items-center gap-2">
                    <ImportIcon class="size-4" />
                    {{ __('Import') }}
                  </div>
                </Button>
              </Dropdown>
            </div>
            <!-- Indicators -->
            <div class="flex gap-4" v-if="holidayListView === 'calendar'">
              <div class="gap-1 flex items-center">
                <span class="bg-yellow-100 size-4 rounded-sm" />
                <span class="text-sm text-ink-gray-6">{{
                  __('Holidays')
                }}</span>
              </div>
              <div class="gap-1 flex items-center">
                <span class="bg-gray-100 size-4 rounded-sm" />
                <span class="text-sm text-ink-gray-6">{{
                  __('Recurring holidays')
                }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
  <AddHolidayModal v-model="dialog" />
  <ConfirmDialog
    v-model="showConfirmDialog.show"
    :title="showConfirmDialog.title"
    :message="showConfirmDialog.message"
    :onConfirm="showConfirmDialog.onConfirm"
    :onCancel="() => (showConfirmDialog.show = false)"
  />
</template>

<script setup>
import {
  Badge,
  Button,
  ConfirmDialog,
  createResource,
  DatePicker,
  dayjs,
  Dropdown,
  ErrorMessage,
  FormControl,
  FormLabel,
  LoadingIndicator,
  TabButtons,
  toast,
} from 'frappe-ui'
import { computed, inject, onMounted, onUnmounted, ref, watch } from 'vue'
import SettingsLayoutBase from '../../Layouts/SettingsLayoutBase.vue'
import {
  resetHolidayListErrors,
  holidayListData,
  holidayListDataErrors,
  validateHolidayListData,
  updateWeeklyOffDates,
  holidayListActiveStep,
} from './utils'
import {
  disableSettingModalOutsideClick,
  setSettingsActiveTab,
} from '../../../composables/settings'
import RecurringHolidaysList from './RecurringHolidaysList.vue'
import HolidaysTableView from './HolidaysTableView.vue'
import HolidaysCalendarView from './HolidaysCalendarView.vue'
import { getFormat, htmlToText } from '../../../utils'
import AddHolidayModal from './AddHolidayModal.vue'
import ImportIcon from '~icons/lucide/arrow-down-to-line'
import DownloadIcon from '~icons/lucide/download'
import { slaActiveStep } from '../Sla/utils'

const isDirty = ref(false)
const initialData = ref(null)
const useNewUI = ref(true)
const isOldBusinessHoliday = ref(false)
const showConfirmDialog = ref({
  show: false,
  title: '',
  message: '',
  onConfirm: () => {},
})
const dialog = ref({
  show: false,
  date: new Date(),
  description: '',
  editing: null,
})
const holidayListView = ref('calendar')
const csvInputRef = ref(null)
const holidayListResource = inject('holidayListResource')

const getBusinessHolidayResource = createResource({
  url: 'frappe.client.get',
  params: {
    doctype: 'CRM Holiday List',
    name: holidayListActiveStep.value.data?.name,
  },
  onSuccess(data) {
    holidayListData.value = data
    initialData.value = JSON.stringify(data)
  },
  transform(data) {
    for (let holiday of data.holidays) {
      holiday.description = htmlToText(holiday.description)
    }
    data.recurring_holidays = JSON.parse(data.recurring_holidays || '[]')
    return data
  },
})

if (holidayListActiveStep.value.data) {
  getBusinessHolidayResource.submit()
} else {
  disableSettingModalOutsideClick.value = true
  initialData.value = JSON.stringify(holidayListData.value)
}

const goBack = () => {
  const confirmDialogInfo = {
    show: true,
    title: __('Unsaved changes'),
    message: __(
      'Are you sure you want to go back? Unsaved changes will be lost.',
    ),
    onConfirm: goBack,
  }

  if (isDirty.value && !showConfirmDialog.value.show) {
    showConfirmDialog.value = confirmDialogInfo
    return
  }

  if (holidayListActiveStep.value.previousScreen) {
    slaActiveStep.value = {
      screen: 'view',
      data: { name: holidayListActiveStep.value.previousScreen.data },
      fetchData: false,
    }
    holidayListActiveStep.value = {
      screen: 'list',
      data: null,
      previousScreen: null,
    }
    setSettingsActiveTab('SLA Policies')
    return
  }
  setTimeout(() => {
    holidayListActiveStep.value = {
      screen: 'list',
      data: null,
    }
  }, 250)
  showConfirmDialog.value.show = false
}

const saveBusinessHoliday = () => {
  const validationErrors = validateHolidayListData()

  if (Object.values(validationErrors).some((error) => error)) {
    toast.error(
      __('Invalid fields, check if all are filled in and values are correct.'),
    )
    return
  }

  if (holidayListActiveStep.value.data) {
    if (isOldBusinessHoliday.value && useNewUI.value) {
      showConfirmDialog.value = {
        show: true,
        title: __('Confirm overwrite'),
        message: __(
          'Your old conditions will be overwritten. Are you sure you want to save?',
        ),
        onConfirm: () => {
          updateBusinessHoliday()
          showConfirmDialog.value.show = false
        },
      }
      return
    }
    updateBusinessHoliday()
  } else {
    createBusinessHoliday()
  }
}

const createBusinessHoliday = () => {
  const holidays = holidayListData.value.holidays.map((holiday) => {
    return {
      ...holiday,
      date: dayjs(holiday.date).format('YYYY-MM-DD'),
    }
  })

  holidayListResource.insert.submit(
    {
      ...holidayListData.value,
      holidays: holidays,
      recurring_holidays: JSON.stringify(
        holidayListData.value.recurring_holidays,
      ),
    },
    {
      onSuccess(data) {
        toast.success(__('Holiday list created'))
        holidayListData.value = data
        holidayListActiveStep.value = {
          ...holidayListActiveStep.value,
          screen: 'view',
          data: data,
        }
        getBusinessHolidayResource.submit({
          doctype: 'CRM Holiday List',
          name: data.name,
        })
      },
      onError(err) {
        const message = err?.messages?.[0]
        toast.error(
          message || __('Some error occurred while creating SLA policy'),
        )
      },
    },
  )
}

const renameBusinessHolidayResource = createResource({
  url: 'frappe.client.rename_doc',
  makeParams() {
    return {
      doctype: 'CRM Holiday List',
      old_name: holidayListData.value.name,
      new_name: holidayListData.value.holiday_list_name,
    }
  },
})

const updateBusinessHoliday = async () => {
  const holidays = holidayListData.value.holidays.map((holiday) => {
    return {
      ...holiday,
      date: dayjs(holiday.date).format('YYYY-MM-DD'),
    }
  })

  await holidayListResource.setValue.submit(
    {
      ...holidayListData.value,
      holidays: holidays,
      recurring_holidays: JSON.stringify(
        holidayListData.value.recurring_holidays,
      ),
    },
    {
      onError(err) {
        const message = err?.messages?.[0]
        toast.error(
          message || __('Some error occurred while updating SLA policy'),
        )
      },
    },
  )

  if (holidayListData.value.name !== holidayListData.value.holiday_list_name) {
    await renameBusinessHolidayResource.submit().catch(async (er) => {
      const error =
        er?.messages?.[0] ||
        __('Some error occurred while renaming business holiday')
      toast.error(error)
      // Reset assignment rule to previous state
      await getBusinessHolidayResource.reload()
      isLoading.value = false
    })

    getBusinessHolidayResource.submit({
      doctype: 'CRM Holiday List',
      name: holidayListData.value.holiday_list_name,
    })
  } else {
    await getBusinessHolidayResource.reload()
  }

  toast.success(__('Business holiday updated'))
  holidayListResource.reload()
}

const importOptions = computed(() => [
  {
    label: __('Select file (CSV)'),
    icon: 'file',
    onClick: () => {
      csvInputRef.value?.click()
    },
  },
  {
    label: __('Download template'),
    icon: DownloadIcon,
    onClick: () => {
      downloadTemplate()
    },
  },
])

const handleFileSelect = (event) => {
  const file = event.target.files?.[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const text = e.target.result
      const lines = text.split('\n').filter((line) => line.trim())

      if (lines.length < 2) {
        toast.error(__('CSV file is empty or has no data rows'))
        return
      }

      // Parse header to find column indices
      const header = lines[0].split(',').map((h) => h.trim().toLowerCase())
      const dateIndex = header.findIndex(
        (h) => h === 'date' || h === 'holiday_date',
      )
      const descriptionIndex = header.findIndex(
        (h) =>
          h === 'description' ||
          h === 'holiday_description' ||
          h === 'name' ||
          h === 'holiday_name',
      )

      if (dateIndex === -1) {
        toast.error(__('CSV must have a "date" or "holiday_date" column'))
        return
      }

      let importedCount = 0
      let skippedCount = 0

      for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(',').map((v) => v.trim())
        const dateStr = values[dateIndex]
        const description =
          descriptionIndex !== -1 ? values[descriptionIndex] : ''

        if (!dateStr) continue

        const parsedDate = dayjs(dateStr)
        if (!parsedDate.isValid()) {
          skippedCount++
          continue
        }

        // Check if date is within the valid range
        const fromDate = dayjs(holidayListData.value.from_date)
        const toDate = dayjs(holidayListData.value.to_date)
        if (
          fromDate.isValid() &&
          toDate.isValid() &&
          (parsedDate.isBefore(fromDate, 'day') ||
            parsedDate.isAfter(toDate, 'day'))
        ) {
          skippedCount++
          continue
        }

        // Check for duplicate dates
        const dateExists = holidayListData.value.holidays.some(
          (h) =>
            dayjs(h.date).format('YYYY-MM-DD') ===
            parsedDate.format('YYYY-MM-DD'),
        )

        if (dateExists) {
          skippedCount++
          continue
        }

        holidayListData.value.holidays.push({
          date: parsedDate.toDate(),
          description: description || '',
          weekly_off: 0,
        })
        importedCount++
      }

      if (importedCount > 0) {
        toast.success(__('Imported {0} holiday(s)', [importedCount]))
      } else {
        toast.warning(__('No new holidays were imported'))
      }
    } catch (error) {
      console.error('CSV import error:', error)
      toast.error(__('Failed to import CSV file'))
    }
  }
  reader.readAsText(file)

  // Reset input so the same file can be selected again
  event.target.value = ''
}

const downloadTemplate = () => {
  const currentYear = dayjs().year()
  const csvContent = `date,description
${currentYear}-01-01,New Year
${currentYear}-12-25,Christmas Day`

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)

  link.setAttribute('href', url)
  link.setAttribute('download', 'holiday_import_template.csv')
  link.style.visibility = 'hidden'

  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

const updateDuration = (key) => {
  validateHolidayListData(key)
  if (
    !holidayListDataErrors.value.dateRange ||
    holidayListDataErrors.value.dateRange === ''
  ) {
    updateWeeklyOffDates()
  }
}

watch(
  holidayListData,
  (newVal) => {
    if (!initialData.value) return
    isDirty.value = JSON.stringify(newVal) != initialData.value
    if (isDirty.value) {
      disableSettingModalOutsideClick.value = true
    } else {
      disableSettingModalOutsideClick.value = false
    }
  },
  { deep: true },
)

const beforeUnloadHandler = (event) => {
  if (!isDirty.value) return
  event.preventDefault()
  event.returnValue = true
}

onMounted(() => {
  addEventListener('beforeunload', beforeUnloadHandler)
})

onUnmounted(() => {
  removeEventListener('beforeunload', beforeUnloadHandler)
  resetHolidayListErrors()
  disableSettingModalOutsideClick.value = false
})
</script>
