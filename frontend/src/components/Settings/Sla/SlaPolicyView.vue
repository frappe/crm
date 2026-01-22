<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex items-center gap-2">
        <Button
          variant="ghost"
          icon-left="chevron-left"
          :label="slaData.sla_name || __('New SLA policy')"
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
      <div class="flex gap-4 items-center">
        <div
          class="flex items-center justify-between gap-2 cursor-pointer"
          @click="toggleEnabled"
        >
          <Switch size="sm" :model-value="slaData.enabled" />
          <span class="text-sm text-ink-gray-7 font-medium">
            {{ __('Enabled') }}
          </span>
        </div>
        <Button
          :label="__('Save')"
          theme="gray"
          variant="solid"
          @click="saveSla()"
          :disabled="Boolean(!isDirty && step.data)"
          :loading="
            slaPolicyListResource.setValue.loading ||
            renameSlaResource.loading ||
            getSlaResource.loading
          "
        />
      </div>
    </template>
    <template #content>
      <div
        v-if="getSlaResource.loading"
        class="flex items-center h-full justify-center"
      >
        <LoadingIndicator class="w-4" />
      </div>
      <div v-if="!getSlaResource.loading">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <FormControl
              :type="'text'"
              size="sm"
              variant="subtle"
              :placeholder="__('Name')"
              :label="__('Name')"
              v-model="slaData.sla_name"
              required
              @change="validateSlaData('sla_name')"
              maxlength="100"
            />
            <ErrorMessage :message="slaDataErrors.sla_name" class="mt-2" />
          </div>
          <div class="space-y-1.5">
            <FormLabel :label="__('Apply on')" required />
            <Select
              :options="[
                {
                  label: 'Lead',
                  value: 'CRM Lead',
                },
                {
                  label: 'Deal',
                  value: 'CRM Deal',
                },
              ]"
              v-model="slaData.apply_on"
            />
          </div>
          <div class="space-y-0.5">
            <Checkbox
              :label="__('Rolling responses')"
              v-model="slaData.rolling_responses"
            />
            <div class="text-p-sm text-ink-gray-5">
              {{
                __(
                  'Restart the SLA each time the customer replies (status changes to Open) and fulfill it when marked as Replied',
                )
              }}
            </div>
          </div>
        </div>
        <hr class="my-8 border-outline-gray-2" />
        <div>
          <div class="flex flex-col gap-1">
            <span class="text-lg font-semibold text-ink-gray-8">{{
              __('Assignment conditions')
            }}</span>
            <span class="text-p-sm text-ink-gray-6">
              {{ __('Choose which tickets are affected by this policy.') }}
            </span>
          </div>
          <div class="mt-3">
            <div class="flex items-center justify-between">
              <Checkbox
                :label="__('Set as default SLA')"
                :model-value="slaData.default"
                @update:model-value="toggleDefaultSla"
                class="text-ink-gray-6 text-base font-medium"
              />
              <div v-if="isOldSla && step.data && !slaData.default">
                <Popover trigger="hover" :hoverDelay="0.25" placement="top-end">
                  <template #target>
                    <div
                      class="text-sm text-ink-gray-6 flex gap-1 cursor-default"
                    >
                      {{ __('Old Conditions') }}
                      <FeatherIcon name="info" class="size-4" />
                    </div>
                  </template>
                  <template #body-main>
                    <div
                      class="text-sm text-ink-gray-6 p-2 bg-white rounded-md max-w-96 text-wrap whitespace-pre-wrap leading-5"
                    >
                      <code>{{ slaData.condition }}</code>
                    </div>
                  </template>
                </Popover>
              </div>
            </div>
            <div class="mt-5">
              <div
                class="flex flex-col gap-3 items-center text-center text-ink-gray-7 text-sm mb-2 border border-outline-gray-3 rounded-md p-3 py-4"
                v-if="!useNewUI"
              >
                <span class="text-p-sm">
                  Conditions for this SLA were created from
                  <a :href="deskUrl" target="_blank" class="underline">desk</a>
                  which are not compatible with this UI, you will need to
                  recreate the conditions here if you want to manage and add new
                  conditions from this UI.
                </span>
                <Button
                  :label="__('I understand, add conditions')"
                  variant="subtle"
                  theme="gray"
                  @click="useNewUI = true"
                />
              </div>
              <SlaAssignmentConditions
                :conditions="slaData.condition_json"
                v-if="useNewUI"
              />
            </div>
          </div>
        </div>
        <hr class="my-8 border-outline-gray-2" />
        <div>
          <div class="flex flex-col gap-1">
            <span class="text-lg font-semibold text-ink-gray-8">
              {{ __('Valid from') }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{ __('Choose how long this SLA policy will be active.') }}
            </span>
          </div>
          <div class="mt-3.5 flex gap-5 flex-col md:flex-row">
            <div class="w-full space-y-1.5">
              <FormLabel :label="__('Start date')" for="start_date" />
              <DatePicker
                v-model="slaData.start_date"
                variant="subtle"
                placeholder="11/01/2025"
                class="w-full"
                id="start_date"
                @change="validateSlaData('start_date')"
                :formatter="(date) => getFormattedDate(date)"
              >
                <template #prefix>
                  <LucideCalendar class="size-4" />
                </template>
              </DatePicker>
              <ErrorMessage :message="slaDataErrors.start_date" />
            </div>
            <div class="w-full space-y-1.5">
              <FormLabel :label="__('End date')" for="end_date" />
              <DatePicker
                v-model="slaData.end_date"
                variant="subtle"
                placeholder="25/12/2025"
                class="w-full"
                id="end_date"
                @change="validateSlaData('end_date')"
                :formatter="(date) => getFormattedDate(date)"
              >
                <template #prefix>
                  <LucideCalendar class="size-4" />
                </template>
              </DatePicker>
              <ErrorMessage :message="slaDataErrors.end_date" />
            </div>
          </div>
        </div>
        <hr class="my-8 border-outline-gray-2" />
        <div>
          <div class="flex flex-col gap-1">
            <span class="text-lg font-semibold text-ink-gray-8">
              {{ __('Response & Follow up') }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{
                __(
                  'Add time targets around support milestones like first response',
                )
              }}
            </span>
          </div>
          <div class="mt-5">
            <div class="mt-5">
              <SlaPriorityList />
            </div>
          </div>
        </div>
        <hr class="my-8 border-outline-gray-2" />
        <SlaHolidays />
      </div>
    </template>
  </SettingsLayoutBase>
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
  Checkbox,
  ConfirmDialog,
  createResource,
  DatePicker,
  ErrorMessage,
  FeatherIcon,
  FormControl,
  FormLabel,
  LoadingIndicator,
  Popover,
  Select,
  Switch,
  toast,
} from 'frappe-ui'
import { inject, onMounted, onUnmounted, ref, watch } from 'vue'
import SettingsLayoutBase from '../../Layouts/SettingsLayoutBase.vue'
import {
  resetSlaDataErrors,
  slaData,
  slaDataErrors,
  validateSlaData,
} from './utils'
import SlaAssignmentConditions from './SlaAssignmentConditions.vue'
import { disableSettingModalOutsideClick } from '../../../composables/settings'
import { convertToConditions } from '../../../utils'
import SlaHolidays from './SlaHolidays.vue'
import SlaPriorityList from './SlaPriorityList.vue'

