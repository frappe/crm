<template>
  <Dialog v-model="show" :title="__('Batch Mark Attendance')">
    <template #body>
      <div class="space-y-4">
        <div class="text-p-sm text-ink-gray-7">{{ __('Set status for all unmarked students') }}</div>
        <div class="flex items-center gap-3">
          <label class="text-p-sm text-ink-gray-7">{{ __('Status') }}:</label>
          <select
            v-model="defaultStatus"
            class="border border-outline-gray-2 rounded-lg px-3 py-1.5 text-p-sm bg-surface-base flex-1"
          >
            <option value="Present">{{ __('Present') }}</option>
            <option value="Absent">{{ __('Absent') }}</option>
            <option value="Late">{{ __('Late') }}</option>
            <option value="Excused">{{ __('Excused') }}</option>
          </select>
        </div>
        <div class="max-h-60 overflow-y-auto border border-outline-gray-1 rounded-lg divide-y divide-outline-gray-1">
          <div v-for="s in students" :key="s.name" class="flex items-center justify-between p-3">
            <span class="text-p-sm text-ink-gray-8">{{ s.name }}</span>
            <Badge v-if="markedStudents.includes(s.name)" :label="__('Marked')" variant="subtle" size="sm" />
          </div>
        </div>
      </div>
    </template>
    <template #actions>
      <Button variant="outline" :label="__('Cancel')" @click="show = false" />
      <Button variant="solid" :label="__('Apply')" @click="apply" :loading="applying" />
    </template>
  </Dialog>
</template>

<script setup>
import { Dialog, Button, Badge, call, toast } from 'frappe-ui'
import { ref } from 'vue'

const props = defineProps({
  session: { type: String, required: true },
  students: { type: Array, default: () => [] },
  markedStudents: { type: Array, default: () => [] },
})

const emit = defineEmits(['applied'])

const show = defineModel()
const defaultStatus = ref('Present')
const applying = ref(false)

async function apply() {
  applying.value = true
  try {
    const list = props.students
      .filter(s => !props.markedStudents.includes(s.name))
      .map(s => ({ student: s.name, status: defaultStatus.value }))

    if (!list.length) {
      toast.error(__('All students already marked'))
      return
    }

    await call('crm.api.lms.batch_mark_attendance', {
      data: { academic_session: props.session, attendance_list: list },
    })
    toast.success(__('Attendance marked'))
    show.value = false
    emit('applied')
  } catch (e) {
    toast.error(e.messages?.[0] || __('Error marking attendance'))
  } finally {
    applying.value = false
  }
}
</script>
