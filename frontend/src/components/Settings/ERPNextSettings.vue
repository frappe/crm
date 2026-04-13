<template>
  <SettingsLayoutBase
    :title="__('ERPNext Settings')"
    :description="__('Manage ERPNext integration settings')"
  >
    <template #title>
      <div class="flex gap-2 items-center">
        <h2 class="flex text-xl font-semibold leading-none h-5">
          {{ __('ERPNext Settings') }}
        </h2>
        <Tooltip text="View documentation">
          <a href="https://docs.frappe.io/crm/erpnext" target="_blank">
            <lucide-circle-question-mark class="h-4 w-4 text-ink-gray-6" />
          </a>
        </Tooltip>
      </div>
    </template>
    <template #header-actions>
      <div
        v-if="
          erpnextCRMSettingsResource.doc &&
          !erpnextCRMSettingsResource.get.loading &&
          erpnextCRMSettingsResource.doc.enabled
        "
        class="flex gap-2 items-center"
      >
        <Button
          v-if="isDisableButtonVisible"
          variant="subtle"
          @click="toggleEnable(erpnextCRMSettingsResource.doc.enabled)"
        >
          {{ __('Disable') }}
        </Button>
        <Button
          v-if="isUpdateButtonVisible"
          variant="solid"
          :loading="erpnextCRMSettingsResource.setValue.loading"
          :disabled="!isDirty || isDisabled"
          @click="saveSettings"
        >
          {{ __('Update') }}
        </Button>
      </div>
    </template>
    <template #content>
      <div
        v-if="
          erpnextCRMSettingsResource.get.loading ||
          erpnextCRMSettingsResource.isERPNextInstalled.loading ||
          (erpnextCRMSettingsResource.getExternalCompanies.loading &&
            !erpnextCRMSettingsResource.getExternalCompanies.fetched) ||
          !erpnextCRMSettingsResource.get.fetched
        "
        class="flex items-center justify-center mt-[35%]"
      >
        <LoadingIndicator class="size-6" />
      </div>
      <div v-else class="h-full">
        <div v-if="erpnextCRMSettingsResource.doc.enabled">
          <div
            v-if="!erpnextCRMSettingsResource.isERPNextInstalled.data"
            class="space-y-4"
          >
            <FormControl
              v-model="erpnextCRMSettingsResource.doc.erpnext_site_url"
              :label="__('Site URL')"
              type="text"
              placeholder="https://erpnext.example.com"
              required
              :description="
                __(
                  'ERPNext is not installed on this site either install it or enter the URL of your ERPNext site to connect',
                )
              "
              autocomplete="off"
            />
            <div class="grid grid-cols-2 gap-4">
              <FormControl
                v-model="erpnextCRMSettingsResource.doc.api_key"
                :label="__('API Key')"
                type="text"
                placeholder="9g3f7693gho2ih23hiuhsad"
                required
                autocomplete="off"
              />
              <FormControl
                v-model="erpnextCRMSettingsResource.doc.api_secret"
                :label="__('API Secret')"
                type="text"
                placeholder="o2ih23hiuhsado2ih23hiuhsad"
                required
                autocomplete="off"
              />
            </div>
            <Button
              v-if="
                !erpnextCRMSettingsResource.isERPNextInstalled.data &&
                areSiteSettingsChanged
              "
              variant="subtle"
              :disabled="
                erpnextCRMSettingsResource.getExternalCompanies.loading ||
                !erpnextCRMSettingsResource.doc.erpnext_site_url ||
                !erpnextCRMSettingsResource.doc.api_key ||
                !erpnextCRMSettingsResource.doc.api_secret
              "
              :loading="erpnextCRMSettingsResource.setValue.loading"
              @click="verifyConnection"
            >
              {{ __('Verify Connection') }}
            </Button>
          </div>
          <div
            v-if="
              !erpnextCRMSettingsResource.isERPNextInstalled.data &&
              isUpdateButtonVisible
            "
            class="h-px border-t my-4 border-outline-gray-modals"
          />
          <div
            v-if="
              erpnextCRMSettingsResource.isERPNextInstalled.data ||
              isUpdateButtonVisible
            "
            class="-mx-2"
          >
            <div class="flex items-center justify-between pb-3 px-2">
              <div class="flex flex-col">
                <div class="text-p-base font-medium text-ink-gray-7 truncate">
                  {{ __('Company Name') }}
                </div>
                <div class="text-p-sm text-ink-gray-5 truncate">
                  {{ __('Select your ERPNext company to connect with') }}
                </div>
              </div>
              <div class="w-48">
                <Autocomplete
                  v-if="!erpnextCRMSettingsResource.isERPNextInstalled.data"
                  :model-value="erpnextCRMSettingsResource.doc.erpnext_company"
                  :options="
                    erpnextCRMSettingsResource.getExternalCompanies.data?.map(
                      (company) => ({
                        label: company.company_name,
                        value: company.company_name,
                      }),
                    ) || []
                  "
                  required
                  class="pb-0.5"
                  @update:modelValue="
                    erpnextCRMSettingsResource.doc.erpnext_company =
                      $event?.value
                  "
                >
                  <template #footer>
                    <Button
                      :label="__('Refresh Companies')"
                      theme="gray"
                      variant="ghost"
                      class="w-full"
                      icon-left="refresh-cw"
                      :loading="
                        erpnextCRMSettingsResource.getExternalCompanies.loading
                      "
                      @click="
                        erpnextCRMSettingsResource.getExternalCompanies.submit()
                      "
                    />
                  </template>
                </Autocomplete>
                <Link
                  v-else
                  v-model="erpnextCRMSettingsResource.doc.erpnext_company"
                  :doc="'Company'"
                  :doctype="'Company'"
                  :placeholder="__('Select Company')"
                  class="w-48 flex-shrink-0"
                />
              </div>
            </div>
            <div class="h-px border-t border-outline-gray-modals" />
            <div class="flex items-center justify-between py-3 px-2">
              <div class="flex flex-col">
                <div class="text-p-base font-medium text-ink-gray-7 truncate">
                  {{ __('Auto Create Customer') }}
                </div>
                <div class="text-p-sm text-ink-gray-5 truncate">
                  {{
                    __(
                      'Create customer in ERPNext when the deal status is changed',
                    )
                  }}
                </div>
              </div>
              <div>
                <Switch
                  v-model="
                    erpnextCRMSettingsResource.doc
                      .create_customer_on_status_change
                  "
                  size="sm"
                />
              </div>
            </div>
            <div
              v-if="
                erpnextCRMSettingsResource.doc.create_customer_on_status_change
              "
            >
              <div class="flex items-center justify-between py-3 px-2 gap-4">
                <div class="flex flex-col">
                  <div class="text-p-base font-medium text-ink-gray-7">
                    {{ __('Deal Status') }}
                  </div>
                  <div class="text-p-sm text-ink-gray-5">
                    {{
                      __(
                        'Select the deal status to trigger the auto customer creation in ERPNext',
                      )
                    }}
                  </div>
                </div>
                <Link
                  v-model="erpnextCRMSettingsResource.doc.deal_status"
                  doctype="CRM Deal Status"
                  :placeholder="__('Won')"
                  :disabled="
                    !erpnextCRMSettingsResource.doc
                      .create_customer_on_status_change
                  "
                  class="w-48 flex-shrink-0"
                />
              </div>
            </div>
          </div>
        </div>
        <!--  Disabled state -->
        <div v-else class="relative flex h-full w-full justify-center">
          <div
            class="absolute left-1/2 flex w-64 -translate-x-1/2 flex-col items-center gap-3"
            :style="{ top: '35%' }"
          >
            <ERPNextIcon class="size-7.5 text-ink-gray-5" />
            <div class="flex flex-col items-center gap-1.5 text-center">
              <span class="text-lg font-medium text-ink-gray-8">
                {{ __('Connect ERPNext to Frappe CRM') }}
              </span>
              <span class="text-center text-p-base text-ink-gray-6">
                {{
                  __(
                    'Enable the integration to create quotations and auto create customers in ERPNext.',
                  )
                }}
              </span>
              <Button
                variant="solid"
                @click="erpnextCRMSettingsResource.doc.enabled = true"
              >
                {{ __('Enable') }}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import {
  Button,
  createDocumentResource,
  FormControl,
  LoadingIndicator,
  Switch,
  toast,
  Tooltip,
} from 'frappe-ui'
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import { computed, onMounted } from 'vue'
import Link from '../Controls/Link.vue'
import { globalStore } from '@/stores/global'

