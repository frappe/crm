<template>
  <Dialog
    v-model="show"
    :options="{
      title:
        mode == 'edit'
          ? __('Edit View')
          : mode == 'duplicate'
            ? __('Duplicate View')
            : __('Create View'),
    }"
  >
    <template #body-content>
      <div class="mb-1.5 block text-base text-ink-gray-5">
        {{ __('View Name') }}
      </div>
      <div class="flex gap-2">
        <IconPicker v-model="view.icon" v-slot="{ togglePopover }">
          <Button
            size="md"
            class="flex min-w-9 text-2xl leading-none"
            :label="view.icon"
            @click="togglePopover"
          />
        </IconPicker>
        <TextInput
          ref="viewLabel"
          class="flex-1"
          size="md"
          type="text"
          :placeholder="__('My Open Deals')"
          v-model="view.label"
        />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end">
        <Button
          variant="solid"
          :label="
            mode == 'edit'
              ? __('Save Changes')
              : mode == 'duplicate'
                ? __('Duplicate')
                : __('Create')
          "
          @click="() => (mode == 'edit' ? update() : create())"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import IconPicker from '@/components/IconPicker.vue'
import { useView, useViews } from '@/stores/view'
import { TextInput, useCall } from 'frappe-ui'
import { ref, inject, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  mode: {
    type: String,
    default: 'create',
  },
})

const doctype = inject('doctype')
const viewName = inject('viewName')
const currentView = inject('currentView')

const { reloadCurrentView } = useView(doctype, viewName)
const { reloadViews } = useViews()

const show = defineModel()
const view = defineModel('view')
const viewLabel = ref(null)

const router = useRouter()

function create() {
  view.value.doctype = doctype

  useCall({
    url: '/api/v2/method/crm.fcrm.doctype.crm_view_settings.crm_view_settings.create',
    method: 'POST',
    params: { view: view.value },
    onSuccess: (v) => {
      show.value = false
      reload()
      router.push({
        name: v.route_name,
        params: { viewName: v.name },
      })
    },
  })
}

function update() {
  view.value.doctype = doctype

  useCall({
    url: '/api/v2/method/crm.fcrm.doctype.crm_view_settings.crm_view_settings.update',
    method: 'POST',
    params: { view: view.value },
    onSuccess: (v) => {
      show.value = false
      reload(v.name)
    },
  })
}

function reload(viewName = null) {
  if (viewName && currentView.value?.name === viewName) {
    reloadCurrentView()
  }
  reloadViews()
}

onMounted(() => nextTick(() => viewLabel.value?.el?.focus()))
</script>
