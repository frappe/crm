<template>
  <Dialog
    v-model="show"
    :options="{ title: __('Assign to'), size: 'xl' }"
    @close="() => (assignees = [...oldAssignees])"
  >
    <template #body-content>
      <Link
        class="form-control"
        value=""
        doctype="User"
        @change="(option) => addValue(option) && ($refs.input.value = '')"
        :placeholder="__('John Doe')"
        :filters="{
          name: ['in', users.data.crmUsers?.map((user) => user.name)],
        }"
        :hideMe="true"
      >
        <template #target="{ togglePopover }">
          <div
            class="w-full min-h-12 flex flex-wrap items-center gap-1.5 p-1.5 pb-5 rounded-lg bg-surface-gray-2 cursor-text"
            @click.stop="togglePopover"
          >
            <Tooltip
              :text="assignee.name"
              v-for="assignee in assignees"
              :key="assignee.name"
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
                      <FeatherIcon name="x" class="h-3 w-3 text-ink-gray-6" />
                    </template>
                  </Button>
                </div>
              </div>
            </Tooltip>
          </div>
        </template>
        <template #item-prefix="{ option }">
          <UserAvatar class="mr-2" :user="option.value" size="sm" />
        </template>
        <template #item-label="{ option }">
          <Tooltip :text="option.value">
            <div class="cursor-pointer text-ink-gray-9">
              {{ getUser(option.value).full_name }}
            </div>
          </Tooltip>
        </template>
      </Link>
    </template>
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
import Link from '@/components/Controls/Link.vue'
import { usersStore } from '@/stores/users'
import { capture } from '@/telemetry'
import { Tooltip, call } from 'frappe-ui'
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  doc: {
    type: Object,
    default: null,
  },
  docs: {
    type: Set,
    default: new Set(),
  },
  doctype: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['reload'])

const show = defineModel()
const assignees = defineModel('assignees')
const oldAssignees = ref([])

const error = ref('')

const { users, getUser } = usersStore()

const removeValue = (value) => {
  assignees.value = assignees.value.filter(
    (assignee) => assignee.name !== value,
  )
}

const owner = computed(() => {
  if (!props.doc) return ''
  if (props.doctype == 'CRM Lead') return props.doc.lead_owner
  return props.doc.deal_owner
})

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
      })
    }
  }
  show.value = false
}

onMounted(() => {
  oldAssignees.value = [...assignees.value]
})
</script>