const { $dialog } = globalStore()

const erpnextCRMSettingsResource = createDocumentResource({
  doctype: 'ERPNext CRM Settings',
  name: 'ERPNext CRM Settings',
  whitelistedMethods: {
    isERPNextInstalled: 'is_erpnext_installed',
    getExternalCompanies: {
      method: 'get_external_companies',
      onSuccess(data) {
        if (!data.length) {
          toast.error(__('No companies found in the given site'))
        }
      },
    },
  },
  setValue: {
    onSuccess() {
      toast.success(__('Settings saved'))
    },
    onError(error) {
      const message = error?.messages?.[0] || __('Failed to save settings')
      toast.error(message)
    },
  },
})

const isDisabled = computed(() => {
  const data = erpnextCRMSettingsResource.doc

  const isSiteConfigValid =
    !erpnextCRMSettingsResource.isERPNextInstalled.data &&
    (!data.erpnext_site_url || !data.api_key || !data.api_secret)

  return isSiteConfigValid || !data.erpnext_company
})

const isDisableButtonVisible = computed(() => {
  const data = erpnextCRMSettingsResource.originalDoc
  return (
    data.erpnext_site_url ||
    data.api_key ||
    data.api_secret ||
    data.erpnext_company
  )
})

const isUpdateButtonVisible = computed(() => {
  const isERPNextInstalled = erpnextCRMSettingsResource.isERPNextInstalled.data
  return (
    (isDisableButtonVisible.value && !isERPNextInstalled) || isERPNextInstalled
  )
})

