<template>
  <Dialog v-model:open="show" :size="'4xl'" bare>
    <template #default>
      <div class="bg-surface-elevation-2 px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <Dialog.Title as-child>
              <h3 class="text-3xl-semibold leading-6 text-ink-gray-9">
                {{ __('Editing Row {0}', [index + 1]) }}
              </h3>
            </Dialog.Title>
          </div>
          <div class="flex items-center gap-1">
            <Button
              v-if="isManager()"
              :tooltip="__('Edit Fields Layout')"
              variant="ghost"
              class="w-7"
              :icon="EditIcon"
              @click="openGridRowFieldsModal"
            />
            <Dialog.Close as-child>
              <Button
                :aria-label="__('Close')"
                icon="lucide-x"
                variant="ghost"
                class="w-7"
              />
            </Dialog.Close>
          </div>
        </div>
        <div>
          <FieldLayout
            v-if="tabs.data"
            :tabs="tabs.data"
            :data="data"
            :doctype="doctype"
            :isGridRow="true"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import EditIcon from '@/components/Icons/EditIcon.vue'
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import { usersStore } from '@/stores/users'
import { Dialog, createResource } from 'frappe-ui'
import { nextTick, provide } from 'vue'

const props = defineProps({
  index: { type: Number, default: 0 },
  data: { type: Object, default: () => ({}) },
  doctype: { type: String, default: '' },
  parentDoctype: { type: String, default: '' },
  parentFieldname: { type: String, default: '' },
})

const { isManager } = usersStore()

provide('parentFieldname', props.parentFieldname)

const show = defineModel({ type: Boolean })
const showGridRowFieldsModal = defineModel('showGridRowFieldsModal', {
  type: Boolean,
})

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['Grid Row', props.doctype, props.parentDoctype],
  params: {
    doctype: props.doctype,
    type: 'Grid Row',
    parent_doctype: props.parentDoctype,
  },
  auto: true,
})

function openGridRowFieldsModal() {
  showGridRowFieldsModal.value = true
  nextTick(() => (show.value = false))
}
</script>
