<template>
  <Dialog v-model="show" :options="{ size: '4xl' }">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ __('Editing Row {0}', [index + 1]) }}
            </h3>
          </div>
          <div class="flex items-center gap-1">
            <Button
              v-if="isManager()"
              variant="ghost"
              class="w-7"
              @click="openGridRowFieldsModal"
            >
              <template #icon>
                <EditIcon />
              </template>
            </Button>
            <Button variant="ghost" class="w-7" @click="show = false">
              <template #icon>
                <FeatherIcon name="x" class="size-4" />
              </template>
            </Button>
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
import { createResource } from 'frappe-ui'
import { nextTick } from 'vue'

const props = defineProps({
  index: Number,
  data: Object,
  doctype: String,
  parentDoctype: String,
})

const { isManager } = usersStore()

const show = defineModel()
const showGridRowFieldsModal = defineModel('showGridRowFieldsModal')

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
