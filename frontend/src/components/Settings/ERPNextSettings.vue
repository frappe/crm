<template>
  <SettingsLayoutBase
    :title="__('ERPNext Settings')"
    :description="__('Manage ERPNext integration settings')"
  >
    <template #header-actions>
      <div
        v-if="
          !erpnextCrmSettingsResource.loading && erpnextCrmSettingsData.enabled
        "
        class="flex gap-4 items-center"
      >
        <div
          class="flex items-center gap-2"
          @click="toggleEnable(erpnextCrmSettingsData.enabled)"
        >
          <Switch :model-value="erpnextCrmSettingsData.enabled" />
          <span
            class="text-sm text-ink-gray-7 font-medium cursor-pointer select-none"
            >{{ __('Enabled') }}</span
          >
        </div>
        <Button
          variant="solid"
          @click="saveSettings"
          :loading="saveErpnextCrmSettings.loading"
          :disabled="!isDirty || isDisabled"
        >
          {{ __('Update') }}
        </Button>
      </div>
    </template>
    <template #content>
      <div
        v-if="
          (erpnextCrmSettingsResource.loading || isErpnextInstalled.loading) &&
          !erpnextCrmSettingsResource.data
        "
        class="flex items-center justify-center mt-[35%]"
      >
        <LoadingIndicator class="size-6" />
      </div>
      <div v-else class="h-full">
        <div v-if="erpnextCrmSettingsData.enabled" class="space-y-4">
          <div
            v-if="erpnextCrmSettingsData.isErpnextInDifferentSite"
            class="space-y-4"
          >
            <FormControl
              v-model="erpnextCrmSettingsData.erpnextSiteUrl"
              :label="__('Site URL')"
              type="text"
              placeholder="https://erpnext.example.com"
              required
              :description="
                __(
                  'ERPNext is not installed on this site. Enter the URL of your ERPNext site to connect it with this CRM',
                )
              "
            />
            <div class="grid grid-cols-2 gap-4">
              <FormControl
                v-model="erpnextCrmSettingsData.apiKey"
                :label="__('API Key')"
                type="text"
                placeholder="9g3f7693gho2ih23hiuhsad"
                required
              />
              <FormControl
                v-model="erpnextCrmSettingsData.apiSecret"
                :label="__('API Secret')"
                type="text"
                placeholder="o2ih23hiuhsado2ih23hiuhsad"
                required
              />
            </div>
            <div class="flex items-center justify-between gap-2">
              <Button
                v-if="erpnextCrmSettingsData.isErpnextInDifferentSite"
                variant="subtle"
                @click="
                  getExternalCompanies.submit({
                    site_url: erpnextCrmSettingsData.erpnextSiteUrl,
                    api_key: erpnextCrmSettingsData.apiKey,
                    api_secret: erpnextCrmSettingsData.apiSecret,
                  })
                "
                :disabled="
                  getExternalCompanies.loading ||
                  !erpnextCrmSettingsData.erpnextSiteUrl ||
                  !erpnextCrmSettingsData.apiKey ||
                  !erpnextCrmSettingsData.apiSecret
                "
                icon-left="download"
              >
                {{ __('Fetch Companies') }}
              </Button>
            </div>
          </div>
          <div
            v-if="
              getExternalCompanies.data?.length &&
              erpnextCrmSettingsData.isErpnextInDifferentSite
            "
            class="h-px border-t mb-2 border-outline-gray-modals"
          />
          <div
            v-if="
              getExternalCompanies.data?.length ||
              !erpnextCrmSettingsData.isErpnextInDifferentSite
            "
            class="-mx-2"
          >
            <div class="flex items-center justify-between pb-3 px-2">
              <div class="flex flex-col">
                <div class="text-p-base font-medium text-ink-gray-7 truncate">
                  {{ __('Company Name') }}
                </div>
                <div class="text-p-sm text-ink-gray-5 truncate">
                  {{ __('Select the company name that is used in ERPNext') }}
                </div>
              </div>
              <div class="w-48">
                <Autocomplete
                  v-if="erpnextCrmSettingsData.isErpnextInDifferentSite"
                  :model-value="erpnextCrmSettingsData.erpnextCompany"
                  @update:modelValue="
                    erpnextCrmSettingsData.erpnextCompany = $event?.value
                  "
                  :options="
                    getExternalCompanies.data?.map((company) => ({
                      label: company.company_name,
                      value: company.company_name,
                    })) || []
                  "
                  required
                  class="pb-0.5"
                  :disabled="!getExternalCompanies.data?.length"
                />
                <Link
                  v-else
                  :doc="'Company'"
                  :doctype="'Company'"
                  :placeholder="__('Select Company')"
                  v-model="erpnextCrmSettingsData.erpnextCompany"
                  class="w-48 flex-shrink-0"
                />
              </div>
            </div>
            <div class="h-px border-t mx-2 border-outline-gray-modals" />

            <div class="flex items-center justify-between py-3 px-2">
              <div class="flex flex-col">
                <div class="text-p-base font-medium text-ink-gray-7 truncate">
                  {{ __('Create Customer On Deal Status Change') }}
                </div>
                <div class="text-p-sm text-ink-gray-5 truncate">
                  {{
                    __(
                      'Create customer in ERPNext when a deal status is changed',
                    )
                  }}
                </div>
              </div>
              <div>
                <Switch
                  size="sm"
                  v-model="erpnextCrmSettingsData.createCustomerOnStatusChange"
                />
              </div>
            </div>
            <div v-if="erpnextCrmSettingsData.createCustomerOnStatusChange">
              <div class="h-px border-t mx-2 border-outline-gray-modals" />

              <div class="flex items-center justify-between py-3 px-2 gap-4">
                <div class="flex flex-col">
                  <div class="text-p-base font-medium text-ink-gray-7">
                    {{ __('Deal Status') }}
                  </div>
                  <div class="text-p-sm text-ink-gray-5">
                    {{
                      __(
                        'Select the deal status to trigger the customer creation in ERPNext',
                      )
                    }}
                  </div>
                </div>
                <Link
                  v-model="erpnextCrmSettingsData.dealStatus"
                  doctype="CRM Deal Status"
                  :placeholder="__('Won')"
                  :disabled="
                    !erpnextCrmSettingsData.createCustomerOnStatusChange
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
                    'Enable the ERPNext integration to configure it for your CRM.',
                  )
                }}
              </span>
              <Button
                variant="solid"
                @click="erpnextCrmSettingsData.enabled = true"
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
  createResource,
  FormControl,
  LoadingIndicator,
  Switch,
  toast,
} from 'frappe-ui'
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import { computed, ref } from 'vue'
import Link from '../Controls/Link.vue'
import { globalStore } from '@/stores/global'

