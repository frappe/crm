<template>
  <div
    class="my-3 flex items-center justify-between text-lg font-medium sm:mb-4 sm:mt-8"
  >
    <div class="flex h-8 items-center text-xl font-semibold text-ink-gray-8">
      {{ __('Data') }}
      <Badge
        v-if="isDirty"
        class="ml-3"
        :label="__('Not Saved')"
        theme="orange"
      />
    </div>
    <div class="flex gap-1">
      <Button v-if="isManager()" @click="showDataFieldsModal = true">
        <EditIcon class="h-4 w-4" />
      </Button>
      <Button
        :label="__('Save')"
        :disabled="!isDirty"
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
import { ref, watch } from 'vue'

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
const originalData = ref({})
const isDirty = ref(false)

const emit = defineEmits(['update'])

const data = createDocumentResource({
  doctype: props.doctype,
  name: props.docname,
  setValue: {
    onSuccess: () => {
      data.reload()
      createToast({
        title: __('Data Updated'),
        icon: 'check',
        iconClasses: 'text-green-600',
      })
    },
    onError: (err) => {
      createToast({
        title: __('Error'),
        text: err.messages[0],
        icon: 'x',
        iconClasses: 'text-red-600',
      })
    },
  },
  onSuccess: (doc) => {
    originalData.value = { ...doc }
    checkDirty()
    emit('update')
  }
})

watch(() => data.doc, (newDoc, oldDoc) => {
  if (!newDoc) return
  if (Object.keys(originalData.value).length === 0) {
    originalData.value = { ...newDoc }
  }
  checkDirty()
}, { deep: true })

function checkDirty() {
  if (!data.doc || !originalData.value) return
  
  isDirty.value = Object.keys(data.doc).some(key => {
    if (key === '_organizationObj') {
      const origOrg = originalData.value._organizationObj || {}
      const currentOrg = data.doc._organizationObj || {}
      return Object.keys(currentOrg).some(orgKey => {
        if (orgKey === 'modified' || orgKey === 'modified_by') return false
        return origOrg[orgKey] !== currentOrg[orgKey]
      })
    }
    
    if (key === '_contactObj') {
      const origContact = originalData.value._contactObj || {}
      const currentContact = data.doc._contactObj || {}
      return Object.keys(currentContact).some(contactKey => {
        if (contactKey === 'modified' || contactKey === 'modified_by') return false
        return origContact[contactKey] !== currentContact[contactKey]
      })
    }
    
    if (key.startsWith('_') || key === 'modified' || key === 'modified_by') return false
    
    const originalValue = originalData.value[key]
    const currentValue = data.doc[key]
    if (!originalValue && !currentValue) return false
    if (originalValue === '' && currentValue === '') return false
    if (originalValue === currentValue) return false
    return true
  })
}

function saveChanges() {
  data.save.submit().then(() => {
    originalData.value = { ...data.doc }
    isDirty.value = false
  })
}

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['DataFields', props.doctype],
  params: { doctype: props.doctype, type: 'Data Fields' },
  auto: true,
})
</script>
