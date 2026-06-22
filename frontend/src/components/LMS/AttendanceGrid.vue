<template>
  <div class="overflow-x-auto border border-outline-gray-1 rounded-xl">
    <table class="w-full text-left min-w-[600px]">
      <thead>
        <tr class="bg-surface-gray-1 border-b border-outline-gray-2 text-p-xs text-ink-gray-5 uppercase tracking-wider">
          <th class="py-3 px-4 font-medium sticky left-0 bg-surface-gray-1 z-10">{{ __('Student') }}</th>
          <th v-for="s in students" :key="s.name" class="py-3 px-2 font-medium text-center whitespace-nowrap">
            <div class="text-p-xs">{{ s.name }}</div>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="s in students" :key="s.name" class="border-b border-outline-gray-1 hover:bg-surface-gray-1 transition-colors">
          <td class="py-2.5 px-4 text-p-sm font-medium text-ink-gray-8 sticky left-0 bg-surface-base whitespace-nowrap">{{ s.name }}</td>
          <td v-for="col in students" :key="col.name" class="py-2.5 px-2 text-center">
            <select
              v-if="s.name === col.name"
              :value="getStatus(s.name)"
              class="border border-outline-gray-2 rounded px-2 py-1 text-p-xs bg-surface-base cursor-pointer"
              @change="updateStatus(s.name, $event.target.value)"
            >
              <option value="Present">{{ __('Present') }}</option>
              <option value="Absent">{{ __('Absent') }}</option>
              <option value="Late">{{ __('Late') }}</option>
              <option value="Excused">{{ __('Excused') }}</option>
            </select>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { call, toast } from 'frappe-ui'

const props = defineProps({
  session: { type: String, required: true },
  attendance: { type: Array, default: () => [] },
  students: { type: Array, default: () => [] },
})

const emit = defineEmits(['update'])

function getStatus(studentName) {
  const rec = props.attendance.find(a => a.student === studentName)
  return rec ? rec.status : 'Absent'
}

function updateStatus(student, status) {
  emit('update', { student, status })
}
</script>
