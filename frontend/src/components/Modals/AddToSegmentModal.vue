<template>
  <Dialog v-model:open="show" :options="{ title: __('Add to Segment') }">
    <template #body-content>
      <div class="mb-2 text-p-base text-ink-gray-6">
        {{ __('Add {0} lead(s) to a segment.', [leads.size]) }}
      </div>
      <Link
        class="form-control"
        :value="segment"
        doctype="CRM Lead Segment"
        :placeholder="__('Select a segment...')"
        @change="(value) => (segment = value)"
        @create="(value, close) => createSegment(value, close)"
      />
      <ErrorMessage class="mt-2" :message="error" />
    </template>
    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        :label="__('Add')"
        :disabled="!segment"
        :loading="adding"
        @click="addToSegment"
      />
    </template>
  </Dialog>
</template>

<script setup>
import Link from '@/components/Controls/Link.vue'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { Dialog, ErrorMessage, call, toast } from 'frappe-ui'
import { ref } from 'vue'

const props = defineProps({
  leads: { type: Set, required: true },
})

const emit = defineEmits(['reload'])

const show = defineModel({ type: Boolean })

const { showModal } = useDoctypeModal()

const segment = ref('')
const error = ref('')
const adding = ref(false)

function createSegment(value, close) {
  close?.()
  showModal({
    doctype: 'CRM Lead Segment',
    title: 'Lead Segment',
    defaults: { segment_name: value },
    callbacks: { afterInsert: (doc) => (segment.value = doc.name) },
  })
}

async function addToSegment() {
  adding.value = true
  error.value = ''
  try {
    const { added, skipped } = await call(
      'crm.fcrm.doctype.crm_lead_segment.crm_lead_segment.add_leads',
      {
        segment: segment.value,
        leads: JSON.stringify(Array.from(props.leads)),
      },
    )
    toast.success(
      skipped
        ? __('{0} lead(s) added, {1} already in the segment', [added, skipped])
        : __('{0} lead(s) added', [added]),
    )
    emit('reload')
    show.value = false
  } catch (e) {
    error.value = e.messages?.[0] || e.message
  } finally {
    adding.value = false
  }
}
</script>