const isDirty = ref(false)
const initialData = ref(null)
const useNewUI = ref(true)
const isOldSla = ref(false)
const showConfirmDialog = ref({
  show: false,
  title: '',
  message: '',
  onConfirm: () => {},
})

const slaPolicyListResource = inject('slaPolicyListResource')
const step = inject('step')
const updateStep = inject('updateStep')

const deskUrl = `${window.location.origin}/app/crm-service-level-agreement/${step.value.data?.name}`

const getSlaResource = createResource({
  url: 'frappe.client.get',
  params: {
    doctype: 'CRM Service Level Agreement',
    name: step.value.data?.name,
  },
  onSuccess(data) {
    let condition_json
    try {
      condition_json = JSON.parse(data.condition_json || '[]')
    } catch (error) {
      toast.error(
        __(
          'Assignment conditions are invalid or corrupt, recreate the conditions.',
        ),
      )
      condition_json = []
    }

    const newData = {
      ...data,
      enabled: Boolean(data.enabled),
      default: Boolean(data.default),
      rolling_responses: Boolean(data.rolling_responses),
      loading: false,
      condition_json: condition_json,
    }
    slaData.value = newData
    step.value.data = newData

    initialData.value = JSON.stringify(newData)
    const conditionsAvailable = slaData.value.condition?.length > 0
    const conditionsJsonAvailable = slaData.value.condition_json?.length > 0
    if (conditionsAvailable && !conditionsJsonAvailable) {
      useNewUI.value = false
      isOldSla.value = true
    } else {
      useNewUI.value = true
      isOldSla.value = false
    }
  },
})

