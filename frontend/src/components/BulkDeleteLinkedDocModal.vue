<template>
  <Dialog v-model="show" :options="{ size: 'xl' }">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-6 flex items-center justify-between">
          <div>
            <h3 class="text-2xl leading-6 text-ink-gray-9 font-semibold">
              {{ __('Delete') }}
            </h3>
          </div>
          <div class="flex items-center gap-1">
            <Button variant="ghost" class="w-7" @click="show = false">
              <FeatherIcon name="x" class="h-4 w-4" />
            </Button>
          </div>
        </div>
        <div>
          <div class="text-ink-gray-5">
            {{
              __('Are you sure you want to delete {0} items?', [
                props.items?.length,
              ])
            }}
          </div>
        </div>
      </div>
      <div class="px-4 pb-7 pt-0 sm:px-6">
        <div class="flex flex-row-reverse gap-2">
          <Button theme="red" variant="solid" @click="confirmDelete()">
            <div class="flex gap-1">
              <FeatherIcon name="trash" class="h-4 w-4" />
              <span>
                {{ __('Delete {0} items', [props.items.length]) }}
              </span>
            </div>
          </Button>
          <Button variant="solid" @click="confirmUnlink()">
            <div class="flex gap-1">
              <FeatherIcon name="unlock" class="h-4 w-4" />
              <span>
                {{ __('Unlink and delete {0} items', [props.items.length]) }}
              </span>
            </div>
          </Button>
        </div>
      </div>
    </template>
    <template #body v-if="confirmDeleteInfo.show">
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-6 flex items-center justify-between">
          <div>
            <h3 class="text-2xl leading-6 text-ink-gray-9 font-semibold">
              {{ __('Delete') }}
            </h3>
          </div>
          <div class="flex items-center gap-1">
            <Button variant="ghost" class="w-7" @click="show = false">
              <FeatherIcon name="x" class="h-4 w-4" />
            </Button>
          </div>
        </div>
        <div>
          <div class="text-ink-gray-5">
            {{
              confirmDeleteInfo.delete
                ? __(
                    'This will delete selected items and items linked to it, are you sure?',
                  )
                : __(
                    'This will delete selected items and unlink linked items to it, are you sure?',
                  )
            }}
          </div>
        </div>
      </div>
      <div class="px-4 pb-7 pt-0 sm:px-6">
        <div class="flex flex-row-reverse gap-2">
          <Button variant="solid" theme="red" @click="deleteDocs()">
            <div class="flex gap-1">
              <span>
                {{
                  confirmDeleteInfo.delete
                    ? __('Delete')
                    : __('Unlink and delete')
                }}
              </span>
            </div>
          </Button>
          <Button variant="subtle" @click="confirmDeleteInfo.show = false">
            <div class="flex gap-1">
              <span>
                {{ __('Cancel') }}
              </span>
            </div>
          </Button>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { call } from 'frappe-ui'
import { ref } from 'vue'

const show = defineModel()
const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
  items: {
    type: Array,
    required: true,
  },
  reload: {
    type: Function,
    required: true,
  },
})

const confirmDeleteInfo = ref({
  show: false,
  title: '',
  message: '',
  delete: false,
})

const confirmDelete = () => {
  confirmDeleteInfo.value = {
    show: true,
    title: __('Delete'),
    message: __('Are you sure you want to delete {0} linked doc(s)?', [
      props.items.length,
    ]),
    delete: true,
  }
}

const confirmUnlink = () => {
  confirmDeleteInfo.value = {
    show: true,
    title: __('Unlink'),
    message: __('Are you sure you want to unlink {0} linked doc(s)?', [
      props.items.length,
    ]),
    delete: false,
  }
}

const deleteDocs = () => {
  call('crm.api.doc.delete_bulk_docs', {
    items: props.items,
    doctype: props.doctype,
    delete_linked: confirmDeleteInfo.value.delete,
  }).then(() => {
    confirmDeleteInfo.value = {
      show: false,
      title: '',
    }
    show.value = false
    props.reload()
  })
}
</script>
