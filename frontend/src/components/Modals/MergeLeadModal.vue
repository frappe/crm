<template>
  <Dialog
    v-model="show"
    :options="{
      title: __('Merge with another lead'),
      size: 'md',
    }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <p class="text-base text-ink-gray-7">
          {{
            __(
              'Select a lead to merge into this one. Its activities will be transferred here, and any empty fields on this lead will be populated from the',
            )
          }}
          <span class="inline-flex items-center gap-1">
            {{ __('selected lead.') }}
            <Popover trigger="hover" :hoverDelay="0.25" placement="right">
              <template #target>
                <FeatherIcon name="info" class="size-4 cursor-pointer" />
              </template>
              <template #body-main>
                <div
                  class="max-w-[26rem] whitespace-pre-wrap rounded-md bg-surface-white p-3 text-sm leading-5 text-ink-gray-6"
                >
                  <span class="font-medium text-ink-gray-7">
                    {{ __("Here's what will happen") }}
                  </span>
                  <ul class="mt-1.5 list-disc space-y-1 pl-4">
                    <li>
                      {{
                        __(
                          'All activities, notes, tasks, emails and calls from the selected lead will move to this lead.',
                        )
                      }}
                    </li>
                    <li>
                      {{
                        __(
                          'Empty fields on this lead will be filled in from the selected lead. Existing values are kept as-is.',
                        )
                      }}
                    </li>
                  </ul>
                </div>
              </template>
            </Popover>
          </span>
        </p>

        <div class="flex flex-col gap-1.5">
          <span class="text-sm text-ink-gray-5">{{ __('Lead') }}</span>
          <Link
            v-model="selectedLead"
            doctype="CRM Lead"
            :searchUrl="'crm.api.lead.search_mergeable_leads'"
            :searchParams="{ current_lead: leadId }"
            :placeholder="__('Select Lead')"
          />
        </div>

        <ErrorMessage v-if="error" :message="error" />
      </div>
    </template>

    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        size="md"
        :label="__('Merge Lead')"
        :loading="isMerging"
        :disabled="!selectedLead"
        @click="performMerge"
      />
    </template>
  </Dialog>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  Dialog,
  Button,
  ErrorMessage,
  FeatherIcon,
  Popover,
  call,
  toast,
} from 'frappe-ui'
import Link from '@/components/Controls/Link.vue'
import { reloadDocument } from '@/data/document'

const props = defineProps({
  leadId: { type: String, required: true },
})

const emit = defineEmits(['merged'])
const show = defineModel({ type: Boolean })
const router = useRouter()

const selectedLead = ref('')
const isMerging = ref(false)
const error = ref(null)

async function performMerge() {
  isMerging.value = true
  error.value = null
  try {
    const result = await call('crm.api.lead.merge_leads', {
      target: props.leadId,
      source: selectedLead.value,
    })
    reloadDocument('CRM Lead', result.target)
    reloadDocument('CRM Lead', result.source)
    show.value = false
    emit('merged', result.target)
    toast.success(__('Lead merged successfully'), {
      action: {
        label: __('View'),
        onClick: () =>
          router.push({ name: 'Lead', params: { leadId: result.target } }),
      },
    })
    router.push({ name: 'Leads' })
  } catch (err) {
    error.value =
      err.messages?.[0] || err.message || __('Failed to merge leads')
  } finally {
    isMerging.value = false
  }
}
</script>
