<template>
  <div
    class="my-3 flex items-center justify-between text-lg font-medium sm:mb-4 sm:mt-8"
  >
    <div class="flex h-8 items-center text-xl font-semibold text-ink-gray-8">
      {{ __('Data') }}
      <Badge
        v-if="data.isDirty"
        class="ml-3"
        :label="'Not Saved'"
        theme="orange"
      />
    </div>
    <div class="flex gap-1">
      <Button v-if="isManager()" @click="showDataFieldsModal = true">
        <EditIcon class="h-4 w-4" />
      </Button>
      <Button
        label="Save"
        :disabled="!data.isDirty"
        variant="solid"
        :loading="data.save.loading"
        @click="saveChanges"
      />
    </div>
  </div>
  <div
    v-if="data.get.loading"
    class="flex flex-1 flex-col items-center justify-center gap-3 text-xl font-medium text-gray-500"
  >
    <LoadingIndicator class="h-6 w-6" />
    <span>{{ __('Loading...') }}</span>
  </div>
  <div v-else>
    <FieldLayout v-if="tabs.data" :tabs="tabs.data" :data="data.doc" />
  </div>
  <DataFieldsModal
    v-if="showDataFieldsModal"
    v-model="showDataFieldsModal"
    :doctype="doctype"
    @reload="
      () => {
        tabs.reload()
        data.reload()
      }
    "
  />
</template>

<script setup>
import EditIcon from '@/components/Icons/EditIcon.vue'
import DataFieldsModal from '@/components/Modals/DataFieldsModal.vue'
import FieldLayout from '@/components/FieldLayout.vue'
import { Badge, createResource, createDocumentResource } from 'frappe-ui'
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import { createToast } from '@/utils'
import { usersStore } from '@/stores/users'
import { ref } from 'vue'

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
  docname: {
    type: String,
    required: true,
  },
})

const { isManager } = usersStore()

const showDataFieldsModal = ref(false)

const data = createDocumentResource({
  doctype: props.doctype,
  name: props.docname,
  setValue: {
    onSuccess: () => {
      data.reload()
      createToast({
        title: 'Data Updated',
        icon: 'check',
        iconClasses: 'text-green-600',
      })
    },
    onError: (err) => {
      createToast({
        title: 'Error',
        text: err.messages[0],
        icon: 'x',
        iconClasses: 'text-red-600',
      })
    },
  },
})

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['DataFields', props.doctype],
  params: { doctype: props.doctype, type: 'Data Fields' },
  auto: true,
})

function saveChanges() {
  data.save.submit()
}
</script>