const { $dialog } = globalStore()

const transformData = (data) => {
  if (!data) return {}
  return {
    enabled: Boolean(data.enabled),
    isErpnextInDifferentSite: Boolean(data.is_erpnext_in_different_site),
    createCustomerOnStatusChange: Boolean(
      data.create_customer_on_status_change,
    ),
    erpnextCompany: data.erpnext_company,
    dealStatus: data.deal_status,
    erpnextSiteUrl: data.erpnext_site_url,
    apiKey: data.api_key,
    apiSecret: data.api_secret,
  }
}

const erpnextCrmSettingsData = ref({
  enabled: false,
  isErpnextInDifferentSite: false,
  createCustomerOnStatusChange: false,
  erpnextCompany: '',
  dealStatus: '',
  erpnextSiteUrl: '',
  apiKey: '',
  apiSecret: '',
})

const erpnextCrmSettingsResource = createResource({
  url: 'frappe.client.get',
  params: {
    doctype: 'ERPNext CRM Settings',
    name: 'ERPNext CRM Settings',
  },
  auto: true,
  onSuccess(data) {
    erpnextCrmSettingsData.value = transformData(data)
    isErpnextInstalled.submit()
    if (data.is_erpnext_in_different_site) {
      getExternalCompanies.submit({
        site_url: data.erpnext_site_url,
        api_key: data.api_key,
        api_secret: data.api_secret,
      })
    }
  },
})

