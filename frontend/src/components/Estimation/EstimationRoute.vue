<template>
  <div class="flex flex-col gap-4">
    <div class="flex items-center justify-between">
      <div class="text-xl font-semibold text-ink-gray-8">{{ __('Route') }}</div>
      <Button
        :label="__('Save')"
        :disabled="!document.isDirty"
        variant="solid"
        :loading="document.save.loading"
        @click="document.save.submit()"
      />
    </div>
    <FieldLayout
      v-if="document.doc"
      :tabs="routeTabs"
      :data="document.doc"
      doctype="CRM Estimation"
    />
  </div>
</template>

<script setup>
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import { Button } from 'frappe-ui'
import { useDocument } from '@/data/document'

const props = defineProps({
  docname: { type: String, required: true },
})

const { document } = useDocument('CRM Estimation', props.docname)

// Layout Route (tetap, bisa dijadikan editable-DB nanti bila perlu).
const routeTabs = [
  {
    name: 'route_tab',
    label: '',
    sections: [
      {
        label: 'Route',
        name: 'sec_route',
        opened: true,
        columns: [
          { name: 'rc1', fields: ['route_type', 'route1', 'route2', 'route3', 'route4'] },
          { name: 'rc2', fields: ['route5', 'route6', 'route7', 'route8'] },
        ],
      },
      {
        label: 'Estimated Distance',
        name: 'sec_dist',
        opened: true,
        columns: [{ name: 'rc3', fields: ['est_km', 'est_days'] }],
      },
    ],
  },
]
</script>
