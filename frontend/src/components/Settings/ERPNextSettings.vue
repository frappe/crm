<template>
  <SettingsLayoutBase
    :title="__('ERPNext Settings')"
    :description="__('Manage ERPNext integration settings')"
  >
    <template #title>
      <div class="flex gap-2 items-center">
        <h2 class="flex text-2xl-semibold leading-none h-5">
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
            class="h-px border-t my-4 border-outline-elevation-2"
          />
          <div
            v-if="
              erpnextCRMSettingsResource.isERPNextInstalled.data ||
              isUpdateButtonVisible
            "
            class="-mx-2"
          >
            <div
              v-if="erpnextCRMSettingsResource.isERPNextInstalled.data"
              class="flex gap-5 border-b border-outline-elevation-2 px-2 mb-3"
              role="tablist"
            >
              <button
                v-for="tab in settingsTabs"
                :key="tab.name"
                class="border-b-2 pb-2 text-p-sm"
                :class="
                  activeSettingsTab === tab.name
                    ? 'border-ink-gray-8 text-ink-gray-8'
                    : 'border-transparent text-ink-gray-5'
                "
                role="tab"
                :aria-selected="activeSettingsTab === tab.name"
                @click="activeSettingsTab = tab.name"
              >
                {{ __(tab.label) }}
              </button>
            </div>
            <div v-show="activeSettingsTab === 'general'">
              <div class="flex items-center justify-between pb-3 px-2">
                <div class="flex flex-col">
                  <div class="text-p-base-medium text-ink-gray-7 truncate">
                    {{ __('Company Name') }}
                  </div>
                  <div class="text-p-sm text-ink-gray-5 truncate">
                    {{ __('Select your ERPNext company to connect with') }}
                  </div>
                </div>
                <div class="w-48">
                  <Autocomplete
                    v-if="!erpnextCRMSettingsResource.isERPNextInstalled.data"
                    :model-value="
                      erpnextCRMSettingsResource.doc.erpnext_company
                    "
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
                        icon-left="lucide-refresh-cw"
                        :loading="
                          erpnextCRMSettingsResource.getExternalCompanies
                            .loading
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
              <div
                v-if="erpnextCRMSettingsResource.isERPNextInstalled.data"
                class="h-px border-t border-outline-elevation-2"
              />
              <div
                v-if="erpnextCRMSettingsResource.isERPNextInstalled.data"
                class="flex items-center justify-between py-3 px-2 gap-4"
              >
                <div class="flex flex-col">
                  <div class="text-p-base-medium text-ink-gray-7 truncate">
                    {{ __('Bidirectional Product Sync') }}
                  </div>
                  <div class="text-p-sm text-ink-gray-5">
                    {{
                      __(
                        'ERPNext Items always sync into CRM Products. Turn this on to also sync CRM Product changes back to ERPNext Items.',
                      )
                    }}
                  </div>
                </div>
                <div>
                  <Switch
                    v-model="erpnextCRMSettingsResource.doc.sync_products"
                    size="sm"
                    @update:modelValue="
                      (v) =>
                        capture('erpnext_product_sync_toggled', { enabled: v })
                    "
                  />
                </div>
              </div>
              <div
                v-if="erpnextCRMSettingsResource.isERPNextInstalled.data"
                class="h-px border-t border-outline-elevation-2"
              />
              <div
                v-if="erpnextCRMSettingsResource.isERPNextInstalled.data"
                class="flex items-center justify-between py-3 px-2 gap-4"
              >
                <div class="flex flex-col">
                  <div class="text-p-base-medium text-ink-gray-7 truncate">
                    {{ __('Manual Sync') }}
                  </div>
                  <div class="text-p-sm text-ink-gray-5">
                    {{
                      erpnextCRMSettingsResource.doc.sync_products
                        ? __(
                            'Run a manual bi-directional sync between ERPNext Items and CRM Products.',
                          )
                        : __(
                            'Run a manual synchronization to pull the latest Items from ERPNext.',
                          )
                    }}
                  </div>
                </div>
                <Button
                  variant="subtle"
                  icon-left="lucide-refresh-cw"
                  :loading="erpnextCRMSettingsResource.runProductSync.loading"
                  @click="runProductSync"
                >
                  {{ __('Sync Now') }}
                </Button>
              </div>
              <div class="h-px border-t border-outline-elevation-2" />
              <div class="flex items-center justify-between py-3 px-2">
                <div class="flex flex-col">
                  <div class="text-p-base-medium text-ink-gray-7 truncate">
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
              <div class="h-px border-t border-outline-elevation-2" />
              <div
                v-if="
                  erpnextCRMSettingsResource.doc
                    .create_customer_on_status_change
                "
              >
                <div class="flex items-center justify-between py-3 px-2 gap-4">
                  <div class="flex flex-col">
                    <div class="text-p-base-medium text-ink-gray-7">
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
            <div
              v-if="erpnextCRMSettingsResource.isERPNextInstalled.data"
              v-show="activeSettingsTab === 'logs'"
              class="px-2"
            >
              <div
                v-if="productSyncStatus.loading"
                class="flex items-center justify-center py-10"
              >
                <LoadingIndicator class="size-5" />
              </div>
              <div v-else class="flex flex-col gap-2">
                <div
                  class="flex gap-5 border-b border-outline-elevation-2 overflow-x-auto"
                  role="tablist"
                >
                  <button
                    v-for="section in productSyncSections"
                    :key="section.name"
                    class="flex items-center gap-1 whitespace-nowrap border-b-2 px-0 pb-2 text-p-sm"
                    :class="
                      activeProductSyncLogTab === section.name
                        ? 'border-ink-gray-8 text-ink-gray-8'
                        : 'border-transparent text-ink-gray-5'
                    "
                    role="tab"
                    :aria-selected="activeProductSyncLogTab === section.name"
                    @click="activeProductSyncLogTab = section.name"
                  >
                    <span>{{ __(section.label) }}</span>
                    <span
                      class="rounded bg-surface-gray-2 px-1.5 text-xs text-ink-gray-6"
                    >
                      {{ section.count }}
                    </span>
                  </button>
                </div>
                <div
                  v-if="activeProductSyncLogTab === 'failed' && unsyncedSummary"
                  class="rounded bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-6"
                >
                  {{ unsyncedSummary }}
                </div>
                <div
                  v-if="!currentProductSyncRows.length"
                  class="rounded border border-outline-elevation-2 px-3 py-2 text-p-sm text-ink-gray-5"
                >
                  {{ __(currentProductSyncSection.emptyLabel) }}
                </div>
                <div v-else class="flex flex-col">
                  <div
                    v-for="row in currentProductSyncRows"
                    :key="row.name"
                    class="flex items-start justify-between gap-2 border-b border-outline-elevation-2 py-2 last:border-b-0"
                  >
                    <div class="min-w-0">
                      <a
                        v-if="getDeskUrl(row)"
                        :href="getDeskUrl(row)"
                        target="_blank"
                        rel="noopener noreferrer"
                        class="inline-flex max-w-full items-center gap-1 text-p-sm-medium text-ink-gray-8 hover:underline"
                      >
                        <span class="truncate">{{ getSyncRowName(row) }}</span>
                        <lucide-square-arrow-out-up-right
                          class="size-3.5 shrink-0 text-ink-gray-6"
                        />
                      </a>
                      <div
                        v-else
                        class="truncate text-p-sm-medium text-ink-gray-8"
                      >
                        {{ getSyncRowName(row) }}
                      </div>
                      <div
                        v-if="isSyncedDocumentLog"
                        class="mt-0.5 flex flex-wrap gap-x-3 gap-y-1"
                      >
                        <span
                          v-if="getSyncRowGroup(row)"
                          class="text-p-sm text-ink-gray-5"
                        >
                          {{ __('Item Group') }}: {{ getSyncRowGroup(row) }}
                        </span>
                        <span class="text-p-sm text-ink-gray-5">
                          {{ __('ID') }}: {{ getSyncRowId(row) }}
                        </span>
                      </div>
                      <div v-else class="truncate text-p-sm text-ink-gray-5">
                        {{ row.detail || row.kind }}
                      </div>
                    </div>
                    <div
                      v-if="!isSyncedDocumentLog"
                      class="shrink-0 text-p-sm text-ink-gray-5"
                    >
                      {{ getSyncRowMeta(row) }}
                    </div>
                  </div>
                </div>
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
              <span class="text-lg-medium text-ink-gray-8">
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
  createResource,
  FormControl,
  LoadingIndicator,
  Switch,
  toast,
  Tooltip,
} from 'frappe-ui'
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import Link from '../Controls/Link.vue'
import { globalStore } from '@/stores/global'
import { formatDate } from '@/utils'
import { useTelemetry } from 'frappe-ui/frappe'

