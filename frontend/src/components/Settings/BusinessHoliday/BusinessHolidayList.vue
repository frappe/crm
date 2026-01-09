<template>
  <SettingsLayoutBase
    :title="__('Holiday List')"
    :description="__('Manage your business holiday lists')"
  >
    <template #header-actions>
      <Button
        :label="__('New')"
        variant="solid"
        icon-left="plus"
        @click="createNewHolidayList"
      />
    </template>
    <template
      v-if="
        holidayListResource?.data?.length > 9 || holidayListSearchQuery.length
      "
      #header-bottom
    >
      <div class="relative">
        <Input
          :model-value="holidayListSearchQuery"
          @input="holidayListSearchQuery = $event"
          :placeholder="__('Search')"
          type="text"
          class="bg-surface-gray-2 hover:bg-surface-gray-2 focus:ring-0 border-outline-gray-2 rounded"
          icon-left="search"
          debounce="300"
          inputClass="p-4 pr-12"
        />
        <Button
          v-if="holidayListSearchQuery"
          icon="x"
          variant="ghost"
          @click="holidayListSearchQuery = ''"
          class="absolute right-1 top-1/2 -translate-y-1/2"
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
        <div
          v-if="
            !holidayListResource.loading && !holidayListResource.data?.length
          "
          class="flex flex-col items-center justify-center gap-4 h-full"
        >
          <div
            class="p-4 size-14.5 rounded-full bg-surface-gray-2 flex justify-center items-center"
          >
            <Briefcase class="size-6 text-ink-gray-6" />
          </div>
          <div class="flex flex-col items-center gap-1">
            <div class="text-base font-medium text-ink-gray-6">
              {{ __('No Holiday List found') }}
            </div>
            <div class="text-p-sm text-ink-gray-5 max-w-60 text-center">
              {{ __('Add one to get started.') }}
            </div>
          </div>
          <Button
            :label="__('New')"
            variant="outline"
            icon-left="plus"
            @click="createNewHolidayList()"
          />
        </div>
        <div v-else class="-ml-2">
          <div class="flex text-sm text-gray-600 ml-2">
            <div class="col-span-5">
              {{ __('Holiday List Name') }}
            </div>
          </div>
          <hr class="mt-2 mx-2 border-outline-gray-2" />
          <div
            v-for="(holidayList, index) in holidayListResource.data"
            :key="holidayList.name"
          >
            <div
              class="flex items-center gap-4 cursor-pointer hover:bg-surface-menu-bar rounded"
            >
              <div
                @click="updateToView(holidayList)"
                class="w-full pl-2 col-span-5 flex items-center h-14 gap-2"
              >
                <div class="text-base text-ink-gray-7 font-medium truncate">
                  {{ holidayList.name }}
                </div>
              </div>
              <div class="pr-2">
                <Dropdown
                  placement="right"
                  :options="dropdownOptions(holidayList)"
                >
                  <Button
                    icon="more-horizontal"
                    variant="ghost"
                    @click="isConfirmingDelete = false"
                  />
                </Dropdown>
              </div>
            </div>
            <hr
              v-if="index !== holidayListResource.list.data.length - 1"
              class="mx-2 border-outline-gray-2"
            />
          </div>
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
  <Dialog
    :options="{ title: __('Duplicate Holiday List') }"
    v-model="duplicateDialog.show"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <FormControl
          :label="__('New Holiday List Name')"
          type="text"
          v-model="duplicateDialog.newName"
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
          @click="() => duplicate(holidayList)"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import {
  Button,
  createResource,
  Dialog,
  Dropdown,
  FormControl,
  LoadingIndicator,
  toast,
} from 'frappe-ui'
import SettingsLayoutBase from '../../Layouts/SettingsLayoutBase.vue'
import { inject, ref, watch } from 'vue'
import { ConfirmDelete } from '../../../utils'
import {
  resetHolidayListData,
  holidayListData,
  holidayListActiveStep,
} from './utils'
import Briefcase from '~icons/lucide/briefcase'

const holidayListResource = inject('holidayListResource')
const holidayListSearchQuery = inject('holidayListSearchQuery')

function createNewHolidayList() {
  resetHolidayListData()
  holidayListActiveStep.value = { screen: 'view', data: null }
}

function updateToView(holidayList) {
  holidayListData.value = holidayList
  holidayListActiveStep.value = {
    screen: 'view',
    data: holidayList,
    previousScreen: null,
  }
}

const duplicateDialog = ref({
  show: false,
  newName: '',
  name: '',
})

const isConfirmingDelete = ref(false)

const dropdownOptions = (holidayList) => [
  {
    label: __('Duplicate'),
    onClick: () => {
      duplicateDialog.value = {
        show: true,
        newName: holidayList.name + ' (Copy)',
        name: holidayList.name,
      }
    },
    icon: 'copy',
  },
  ...ConfirmDelete({
    onConfirmDelete: () => deleteHolidayList(holidayList),
    isConfirmingDelete,
  }),
]

const duplicate = () => {
  createResource({
    url: 'frappe.client.get',
    params: {
      doctype: 'CRM Holiday List',
      name: duplicateDialog.value.name,
    },
    onSuccess: (data) => {
      createResource({
        url: 'frappe.client.insert',
        params: {
          doc: {
            ...data,
            holiday_list_name: duplicateDialog.value.newName,
            name: duplicateDialog.value.newName,
          },
        },
        auto: true,
        onSuccess(newHolidayListData) {
          holidayListResource.reload()
          toast.success(__('Holiday list duplicated'))
          duplicateDialog.value = {
            show: false,
            newName: '',
          }
          resetHolidayListData()
          setTimeout(() => {
            holidayListData.value = newHolidayListData
            holidayListActiveStep.value = {
              screen: 'view',
              data: newHolidayListData,
            }
          }, 250)
        },
      })
    },
    auto: true,
  })
}

const deleteHolidayList = (holidayList) => {
  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true
    return
  }

  holidayListResource.delete.submit(holidayList.name, {
    onSuccess: () => {
      toast.success(__('Holiday list deleted'))
    },
    onError: (err) => {
      const message =
        err.messages?.[0] || __('Something went wrong, try again later')
      toast.error(message)
    },
  })
}

watch(holidayListSearchQuery, (newValue) => {
  holidayListResource.filters = {
    name: ['like', `%${newValue}%`],
  }
  if (!newValue) {
    holidayListResource.start = 0
    holidayListResource.pageLength = 10
  }
  holidayListResource.reload()
})
</script>
