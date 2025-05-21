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
          <div v-if="linkedDocs.data?.length > 0">
            <span>
              {{
                __(
                  'Unlink these linked documents before deleting this document',
                )
              }}
            </span>
            <ul class="mt-5 space-y-1">
              <hr />
              <li v-for="doc in linkedDocs.data" :key="doc.name">
                <div class="flex justify-between items-center">
                  <span
                    class="text-lg font-medium text-ellipsis overflow-hidden whitespace-nowrap w-full"
                    >{{ doc.reference_doctype }} ({{
                      doc.reference_docname
                    }})</span
                  >
                  <div class="flex gap-2">
                    <Button variant="ghost" @click="viewLinkedDoc(doc)">
                      <div class="flex gap-1">
                        <FeatherIcon name="external-link" class="h-4 w-4" />
                        <span> View </span>
                      </div>
                    </Button>
                    <Button variant="ghost" @click="unlinkLinkedDoc(doc)">
                      <div class="flex gap-1">
                        <FeatherIcon name="unlock" class="h-4 w-4" />
                        <span> Unlink </span>
                      </div>
                    </Button>
                  </div>
                </div>
                <hr class="my-2 w-full" />
              </li>
            </ul>
          </div>
          <div v-if="linkedDocs.data?.length == 0">
            {{
              __('Are you sure you want to delete {0} - {1}?', [
                props.doctype,
                props.docname,
              ])
            }}
          </div>
          <ErrorMessage class="mt-4" v-if="error" :message="__(error)" />
        </div>
      </div>
      <div class="px-4 pb-7 pt-0 sm:px-6">
        <div class="flex flex-row-reverse gap-2">
          <Button
            v-if="linkedDocs.data?.length > 0"
            variant="solid"
            @click="
              unlinkLinkedDoc({
                reference_doctype: props.doctype,
                reference_docname: props.docname,
                removeAll: true,
              })
            "
          >
            <div class="flex gap-1">
              <FeatherIcon name="unlock" class="h-4 w-4" />
              <span> Unlink all </span>
            </div>
          </Button>
          <Button
            v-if="linkedDocs.data?.length == 0"
            variant="solid"
            :label="__('Delete')"
            :loading="isDealCreating"
            @click="deleteDoc()"
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
})

const linkedDocs = createResource({
  url: 'crm.api.doc.getLinkedDocs',
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

const viewLinkedDoc = (doc) => {
  window.open(`/app/Form/${doc.reference_doctype}/${doc.reference_docname}`)
}

const unlinkLinkedDoc = (doc) => {
  call('crm.api.doc.removeLinkedDocReference', {
    doctype: doc.reference_doctype,
    docname: doc.reference_docname,
    removeAll: doc.removeAll,
    removeContact: props.doctype == 'Contact',
  }).then(() => {
    linkedDocs.reload()
  })
}

const deleteDoc = async () => {
  await call('frappe.client.delete', {
    doctype: props.doctype,
    name: props.docname,
  })
  router.push({ name: props.name })
}
</script>
