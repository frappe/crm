<template>
  <Dialog
    v-model="show"
    :options="{ title: __('Lost reason') }"
    @close="cancel"
  >
    <template #body-content>
      <div class="-mt-3 mb-4 text-p-base text-ink-gray-7">
        {{ __('Please provide a reason for marking this deal as lost') }}
      </div>
      <div class="flex flex-col gap-3">
        <div>
          <div class="mb-2 text-sm text-ink-gray-5">
            {{ __('Lost reason') }}
            <span class="text-ink-red-2">*</span>
          </div>
          <Link
            class="form-control flex-1 truncate"
            :value="lostReason"
            doctype="CRM Lost Reason"
            @change="(v) => (lostReason = v)"
            :onCreate="onCreate"
          />
        </div>
        <div>
          <div class="mb-2 text-sm text-ink-gray-5">
            {{ __('Lost notes') }}
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
  deal: {
    type: Object,
    required: true,
  },
})

const show = defineModel()

const lostReason = ref(props.deal.doc.lost_reason || '')
const lostNotes = ref(props.deal.doc.lost_notes || '')
const error = ref('')

function cancel() {
  show.value = false
  error.value = ''
  lostReason.value = ''
  lostNotes.value = ''
  props.deal.doc.status = props.deal.originalDoc.status
}

function save() {
  if (!lostReason.value) {
    error.value = __('Lost reason is required')
    return
  }
  if (lostReason.value === 'Other' && !lostNotes.value) {
    error.value = __('Lost notes are required when lost reason is "Other"')
    return
  }

  error.value = ''
  show.value = false

  props.deal.doc.lost_reason = lostReason.value
  props.deal.doc.lost_notes = lostNotes.value
  props.deal.save.submit()
}

function onCreate(value, close) {
  createDocument('CRM Lost Reason', value, close)
}
</script>
