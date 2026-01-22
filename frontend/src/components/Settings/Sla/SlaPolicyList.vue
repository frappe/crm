<template>
  <SettingsLayoutBase
    :title="__('SLA policies')"
    :description="__('Manage your service level agreement policies')"
  >
    <template #header-actions>
      <Button
        :label="__('New')"
        variant="solid"
        icon-left="plus"
        @click="createNewSlaPolicy"
      />
    </template>
    <template
      v-if="slaPolicyListResource.data?.length > 9 || slaSearchQuery.length"
      #header-bottom
    >
      <div class="relative">
        <Input
          :model-value="slaSearchQuery"
          @input="slaSearchQuery = $event"
          :placeholder="__('Search')"
          type="text"
          class="bg-surface-gray-2 hover:bg-surface-gray-2 focus:ring-0 border-outline-gray-2 rounded"
          icon-left="search"
          debounce="300"
          inputClass="p-4 pr-12"
        />
        <Button
          v-if="slaSearchQuery"
          icon="x"
          variant="ghost"
          @click="slaSearchQuery = ''"
          class="absolute right-1 top-1/2 -translate-y-1/2"
        />
      </div>
    </template>
    <template #content>
      <div
        v-if="
          slaPolicyListResource.list.loading && !slaPolicyListResource.list.data
        "
        class="flex items-center justify-center mt-12"
      >
        <LoadingIndicator class="w-4" />
      </div>
      <div v-else class="h-full">
        <EmptyState
          v-if="
            !slaPolicyListResource.list.loading &&
            !slaPolicyListResource.list.data?.length
          "
          title="No SLA found"
          description="Add one to get started."
          :icon="ShieldCheck"
        />
        <div v-else class="-ml-2">
          <div
            class="grid grid-cols-7 items-center gap-3 text-sm text-gray-600 ml-2"
          >
            <div class="col-span-5">
              {{ __('Policy Name') }}
            </div>
            <div class="col-span-1">{{ __('Apply on') }}</div>
            <div class="col-span-1">{{ __('Enabled') }}</div>
          </div>
          <hr class="mt-2 mx-2 border-outline-gray-2" />
          <div
            v-for="(sla, index) in slaPolicyListResource.data"
            :key="sla.name"
          >
            <div
              class="grid grid-cols-7 items-center gap-4 cursor-pointer hover:bg-surface-menu-bar rounded"
            >
              <div
                @click="updateStep('view', sla, true)"
                class="w-full pl-2 col-span-5 flex items-center h-14 gap-2"
              >
                <div class="text-base text-ink-gray-7 font-medium truncate">
                  {{ sla.name }}
                </div>
                <Badge v-if="sla.default" color="gray" size="sm">Default</Badge>
              </div>
              <div class="col-span-1 text-ink-gray-8 text-sm">
                {{ sla.apply_on == 'CRM Lead' ? 'Lead' : 'Deal' }}
              </div>
              <div class="flex justify-between items-center w-full pr-2">
                <div>
                  <Switch
                    size="sm"
                    :modelValue="sla.enabled"
                    @update:modelValue="onToggle(sla)"
                  />
                </div>
                <div>
                  <Dropdown placement="right" :options="dropdownOptions(sla)">
                    <Button
                      icon="more-horizontal"
                      variant="ghost"
                      @click="isConfirmingDelete = false"
                    />
                  </Dropdown>
                </div>
              </div>
            </div>
            <hr
              v-if="index !== slaPolicyListResource.list.data.length - 1"
              class="mx-2 border-outline-gray-2"
            />
            <Dialog
              :options="{ title: __('Duplicate SLA policy') }"
              v-model="duplicateDialog.show"
            >
              <template #body-content>
                <div class="flex flex-col gap-4">
                  <FormControl
                    :label="__('New SLA policy name')"
                    type="text"
                    v-model="duplicateDialog.name"
                    maxlength="100"
                  />
                </div>
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
                    @click="() => duplicate(sla)"
                  />
                </div>
              </template>
            </Dialog>
          </div>
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import ShieldCheck from '~icons/lucide/shield-check'
import {
  Badge,
  Button,
  createResource,
  Dialog,
  Dropdown,
  FormControl,
  LoadingIndicator,
  Switch,
  toast,
} from 'frappe-ui'
import { ConfirmDelete } from '@/utils'
import { resetSlaData } from './utils'
import { inject, ref, watch } from 'vue'

const slaPolicyListResource = inject('slaPolicyListResource')
const updateStep = inject('updateStep')
const slaSearchQuery = inject('slaSearchQuery')

function createNewSlaPolicy() {
  resetSlaData()
  updateStep('view', null)
}

const duplicateDialog = ref({
  show: false,
  name: '',
})

const isConfirmingDelete = ref(false)

const dropdownOptions = (sla) => [
  {
    label: __('Duplicate'),
    onClick: () => {
      duplicateDialog.value = {
        show: true,
        name: sla.name + ' (Copy)',
      }
    },
    icon: 'copy',
  },
  ...ConfirmDelete({
    onConfirmDelete: () => deleteSla(sla),
    isConfirmingDelete,
  }),
]

const duplicate = (sla) => {
  createResource({
    url: 'frappe.client.get',
    params: {
      doctype: 'CRM Service Level Agreement',
      name: sla.name,
    },
    onSuccess: (data) => {
      createResource({
        url: 'frappe.client.insert',
        params: {
          doc: {
            ...data,
            default: false,
            sla_name: duplicateDialog.value.name,
          },
        },
        auto: true,
        onSuccess(newSlaData) {
          slaPolicyListResource.reload()
          toast.success(__('SLA policy duplicated'))
          duplicateDialog.value = {
            show: false,
            name: '',
          }
          resetSlaData()
          setTimeout(() => {
            updateStep('view', newSlaData, true)
          }, 250)
        },
      })
    },
    auto: true,
  })
}

const deleteSla = (sla) => {
  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true
    return
  }

  slaPolicyListResource.delete.submit(sla.name, {
    onSuccess: () => {
      toast.success(__('SLA policy deleted'))
    },
    onError: (err) => {
      const message =
        err.messages?.[0] || __('Something went wrong, try again later')
      toast.error(message)
    },
  })
}

const onToggle = (sla) => {
  if (sla.default) {
    toast.error(__('SLA set as default cannot be disabled'))
    return
  }
  slaPolicyListResource.setValue.submit(
    {
      name: sla.name,
      enabled: !sla.enabled,
    },
    {
      onSuccess: () => {
        toast.success(__('SLA policy status updated'))
      },
    },
  )
}

watch(slaSearchQuery, (newValue) => {
  slaPolicyListResource.filters = {
    name: ['like', `%${newValue}%`],
  }
  if (!newValue) {
    slaPolicyListResource.start = 0
    slaPolicyListResource.pageLength = 10
  }
  slaPolicyListResource.reload()
})
</script>
