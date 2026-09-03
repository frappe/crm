<template>
  <Dialog v-model:open="show" :options="{ title: __('Add Leads') }">
    <template #body-content>
      <Link
        class="form-control"
        value=""
        doctype="CRM Lead"
        :placeholder="__('Select a lead...')"
        @change="(lead) => addLead(lead)"
      />
      <div v-if="leads.length" class="mt-3 flex flex-wrap gap-1.5">
        <div
          v-for="lead in leads"
          :key="lead"
          class="flex items-center gap-1 rounded-full border border-outline-gray-1 bg-surface-base py-0.5 pl-2 pr-0.5 text-sm text-ink-gray-6"
        >
          {{ lead }}
          <Button
            variant="ghost"
            class="rounded-full !size-4"
            @click="leads = leads.filter((l) => l !== lead)"
          >
            <template #icon>
              <span
                class="lucide-x h-3 w-3 text-ink-gray-6"
                aria-hidden="true"
              />
            </template>
          </Button>
        </div>
      </div>
      <ErrorMessage class="mt-2" :message="error" />
    </template>
    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        :label="__('Add')"
        :disabled="!leads.length"
        :loading="adding"
        @click="addLeads"
      />
    </template>
  </Dialog>
</template>

<script setup>
import Link from '@/components/Controls/Link.vue'
import { Dialog, ErrorMessage, call, toast } from 'frappe-ui'
import { ref } from 'vue'

const props = defineProps({
  segment: { type: String, required: true },
})

const emit = defineEmits(['reload'])

const show = defineModel({ type: Boolean })

const leads = ref([])
const error = ref('')
const adding = ref(false)

function addLead(lead) {
  if (!lead || leads.value.includes(lead)) return
  leads.value.push(lead)
}

async function addLeads() {
  adding.value = true
  error.value = ''
  try {
    const { added, skipped } = await call(
      'crm.fcrm.doctype.crm_lead_segment.crm_lead_segment.add_leads',
      { segment: props.segment, leads: JSON.stringify(leads.value) },
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
