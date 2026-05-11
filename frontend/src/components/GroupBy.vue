<template>
  <Combobox :options="options" @update:selectedOption="(e) => setGroupBy(e)">
    <template #trigger="{ open }">
      <Button
        :label="
          hideLabel
            ? groupByValue?.label
            : __('Group By: ') + groupByValue?.label
        "
        :iconLeft="DetailsIcon"
        :iconRight="open ? 'chevron-up' : 'chevron-down'"
      />
    </template>
  </Combobox>
</template>
<script setup>
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import { Combobox, createResource } from 'frappe-ui'
import { ref, computed, onMounted, nextTick, watch } from 'vue'

const props = defineProps({
  doctype: { type: String, required: true },
  hideLabel: { type: Boolean, default: false },
})

const emit = defineEmits(['update'])

const list = defineModel({ type: Object, default: () => ({}) })

const groupByValue = ref({
  label: '',
  fieldname: '',
  value: '',
})

const groupByOptions = createResource({
  url: 'crm.api.doc.get_group_by_fields',
  cache: ['groupByOptions', props.doctype],
  params: { doctype: props.doctype },
})

onMounted(() => {
  if (groupByOptions.data?.length) return
  groupByOptions.fetch()
})

function setGroupBy(data) {
  if (!data?.fieldname) return
  groupByValue.value = data
  nextTick(() => emit('update', data.fieldname))
}

watch(
  () => list.value?.data?.group_by_field,
  (val) => {
    if (val) groupByValue.value = val
  },
  { immediate: true },
)

const options = computed(() => {
  if (!groupByOptions.data) return []
  if (!list.value?.data?.group_by_field) return groupByOptions.data
  return groupByOptions.data.filter(
    (option) => option.fieldname !== groupByValue.value.fieldname,
  )
})
</script>
