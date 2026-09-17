<template>
  <Dialog v-model:open="show" :size="'xl'">
    <template #body-header>
      <div class="mb-6 flex items-center justify-between">
        <h3 class="text-3xl-semibold leading-6 text-ink-gray-9">
          {{ __('Merge Lead') }}
        </h3>
        <Button icon="lucide-x" variant="ghost" @click="show = false" />
      </div>
    </template>
    <template #default>
      <div class="mb-4 flex items-center gap-2 text-ink-gray-5">
        <LeadsIcon class="h-4 w-4" />
        <label class="block text-base">{{ __('Merge with') }}</label>
      </div>
      <div class="ml-6 text-ink-gray-9">
        <Link
          class="form-control"
          size="md"
          :value="otherLead"
          doctype="CRM Lead"
          :filters="otherLeadFilters"
          :placeholder="__('Select a lead')"
          @change="(data) => (otherLead = data)"
        />
        <div v-if="duplicates.length" class="mt-2.5 flex flex-col gap-1">
          <div class="text-sm text-ink-gray-5">
            {{ __('Possible duplicates') }}
          </div>
          <div
            v-for="d in duplicates"
            :key="d.name"
            class="flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-base text-ink-gray-8 hover:bg-surface-gray-3"
            @click="otherLead = d.name"
          >
            <input type="radio" :checked="otherLead === d.name" />
            <div class="flex-1 truncate">
              {{ d.lead_name || d.name }}
              <span class="text-ink-gray-5">
                · {{ d.email || d.mobile_no || d.phone }}
              </span>
            </div>
            <Badge :label="d.status" variant="subtle" />
          </div>
        </div>
      </div>

      <template v-if="otherLead">
        <div class="my-6 h-px w-full border-t" />

        <div class="mb-4 flex items-center gap-2 text-ink-gray-5">
          <Icon icon="lucide-git-merge" class="h-4 w-4" />
          <label class="block text-base">{{ __('Keep') }}</label>
        </div>
        <div
          class="ml-6 flex items-center justify-between text-base text-ink-gray-9"
        >
          <div>
            {{
              __('{0} will be kept and {1} will be deleted', [target, source])
            }}
          </div>
          <Button
            :label="__('Swap')"
            icon-left="lucide-arrow-left-right"
            @click="keepThis = !keepThis"
          />
        </div>

        <div class="my-6 h-px w-full border-t" />

        <div class="mb-4 flex items-center gap-2 text-ink-gray-5">
          <Icon icon="lucide-list-checks" class="h-4 w-4" />
          <label class="block text-base">{{ __('Fields') }}</label>
        </div>
        <div class="ml-6 text-base text-ink-gray-9">
          <div v-if="mergeFields.loading" class="text-ink-gray-5">
            {{ __('Loading...') }}
          </div>
          <div v-else-if="!mergeFields.data?.length" class="text-ink-gray-5">
            {{ __('Both leads have the same details') }}
          </div>
          <template v-else>
            <div class="mb-2 text-sm text-ink-gray-5">
              {{ __('Choose which value to keep for each field that differs') }}
            </div>
            <div
              class="grid grid-cols-[1fr_2fr_2fr] gap-x-4 border-b pb-1.5 text-sm text-ink-gray-5"
            >
              <div>{{ __('Field') }}</div>
              <div>{{ target }}</div>
              <div>{{ source }}</div>
            </div>
            <div
              v-for="field in mergeFields.data"
              :key="field.fieldname"
              class="grid grid-cols-[1fr_2fr_2fr] items-center gap-x-4 border-b py-1.5"
            >
              <div class="truncate text-ink-gray-7">{{ field.label }}</div>
              <label class="flex cursor-pointer items-center gap-2">
                <input
                  type="radio"
                  :name="field.fieldname"
                  value="target"
                  v-model="choices[field.fieldname]"
                />
                <span
                  class="truncate"
                  :class="{ 'text-ink-gray-4': !field.target_display }"
                >
                  {{ field.target_display || __('Empty') }}
                </span>
              </label>
              <label class="flex cursor-pointer items-center gap-2">
                <input
                  type="radio"
                  :name="field.fieldname"
                  value="source"
                  v-model="choices[field.fieldname]"
                />
                <span
                  class="truncate"
                  :class="{ 'text-ink-gray-4': !field.source_display }"
                >
                  {{ field.source_display || __('Empty') }}
                </span>
              </label>
            </div>
          </template>
        </div>
      </template>
      <ErrorMessage class="mt-4" :message="error" />
    </template>
    <template #actions>
      <div class="flex justify-end">
        <Button
          :label="__('Merge')"
          variant="solid"
          :disabled="!otherLead || mergeFields.loading"
          :loading="merging"
          @click="mergeLeads"
        />
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import Link from '@/components/Controls/Link.vue'
import Icon from '@/components/Icon.vue'
import { Dialog, Badge, createResource, call, toast } from 'frappe-ui'
import { ref, computed, reactive, watch } from 'vue'

const props = defineProps({
  lead: { type: Object, required: true },
  duplicates: { type: Array, default: () => [] },
})

const emit = defineEmits(['merged'])

const show = defineModel({ type: Boolean })

const otherLead = ref(
  props.duplicates.length === 1 ? props.duplicates[0].name : '',
)
const keepThis = ref(false)
const choices = reactive({})
const error = ref('')
const merging = ref(false)

const otherLeadFilters = computed(() => ({
  name: ['!=', props.lead.name],
  converted: 0,
}))

// The source is deleted; its links and the chosen values move to the target.
const source = computed(() =>
  keepThis.value ? otherLead.value : props.lead.name,
)
const target = computed(() =>
  keepThis.value ? props.lead.name : otherLead.value,
)

const mergeFields = createResource({
  url: 'crm.fcrm.doctype.crm_lead.crm_lead.get_lead_merge_fields',
  makeParams: () => ({ source: source.value, target: target.value }),
  onSuccess: (fields) => {
    Object.keys(choices).forEach((k) => delete choices[k])
    fields.forEach((f) => {
      choices[f.fieldname] = f.target_value ? 'target' : 'source'
    })
  },
})

watch(
  [source, target],
  () => {
    error.value = ''
    if (source.value && target.value) mergeFields.fetch()
  },
  { immediate: true },
)

async function mergeLeads() {
  error.value = ''
  let values = {}
  mergeFields.data?.forEach((f) => {
    if (choices[f.fieldname] === 'source') values[f.fieldname] = f.source_value
  })

  merging.value = true
  try {
    await call('crm.fcrm.doctype.crm_lead.crm_lead.merge_leads', {
      source: source.value,
      target: target.value,
      values,
    })
  } catch (err) {
    error.value = __('Error merging leads: {0}', [err.messages?.[0]])
    merging.value = false
    return
  }
  merging.value = false
  show.value = false
  toast.success(__('Lead {0} merged into {1}', [source.value, target.value]))
  emit('merged', target.value)
}
</script>
