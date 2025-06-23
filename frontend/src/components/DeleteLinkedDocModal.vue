<template>
  <Dialog v-model="show" :options="{ size: 'xl' }">
    <template #body v-if="!confirmDeleteInfo.show">
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-4 flex items-center justify-between">
          <div>
            <h3 class="text-2xl leading-6 text-ink-gray-9 font-semibold">
              {{
                linkedDocs?.length == 0
                  ? __('Delete')
                  : __('Delete or unlink linked documents')
              }}
            </h3>
          </div>
          <div class="flex items-center gap-1">
            <Button variant="ghost" class="w-7" @click="show = false">
              <FeatherIcon name="x" class="h-4 w-4" />
            </Button>
          </div>
        </div>
        <div>
          <div v-if="linkedDocs?.length > 0">
            <span class="text-ink-gray-5 text-base">
              {{
                __(
                  'Delete or unlink these linked documents before deleting this document',
                )
              }}
            </span>
            <LinkedDocsListView
              class="mt-4"
              :rows="linkedDocs"
              :columns="[
                {
                  label: 'Document',
                  key: 'title',
                },
                {
                  label: 'Master',
                  key: 'reference_doctype',
                  width: '30%',
                },
              ]"
              @selectionsChanged="
                (selections) => viewControls.updateSelections(selections)
              "
              :linkedDocsResource="linkedDocsResource"
              :unlinkLinkedDoc="unlinkLinkedDoc"
            />
          </div>
          <div v-if="linkedDocs?.length == 0" class="text-ink-gray-5 text-base">
            {{
              __('Are you sure you want to delete {0} - {1}?', [
                props.doctype,
                props.docname,
              ])
            }}
          </div>
        </div>
      </div>
      <div class="px-4 pb-7 pt-0 sm:px-6">
        <div class="flex flex-row-reverse gap-2">
          <Button
            v-if="linkedDocs?.length > 0"
            theme="red"
            variant="solid"
            @click="confirmDelete()"
          >
            <div class="flex gap-1">
              <FeatherIcon name="trash" class="h-4 w-4" />
              <span>
                {{ __('Delete') }}
                {{
                  viewControls?.selections?.length == 0
                    ? __('all')
                    : `${viewControls?.selections?.length} item(s)`
                }}
              </span>
            </div>
          </Button>
          <Button
            v-if="linkedDocs?.length > 0"
            variant="subtle"
            theme="gray"
            @click="confirmUnlink()"
          >
            <div class="flex gap-1">
              <FeatherIcon name="unlock" class="h-4 w-4" />
              <span>
                {{ __('Unlink') }}
                {{
                  viewControls?.selections?.length == 0
                    ? __('all')
                    : `${viewControls?.selections?.length} item(s)`
                }}
              </span>
            </div>
          </Button>
          <Button
            v-if="linkedDocs?.length == 0"
            variant="solid"
            :label="__('Delete')"
            :loading="isDealCreating"
            @click="deleteDoc()"
            theme="red"
          />
        </div>
      </div>
    </template>
    <template #body v-if="confirmDeleteInfo.show">
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-6 flex items-center justify-between">
          <div>
            <h3 class="text-2xl leading-6 text-ink-gray-9 font-semibold">
              {{ confirmDeleteInfo.title }}
            </h3>
          </div>
          <div class="flex items-center gap-1">
            <Button variant="ghost" class="w-7" @click="show = false">
              <FeatherIcon name="x" class="h-4 w-4" />
            </Button>
          </div>
        </div>
        <div class="text-ink-gray-5 text-base">
          {{ confirmDeleteInfo.message }}
        </div>
        <div class="flex justify-end gap-2 mt-6">
          <Button variant="ghost" @click="cancel()">
            {{ __('Cancel') }}
          </Button>
          <Button
            variant="solid"
            :label="confirmDeleteInfo.title"
            @click="removeDocLinks()"
            theme="red"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { createResource, call } from 'frappe-ui'
import { useRouter } from 'vue-router'
import { computed, ref } from 'vue'

const show = defineModel()
const router = useRouter()
const props = defineProps({
  name: {
    type: String,
    required: true,
  },
  doctype: {
    type: String,
    required: true,
  },
  docname: {
    type: String,
    required: true,
  },
  reload: {
    type: Function,
  },
})
const viewControls = ref({
  selections: [],
  updateSelections: (selections) => {
    viewControls.value.selections = Array.from(selections || [])
  },
})

const confirmDeleteInfo = ref({
  show: false,
  title: '',
})

const linkedDocsResource = createResource({
  url: 'crm.api.doc.get_linked_docs_of_document',
  params: {
    doctype: props.doctype,
    docname: props.docname,
  },
  auto: true,
  validate(params) {
    if (!params?.doctype || !params?.docname) {
      return false
    }
  },
})

const linkedDocs = computed(() => {
  return (
    linkedDocsResource.data?.map((doc) => ({
      id: doc.reference_docname,
      ...doc,
    })) || []
  )
})

const cancel = () => {
  confirmDeleteInfo.value.show = false
  viewControls.value.updateSelections([])
}

const unlinkLinkedDoc = (doc) => {
  let selectedDocs = []
  if (viewControls.value.selections.length > 0) {
    Array.from(viewControls.value.selections).forEach((selection) => {
      const docData = linkedDocs.value.find((d) => d.id == selection)
      selectedDocs.push({
        doctype: docData.reference_doctype,
        docname: docData.reference_docname,
      })
    })
  } else {
    selectedDocs = linkedDocs.value.map((doc) => ({
      doctype: doc.reference_doctype,
      docname: doc.reference_docname,
    }))
  }

  call('crm.api.doc.remove_linked_doc_reference', {
    items: selectedDocs,
    remove_contact: props.doctype == 'Contact',
    delete: doc.delete,
  }).then(() => {
    linkedDocsResource.reload()
    confirmDeleteInfo.value = {
      show: false,
      title: '',
    }
  })
}

const confirmDelete = () => {
  const items =
    viewControls.value.selections.length == 0
      ? 'all'
      : viewControls.value.selections.length
  confirmDeleteInfo.value = {
    show: true,
    title: __('Delete linked item'),
    message: __('Are you sure you want to delete {0} linked item(s)?', [items]),
    delete: true,
  }
}

const confirmUnlink = () => {
  const items =
    viewControls.value.selections.length == 0
      ? 'all'
      : viewControls.value.selections.length
  confirmDeleteInfo.value = {
    show: true,
    title: __('Unlink linked item'),
    message: __('Are you sure you want to unlink {0} linked item(s)?', [items]),
    delete: false,
  }
}

const removeDocLinks = () => {
  unlinkLinkedDoc({
    reference_doctype: props.doctype,
    reference_docname: props.docname,
    delete: confirmDeleteInfo.value.delete,
  })
  viewControls.value.updateSelections([])
}

const deleteDoc = async () => {
  await call('frappe.client.delete', {
    doctype: props.doctype,
    name: props.docname,
  })
  router.push({ name: props.name })
  props?.reload?.()
}
</script>
