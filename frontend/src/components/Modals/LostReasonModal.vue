<template>
  <Dialog
    v-model="show"
    :options="{ title: __('Lost Reason') }"
    @close="cancel"
  >
    <template #body-content>
      <div class="-mt-3 mb-4 text-p-base text-ink-gray-7">
        {{
          __('Please provide a reason for marking this {0} as lost', [
            doctype.toLowerCase().replace('crm ', ''),
          ])
        }}
      </div>
      <div class="flex flex-col gap-3">
        <div>
          <div class="mb-2 text-sm text-ink-gray-5">
            {{ __('Lost Reason') }}
            <span class="text-ink-red-2">*</span>
          </div>
          <Link
            ref="linkRef"
            class="form-control flex-1 truncate"
            :value="lostReason"
            doctype="CRM Lost Reason"
            :onCreate="onCreate"
            @change="(v) => (lostReason = v)"
          />
        </div>
        <div>
          <div class="mb-2 text-sm text-ink-gray-5">
            {{ __('Lost Notes') }}
            <span v-if="lostReason == 'Other'" class="text-ink-red-2">*</span>
          </div>
          <FormControl
            class="form-control flex-1 truncate"
            type="textarea"
            :value="lostNotes"
            @change="(e) => (lostNotes = e.target.value)"
          />
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-between items-center gap-2">
        <div><ErrorMessage :message="error" /></div>
        <div class="flex gap-2">
          <Button :label="__('Cancel')" @click="cancel" />
          <Button variant="solid" :label="__('Save')" @click="save" />
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import Link from '@/components/Controls/Link.vue'
import { createDocument } from '@/composables/document'
import { Dialog } from 'frappe-ui'
import { ref } from 'vue'

const props = defineProps({
  doctype: { type: String, default: 'CRM Lead' },
  document: { type: Object, required: true },
})

const show = defineModel({ type: Boolean })

const linkRef = ref(null)
const doc = props.document.doc
const lostReason = ref(doc.lost_reason || '')
const lostNotes = ref(doc.lost_notes || '')
const error = ref('')

function cancel() {
  show.value = false
  error.value = ''
  lostReason.value = ''
  lostNotes.value = ''
  doc.status = props.document.originalDoc.status
}

function save() {
  if (!lostReason.value) {
    error.value = __('Lost Reason is required')
    return
  }
  if (lostReason.value === 'Other' && !lostNotes.value) {
    error.value = __('Lost Notes are required when Lost Reason is "Other"')
    return
  }

  error.value = ''
  show.value = false

  doc.lost_reason = lostReason.value
  doc.lost_notes = lostNotes.value
  props.document.save.submit()
}

function onCreate(value, close) {
  let doc = { lost_reason: value }
  createDocument('CRM Lost Reason', doc, close, (doc) => {
    lostReason.value = doc.name
    linkRef.value?.reload('', true)
  })
}
</script>
