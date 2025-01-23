<template>
  <Autocomplete :options="options" value="" @change="(e) => setGroupBy(e)">
    <template #target="{ togglePopover, isOpen }">
      <Button
        :label="
          hideLabel
            ? groupByValue?.label
            : __('Group By: ') + groupByValue?.label
        "
        @click="togglePopover()"
      >
        <template #prefix>
          <DetailsIcon />
        </template>
        <template #suffix>
          <FeatherIcon
            :name="isOpen ? 'chevron-up' : 'chevron-down'"
            class="h-4"
          />
        </template>
      </Button>
    </template>
  </Autocomplete>
</template>
<script setup>
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import { createResource } from 'frappe-ui'
import { ref, computed, onMounted, nextTick } from 'vue'

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
  hideLabel: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update'])

const list = defineModel()

const groupByValue = ref({
  label: '',
  fieldname: '',
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

const options = computed(() => {
  if (!groupByOptions.data) return []
  if (!list.value?.data?.group_by_field) return groupByOptions.data
  groupByValue.value = list.value.data.group_by_field
  return groupByOptions.data.filter(
    (option) => option.fieldname !== groupByValue.value.fieldname,
  )
})
</script>