const saveErpnextCrmSettings = createResource({
  url: 'frappe.client.set_value',
  makeParams: () => {
    return {
      doctype: 'ERPNext CRM Settings',
      name: 'ERPNext CRM Settings',
      fieldname: {
        enabled: erpnextCrmSettingsData.value.enabled,
        is_erpnext_in_different_site:
          erpnextCrmSettingsData.value.isErpnextInDifferentSite,
        create_customer_on_status_change:
          erpnextCrmSettingsData.value.createCustomerOnStatusChange,
        erpnext_company: erpnextCrmSettingsData.value.erpnextCompany,
        deal_status: erpnextCrmSettingsData.value.dealStatus,
        erpnext_site_url: erpnextCrmSettingsData.value.erpnextSiteUrl,
        api_key: erpnextCrmSettingsData.value.apiKey,
        api_secret: erpnextCrmSettingsData.value.apiSecret,
      },
    }
  },
  onSuccess() {
    erpnextCrmSettingsResource.reload()
    toast.success(__('Settings saved'))
  },
  onError(err) {
    let message =
      err?.messages?.[0] || __('Failed to update ERPNext CRM Settings')
    if (message.includes('custom field')) {
      message = __('Error connecting to ERPNext, check your API key & secret')
    }
    toast.error(message)
  },
})

const isErpnextInstalled = createResource({
  url: 'crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings.is_erpnext_installed',
  onSuccess(data) {
    erpnextCrmSettingsData.value.isErpnextInDifferentSite = !data
  },
})

const getExternalCompanies = createResource({
  url: 'crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings.get_external_companies',
  onSuccess(data) {
    if (data?.length === 0) {
      return toast.error(
        __(
          'No companies found in this remote ERPNext site, please check your API key & secret',
        ),
      )
    }
  },
  onError() {
    toast.error(
      __('Failed to get external companies, check your API key & secret'),
    )
  },
})

const isDirty = computed(() => {
  const oldData = transformData(erpnextCrmSettingsResource.data)
  const newData = erpnextCrmSettingsData.value
  return JSON.stringify(oldData) !== JSON.stringify(newData)
})

const isDisabled = computed(() => {
  return (
    (erpnextCrmSettingsData.value.isErpnextInDifferentSite &&
      (!erpnextCrmSettingsData.value.erpnextSiteUrl ||
        !erpnextCrmSettingsData.value.apiKey ||
        !erpnextCrmSettingsData.value.apiSecret)) ||
    (erpnextCrmSettingsData.value.createCustomerOnStatusChange &&
      !erpnextCrmSettingsData.value.dealStatus) ||
    !erpnextCrmSettingsData.value.erpnextCompany
  )
})

const saveSettings = () => {
  if (
    erpnextCrmSettingsData.value.createCustomerOnStatusChange &&
    !erpnextCrmSettingsData.value.dealStatus
  ) {
    toast.error(__('Deal status is required'))
    return
  }
  if (!erpnextCrmSettingsData.value.erpnextCompany) {
    toast.error(__('Company name is required'))
    return
  }
  if (erpnextCrmSettingsData.value.isErpnextInDifferentSite) {
    if (!erpnextCrmSettingsData.value.erpnextSiteUrl) {
      toast.error(__('Site URL is required'))
      return
    }

    let url = erpnextCrmSettingsData.value.erpnextSiteUrl

    try {
      new URL(url)
    } catch (e) {
      toast.error(__('Invalid Site URL'))
      return
    }
    if (!erpnextCrmSettingsData.value.apiKey) {
      toast.error(__('API key is required'))
      return
    }
    if (!erpnextCrmSettingsData.value.apiSecret) {
      toast.error(__('API secret is required'))
      return
    }
  }
  saveErpnextCrmSettings.submit()
}

const toggleEnable = (value) => {
  if (value) {
    $dialog({
      title: __('Disable ERPNext Integration'),
      message: __('Are you sure you want to disable ERPNext integration?'),
      actions: [
        {
          label: __('Disable'),
          variant: 'solid',
          theme: 'red',
          onClick: (close) => {
            erpnextCrmSettingsData.value.enabled = false
            saveErpnextCrmSettings.submit()
            close()
          },
        },
      ],
    })
  } else {
    erpnextCrmSettingsData.value.enabled = true
  }
}
</script>
