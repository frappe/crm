<template>
  <SettingsLayoutBase
    :title="__('SLA Policies')"
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
        <div
          v-if="
            !slaPolicyListResource.list.loading &&
            !slaPolicyListResource.list.data?.length
          "
          class="flex flex-col items-center justify-center gap-4 h-full"
        >
          <div
            class="p-4 size-14.5 rounded-full bg-surface-gray-1 flex justify-center items-center"
          >
            <ShieldCheck class="size-6 text-ink-gray-6" />
          </div>
          <div class="flex flex-col items-center gap-1">
            <div class="text-base font-medium text-ink-gray-6">
              {{ __('No SLA found') }}
            </div>
            <div class="text-p-sm text-ink-gray-5 max-w-60 text-center">
              {{ __('Add one to get started.') }}
            </div>
          </div>
          <Button
            :label="__('New')"
            variant="outline"
            icon-left="plus"
            @click="createNewSlaPolicy()"
          />
        </div>
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
          <hr class="mt-2 mx-2" />
          <div
            v-for="(sla, index) in slaPolicyListResource.data"
            :key="sla.name"
          >
            <div
              class="grid grid-cols-7 items-center gap-4 cursor-pointer hover:bg-surface-menu-bar rounded"
            >
              <div
                @click="updateStep('view', sla, true)"
                class="w-full pl-2 col-span-5 flex flex-col justify-center h-14"
              >
                <div
                  class="text-base text-ink-gray-7 font-medium flex items-center gap-2"
                >
                  {{ sla.name }}
                  <Badge v-if="sla.default" color="gray" size="sm"
                    >Default</Badge
                  >
                </div>
                <div
                  v-if="sla.description && sla.description.length > 0"
                  class="text-sm w-full text-ink-gray-5 mt-1 truncate"
                >
                  {{ sla.description }}
                </div>
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
              class="mx-2"
            />
            <Dialog
              :options="{ title: __('Duplicate SLA Policy') }"
              v-model="duplicateDialog.show"
            >
              <template #body-content>
                <div class="flex flex-col gap-4">
                  <FormControl
                    :label="__('New SLA Policy Name')"
                    type="text"
                    v-model="duplicateDialog.name"
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
import SettingsLayoutBase from '../../Layouts/SettingsLayoutBase.vue'
import { inject, ref } from 'vue'
import ShieldCheck from '~icons/lucide/shield-check'
import { ConfirmDelete } from '../../../utils'
import { resetSlaData } from './utils'

const slaPolicyListResource = inject('slaPolicyListResource')
const updateStep = inject('updateStep')

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
</script>
