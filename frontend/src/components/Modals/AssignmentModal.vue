<template>
  <Dialog
    v-model="show"
    :options="{
      title: 'Assign To',
      size: 'xl',
      actions: [
        {
          label: 'Cancel',
          variant: 'subtle',
          onClick: () => {
            assignees = oldAssignees
            show = false
          },
        },
        {
          label: 'Update',
          variant: 'solid',
          onClick: () => updateAssignees(),
        },
      ],
    }"
  >
    <template #body-content>
      <Link
        class="form-control"
        value=""
        doctype="User"
        @change="(option) => addValue(option) && ($refs.input.value = '')"
      >
        <template #item-prefix="{ option }">
          <UserAvatar class="mr-2" :user="option.value" size="sm" />
        </template>
        <template #item-label="{ option }">
          <Tooltip :text="option.value">
            {{ getUser(option.value).full_name }}
          </Tooltip>
        </template>
      </Link>
      <div class="mt-3 flex flex-wrap items-center gap-2">
        <Tooltip
          :text="assignee.name"
          v-for="assignee in assignees"
          :key="assignee.name"
        >
          <Button
            :label="getUser(assignee.name).full_name"
            theme="gray"
            variant="outline"
          >
            <template #prefix>
              <UserAvatar :user="assignee.name" size="sm" />
            </template>
            <template #suffix>
              <FeatherIcon
                v-if="assignee.name !== owner"
                class="h-3.5"
                name="x"
                @click.stop="removeValue(assignee.name)"
              />
            </template>
          </Button>
        </Tooltip>
      </div>
      <ErrorMessage class="mt-2" v-if="error" :message="error" />
    </template>
  </Dialog>
</template>

<script setup>
import UserAvatar from '@/components/UserAvatar.vue'
import Link from '@/components/Controls/Link.vue'
import { usersStore } from '@/stores/users'
import { Tooltip, call } from 'frappe-ui'
import { defineModel, ref, computed } from 'vue'
import { watchOnce } from '@vueuse/core'

const props = defineProps({
  doc: {
    type: Object,
    default: null,
  },
})

const show = defineModel()
const assignees = defineModel('assignees')
const oldAssignees = ref([])

const error = ref('')

const { getUser } = usersStore()

const removeValue = (value) => {
  assignees.value = assignees.value.filter(
    (assignee) => assignee.name !== value
  )
}

const owner = computed(() => {
  if (!props.doc) return ''
  if (props.doc.doctype == 'CRM Lead') return props.doc.lead_owner
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

function updateAssignees() {
  if (assignees.value.length === 0) {
    error.value = 'Please select at least one assignee'
    return
  }
  const removedAssignees = oldAssignees.value
    .filter(
      (assignee) => !assignees.value.find((a) => a.name === assignee.name)
    )
    .map((assignee) => assignee.name)

  const addedAssignees = assignees.value
    .filter(
      (assignee) => !oldAssignees.value.find((a) => a.name === assignee.name)
    )
    .map((assignee) => assignee.name)

  if (removedAssignees.length) {
    for (let a of removedAssignees) {
      call('frappe.desk.form.assign_to.remove', {
        doctype: props.doc.doctype,
        name: props.doc.name,
        assign_to: a,
      })
    }
  }

  if (addedAssignees.length) {
    call('frappe.desk.form.assign_to.add', {
      doctype: props.doc.doctype,
      name: props.doc.name,
      assign_to: addedAssignees,
    })
  }
  show.value = false
}

watchOnce(assignees, (value) => {
  oldAssignees.value = [...value]
})
</script>