const { $dialog, $socket } = globalStore()
const { capture } = useTelemetry()

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
    runProductSync: {
      method: 'run_product_sync',
      onSuccess() {
        toast.success(__('Product sync started.'))
        productSyncStatus.submit()
      },
      onError(error) {
        toast.error(error?.messages?.[0] || __('Failed to start sync'))
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

const activeSettingsTab = ref('general')
const activeProductSyncLogTab = ref('products')

const settingsTabs = [
  { name: 'general', label: 'General Settings' },
  { name: 'logs', label: 'Logs' },
]

const productSyncStatus = createResource({
  url: 'crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings.get_product_sync_status',
})

const productSyncSections = computed(() => {
  const data = productSyncStatus.data || {}
  return [
    getProductSyncSection('products', 'Products', 'No CRM Products'),
    getProductSyncSection('items', 'Items', 'No synced ERPNext Items'),
    getProductSyncSection('failed', 'Failed Logs', 'No failed syncs'),
  ].map((section) => ({
    ...section,
    rows: data[section.name]?.rows || data[section.name] || [],
    count: data[section.name]?.count ?? data[section.name]?.length ?? 0,
  }))
})

const currentProductSyncSection = computed(
  () =>
    productSyncSections.value.find(
      (section) => section.name === activeProductSyncLogTab.value,
    ) || productSyncSections.value[0],
)

const currentProductSyncRows = computed(
  () => currentProductSyncSection.value?.rows || [],
)

const isSyncedDocumentLog = computed(() =>
  ['products', 'items'].includes(activeProductSyncLogTab.value),
)

const unsyncedSummary = computed(() => {
  const data = productSyncStatus.data?.unsynced
  if (!data) return ''
  const parts = []
  if (data.items) {
    parts.push(`${data.items} ${data.items === 1 ? __('item') : __('items')}`)
  }
  if (data.sync_products && data.products) {
    parts.push(
      `${data.products} ${data.products === 1 ? __('product') : __('products')}`,
    )
  }
  if (!parts.length) return ''
  return __('{0} not yet synced', [parts.join(__(' and '))])
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
    'sync_products',
  ]

  return fields.some((field) => oldData[field] !== newData[field])
})

const saveSettings = async () => {
  if (!validateData() || !validateSiteConnection()) return

  const wasEnabled = !!erpnextCRMSettingsResource.originalDoc?.enabled

  updateFields(
    {
      enabled: erpnextCRMSettingsResource.doc.enabled,
      is_erpnext_in_different_site:
        !erpnextCRMSettingsResource.isERPNextInstalled.data,
      create_customer_on_status_change:
        erpnextCRMSettingsResource.doc.create_customer_on_status_change,
      sync_products: erpnextCRMSettingsResource.doc.sync_products,
      erpnext_company: erpnextCRMSettingsResource.doc.erpnext_company,
      deal_status: erpnextCRMSettingsResource.doc.deal_status,
      erpnext_site_url: erpnextCRMSettingsResource.doc.erpnext_site_url,
      api_key: erpnextCRMSettingsResource.doc.api_key,
      api_secret: erpnextCRMSettingsResource.doc.api_secret,
    },
    {
      onSuccess: async () => {
        if (erpnextCRMSettingsResource.doc.enabled && !wasEnabled) {
          capture('erpnext_integration_enabled')
        }
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

async function runProductSync() {
  capture('erpnext_sync_now_clicked')
  if (
    erpnextCRMSettingsResource.originalDoc?.sync_products !==
    erpnextCRMSettingsResource.doc.sync_products
  ) {
    await updateFields(
      'sync_products',
      erpnextCRMSettingsResource.doc.sync_products,
    )
  }
  await erpnextCRMSettingsResource.runProductSync.submit()
}

function getProductSyncSection(name, label, emptyLabel) {
  return { name, label, emptyLabel }
}

function getSyncRowName(row) {
  return row.product_name || row.item_name || row.product || row.name
}

function getSyncRowMeta(row) {
  if (activeProductSyncLogTab.value === 'products') return row.erpnext_item_code
  if (activeProductSyncLogTab.value === 'items') return row.crm_product_code
  return row.detected_on ? formatDate(row.detected_on) : row.kind || ''
}

function getSyncRowGroup(row) {
  return row.item_group
}

function getSyncRowId(row) {
  if (activeProductSyncLogTab.value === 'products')
    return row.product_code || row.name
  if (activeProductSyncLogTab.value === 'items')
    return row.item_code || row.name
  return row.product || row.name
}

function getDeskUrl(row) {
  const doctype = getDeskDoctype()
  if (!doctype || !row.name) return ''
  return `${window.location.origin}/app/${doctype}/${encodeURIComponent(row.name)}`
}

function getDeskDoctype() {
  if (activeProductSyncLogTab.value === 'products') return 'crm-product'
  if (activeProductSyncLogTab.value === 'items') return 'item'
  return ''
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

  return erpnextCRMSettingsResource.setValue.submit(obj, options)
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
  if (
    erpnextCRMSettingsResource.isERPNextInstalled.data &&
    erpnextCRMSettingsResource.doc.enabled
  ) {
    productSyncStatus.submit()
  }
})

// Fetch logs lazily when the tab is opened (e.g. after enabling in the same session)
watch(activeSettingsTab, (tab) => {
  if (
    tab === 'logs' &&
    erpnextCRMSettingsResource.isERPNextInstalled.data &&
    !productSyncStatus.fetched
  ) {
    productSyncStatus.submit()
  }
})

// The sync runs in a background job; refresh logs when it signals completion
function onSyncComplete() {
  if (erpnextCRMSettingsResource.isERPNextInstalled.data) {
    productSyncStatus.submit()
  }
}
onMounted(() => $socket.on('crm_product_sync_complete', onSyncComplete))
onBeforeUnmount(() => $socket.off('crm_product_sync_complete', onSyncComplete))
</script>
