<template>
  <Dialog
    v-model:open="show"
    :title="__('Assign To')"
    size="xl"
    @close="() => (assignees = [...oldAssignees])"
  >
    <Link
      v-model="selectedUser"
      class="form-control"
      doctype="User"
      :placeholder="__('John Doe')"
      :filters="{
        name: ['in', users.data.crmUsers?.map((user) => user.name)],
        ignore_user_type: 1,
      }"
      @update:modelValue="
        (v) => {
          if (v) {
            addValue(v)
            selectedUser = null
          }
        }
      "
    >
      <template #trigger>
        <div
          class="w-full min-h-12 flex flex-wrap items-center gap-1.5 p-1.5 pb-5 rounded-lg bg-surface-gray-2 cursor-text"
        >
          <Tooltip
            v-for="assignee in assignees"
            :key="assignee.name"
            :text="assignee.name"
            @click.stop
          >
            <div>
              <div
                class="flex items-center text-sm text-ink-gray-6 border border-outline-gray-1 bg-surface-white rounded-full hover:bg-surface-white !p-0.5"
                @click.stop
              >
                <UserAvatar :user="assignee.name" size="sm" />
                <div class="ml-1">{{ getUser(assignee.name).full_name }}</div>
                <Button
                  variant="ghost"
                  class="rounded-full !size-4 m-1"
                  @click.stop="removeValue(assignee.name)"
                >
                  <template #icon>
                    <span
                      class="lucide-x size-3 text-ink-gray-6"
                      aria-hidden="true"
                    />
                  </template>
                </Button>
              </div>
            </div>
          </Tooltip>
        </div>
      </template>
      <template #item-prefix="{ item }">
        <UserAvatar class="mr-1" :user="item.value" size="sm" />
      </template>
    </Link>
    <template #actions>
      <div class="flex justify-between items-center gap-2">
        <div><ErrorMessage :message="__(error)" /></div>
        <div class="flex items-center justify-end gap-2">
          <Button
            variant="subtle"
            :label="__('Cancel')"
            @click="
              () => {
                assignees = [...oldAssignees]
                show = false
              }
            "
          />
          <Button
            variant="solid"
            :label="__('Update')"
            @click="updateAssignees()"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import UserAvatar from '@/components/UserAvatar.vue'
import { usersStore } from '@/stores/users'
import { useTelemetry, Link } from 'frappe-ui/frappe'
import { Tooltip, call } from 'frappe-ui'
import { ref, onMounted } from 'vue'

const props = defineProps({
  doc: { type: Object, default: null },
  docs: { type: Set, default: () => new Set() },
  doctype: { type: String, default: '' },
})

const emit = defineEmits(['reload'])

const show = defineModel({ type: Boolean })
const assignees = defineModel('assignees', { type: Array, default: () => [] })
const oldAssignees = ref([])
const selectedUser = ref(null)

const error = ref('')

const { users, getUser } = usersStore()
const { capture } = useTelemetry()

const removeValue = (value) => {
  assignees.value = assignees.value.filter(
    (assignee) => assignee.name !== value,
  )
}

const addValue = (value) => {
  error.value = ''
  let obj = {
    name: value,
    image: getUser(value).user_image,
    label: getUser(value).full_name,
  }
  if (!assignees.value.find((assignee) => assignee.name === value)) {
    assignees.value.push(obj)
  }
}

async function updateAssignees() {
  const removedAssignees = oldAssignees.value
    .filter(
      (assignee) => !assignees.value.find((a) => a.name === assignee.name),
    )
    .map((assignee) => assignee.name)

  const addedAssignees = assignees.value
    .filter(
      (assignee) => !oldAssignees.value.find((a) => a.name === assignee.name),
    )
    .map((assignee) => assignee.name)

  if (removedAssignees.length) {
    await call('crm.api.doc.remove_assignments', {
      doctype: props.doctype,
      name: props.doc.name,
      assignees: JSON.stringify(removedAssignees),
    })
  }

  if (addedAssignees.length) {
    if (props.docs.size) {
      capture('bulk_assign_to', { doctype: props.doctype })
      call('frappe.desk.form.assign_to.add_multiple', {
        doctype: props.doctype,
        name: JSON.stringify(Array.from(props.docs)),
        assign_to: addedAssignees,
        bulk_assign: true,
        re_assign: true,
      }).then(() => {
        emit('reload')
      })
    } else {
      capture('assign_to', { doctype: props.doctype })
      call('frappe.desk.form.assign_to.add', {
        doctype: props.doctype,
        name: props.doc.name,
        assign_to: addedAssignees,
      }).then(() => {
        emit('reload')
      })
    }
  }
  show.value = false
}

onMounted(() => {
  oldAssignees.value = [...assignees.value]
})
</script>
