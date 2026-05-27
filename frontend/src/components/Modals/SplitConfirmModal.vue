<template>
  <Dialog v-model="show" :options="{ size: 'md' }">
    <template #body-header>
      <div class="mb-4 flex items-center justify-between">
        <div>
          <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
            {{ __('Split Lead') }}
          </h3>
        </div>
        <Button icon="x" variant="ghost" @click="show = false" />
      </div>
    </template>
    <template #body-content>
      <div
        class="rounded-lg border border-yellow-200 bg-yellow-50 px-4 py-3 text-sm"
      >
        <div class="mb-1 font-medium text-yellow-800">
          {{ __('Are you sure?') }}
        </div>
        <p class="text-ink-gray-7">
          {{
            __('This will undo the merge of {0} from {1}.', [
              mergeLog?.source_title || mergeLog?.source_document_name,
              mergeLog?.target_title || mergeLog?.target_document_name,
            ])
          }}
        </p>
        <p class="mt-2 text-ink-gray-7">
          {{
            __(
              'Any changes made to the target lead since the merge will be lost for the affected fields. Child records will be moved back to the source lead.',
            )
          }}
        </p>
      </div>
      <ErrorMessage v-if="error" class="mt-4" :message="error" />
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          :label="__('Split')"
          variant="solid"
          theme="red"
          :loading="isSplitting"
          @click="performSplit"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref } from 'vue'
import { call, toast } from 'frappe-ui'
import { useRouter } from 'vue-router'

const props = defineProps({
  mergeLog: { type: Object, required: true },
})

const emit = defineEmits(['split'])
const show = defineModel({ type: Boolean })
const router = useRouter()
const error = ref(null)
const isSplitting = ref(false)

async function performSplit() {
  isSplitting.value = true
  error.value = null
  try {
    const result = await call('crm.api.lead.split_lead', {
      merge_log_name: props.mergeLog.name,
    })
    toast.success(result.message || __('Merge split successfully'))
    show.value = false
    emit('split', result.target)
    router.push({ name: 'Lead', params: { leadId: result.target } })
  } catch (err) {
    error.value =
      err.messages?.[0] || err.message || __('Failed to split leads')
  } finally {
    isSplitting.value = false
  }
}
</script>