const areSiteSettingsChanged = computed(() => {
  const oldData = erpnextCRMSettingsResource.originalDoc
  const newData = erpnextCRMSettingsResource.doc
  return (
    oldData?.erpnext_site_url !== newData?.erpnext_site_url ||
    oldData?.api_key !== newData?.api_key ||
    oldData?.api_secret !== newData?.api_secret
  )
})

const isDirty = computed(() => {
  const oldData = erpnextCRMSettingsResource.originalDoc
  const newData = erpnextCRMSettingsResource.doc

  if (!oldData || !newData) return false

  const fields = [
    'enabled',
    'erpnext_site_url',
    'api_key',
    'api_secret',
    'erpnext_company',
    'create_customer_on_status_change',
    'deal_status',
  ]

  return fields.some((field) => oldData[field] !== newData[field])
})

const saveSettings = async () => {
  if (!validateData() || !validateSiteConnection()) return

  updateFields(
    {
      enabled: erpnextCRMSettingsResource.doc.enabled,
      is_erpnext_in_different_site:
        !erpnextCRMSettingsResource.isERPNextInstalled.data,
      create_customer_on_status_change:
        erpnextCRMSettingsResource.doc.create_customer_on_status_change,
      erpnext_company: erpnextCRMSettingsResource.doc.erpnext_company,
      deal_status: erpnextCRMSettingsResource.doc.deal_status,
      erpnext_site_url: erpnextCRMSettingsResource.doc.erpnext_site_url,
      api_key: erpnextCRMSettingsResource.doc.api_key,
      api_secret: erpnextCRMSettingsResource.doc.api_secret,
    },
    {
      onSuccess: async () => {
        if (!erpnextCRMSettingsResource.isERPNextInstalled.data) {
          await erpnextCRMSettingsResource.getExternalCompanies.submit()
        }
        await erpnextCRMSettingsResource.get.reload()
      },
    },
  )
}

const toggleEnable = (value) => {
  if (value) {
    $dialog({
      title: __('Disable ERPNext Integration'),
      message: __(
        'Create quotation button on deal page and auto customer creation on deal status change will be disabled. Are you sure?',
      ),
      actions: [
        {
          label: __('Disable'),
          variant: 'solid',
          theme: 'red',
          onClick: (close) => {
            updateFields('enabled', false)
            close()
          },
        },
      ],
    })
  } else {
    erpnextCRMSettingsResource.doc.enabled = true
  }
}

function verifyConnection() {
  if (!validateSiteConnection()) return

  updateFields(
    {
      enabled: erpnextCRMSettingsResource.doc.enabled,
      is_erpnext_in_different_site:
        !erpnextCRMSettingsResource.isERPNextInstalled.data,
      erpnext_site_url: erpnextCRMSettingsResource.doc.erpnext_site_url,
      api_key: erpnextCRMSettingsResource.doc.api_key,
      api_secret: erpnextCRMSettingsResource.doc.api_secret,
    },
    {
      onSuccess: () => {
        toast.success(__('Site connection validated'))
        if (!erpnextCRMSettingsResource.isERPNextInstalled.data) {
          erpnextCRMSettingsResource.getExternalCompanies.submit()
        }
      },
    },
  )
}

const validateSiteConnection = () => {
  if (erpnextCRMSettingsResource.isERPNextInstalled.data) return true

  const { erpnext_site_url, api_key, api_secret } =
    erpnextCRMSettingsResource.doc
  let error = ''

  if (!erpnext_site_url) {
    error = __('Site URL is required')
  } else {
    try {
      new URL(erpnext_site_url)
    } catch {
      error = __('Invalid Site URL')
    }
  }

  if (!error && !api_key) {
    error = __('API key is required')
  }
  if (!error && !api_secret) {
    error = __('API secret is required')
  }

  if (error) {
    toast.error(error)
    return false
  }
  return true
}

const validateData = () => {
  let error = ''

  if (!erpnextCRMSettingsResource.doc.erpnext_company) {
    error = __('Company name is required')
  } else if (
    erpnextCRMSettingsResource.doc.create_customer_on_status_change &&
    !erpnextCRMSettingsResource.doc.deal_status
  ) {
    error = __('Deal status is required')
  }

  if (error) {
    toast.error(error)
    return false
  }
  return true
}

function updateFields(fields, value, options) {
  let obj = {}

  if (typeof fields === 'object' && fields !== null) {
    obj = fields
    options = value
  } else {
    obj[fields] = value
  }

  erpnextCRMSettingsResource.setValue.submit(obj, options)
}

onMounted(async () => {
  // Call APIs one after another to avoid race conditions
  await erpnextCRMSettingsResource.get.submit()
  await erpnextCRMSettingsResource.isERPNextInstalled.submit(null, {
    onSuccess: (data) => {
      if (
        !data.message &&
        erpnextCRMSettingsResource.doc.enabled &&
        erpnextCRMSettingsResource.doc.erpnext_site_url &&
        erpnextCRMSettingsResource.doc.api_key &&
        erpnextCRMSettingsResource.doc.api_secret
      ) {
        erpnextCRMSettingsResource.getExternalCompanies.submit()
      }
    },
  })
})
</script>