if (step.value.data && step.value.fetchData) {
  getSlaResource.submit()
} else {
  disableSettingModalOutsideClick.value = true
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
  if (!step.value.data && !showConfirmDialog.value.show) {
    showConfirmDialog.value = confirmDialogInfo
    return
  }
  // Workaround fix for settings modal not closing after going back
  setTimeout(() => {
    step.value = {
      screen: 'list',
      data: null,
      fetchData: true,
    }
  }, 250)
  showConfirmDialog.value.show = false
}

const toggleEnabled = () => {
  if (slaData.value.default) {
    toast.error(__('SLA set as default cannot be disabled'))
    return
  }
  slaData.value.enabled = !slaData.value.enabled
}

const toggleDefaultSla = () => {
  slaData.value.default = !slaData.value.default
  if (slaData.value.default) {
    slaData.value.enabled = true
  }
}

const saveSla = () => {
  const validationErrors = validateSlaData(undefined, !useNewUI.value)

  if (Object.values(validationErrors).some((error) => error)) {
    toast.error(
      __('Invalid fields, check if all are filled in and values are correct.'),
    )
    return
  }

  if (step.value.data) {
    if (isOldSla.value && useNewUI.value) {
      showConfirmDialog.value = {
        show: true,
        title: __('Confirm overwrite'),
        message: __(
          'Your old conditions will be overwritten. Are you sure you want to save?',
        ),
        onConfirm: () => {
          updateSla()
          showConfirmDialog.value.show = false
        },
      }
      return
    }
    updateSla()
  } else {
    createSla()
  }
}

const createSla = () => {
  slaPolicyListResource.insert.submit(
    {
      ...slaData.value,
      condition: convertToConditions({
        conditions: slaData.value.condition_json,
        fieldPrefix: 'doc',
      }),
      condition_json: JSON.stringify(slaData.value.condition_json),
    },
    {
      onSuccess(data) {
        toast.success(__('SLA policy created'))
        updateStep('view', data, true)
        getSlaResource.submit({
          doctype: 'CRM Service Level Agreement',
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

const renameSlaResource = createResource({
  url: 'frappe.client.rename_doc',
  makeParams() {
    return {
      doctype: 'CRM Service Level Agreement',
      old_name: step.value.data.name,
      new_name: slaData.value.sla_name,
    }
  },
})

const updateSla = async () => {
  await slaPolicyListResource.setValue.submit(
    {
      ...slaData.value,
      name: step.value.data.name,
      condition: useNewUI.value
        ? convertToConditions({
            conditions: slaData.value.condition_json,
            fieldPrefix: 'doc',
          })
        : slaData.value.condition,
      condition_json: useNewUI.value
        ? JSON.stringify(slaData.value.condition_json)
        : null,
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

  if (slaData.value.name !== slaData.value.sla_name) {
    await renameSlaResource.submit().catch(async (er) => {
      const error =
        er?.messages?.[0] || __('Some error occurred while renaming SLA policy')
      toast.error(error)
      // Reset assignment rule to previous state
      await getSlaResource.reload()
      isLoading.value = false
    })

    getSlaResource.submit({
      doctype: 'CRM Service Level Agreement',
      name: slaData.value.sla_name,
    })
  } else {
    await getSlaResource.reload()
  }

  toast.success(__('SLA policy updated'))
  slaPolicyListResource.reload()
}

watch(
  slaData,
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
  resetSlaDataErrors()
  disableSettingModalOutsideClick.value = false
})
</script>
