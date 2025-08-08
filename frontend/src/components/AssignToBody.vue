<template>
  <div
    class="flex flex-col gap-2 my-2 w-[470px] rounded-lg bg-surface-modal shadow-2xl ring-1 ring-black p-3 ring-opacity-5 focus:outline-none"
  >
    <div class="text-base text-ink-gray-5">{{ __('Assign to') }}</div>
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
                class="flex items-center text-sm p-0.5 text-ink-gray-6 border border-outline-gray-1 bg-surface-modal rounded-full cursor-pointer"
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
    <div class="flex items-center justify-between gap-2">
      <div
        class="text-base text-ink-gray-5 cursor-pointer select-none"
        @click="assignToMe = !assignToMe"
      >
        {{ __('Assign to me') }}
      </div>
      <Switch v-model="assignToMe" @click.stop />
    </div>
  </div>
</template>

<script setup>
import UserAvatar from '@/components/UserAvatar.vue'
import Link from '@/components/Controls/Link.vue'
import { usersStore } from '@/stores/users'
import { capture } from '@/telemetry'
import { Tooltip, Switch, toast, createResource } from 'frappe-ui'
import { ref, watch } from 'vue'

const props = defineProps({
  doctype: {
    type: String,
    default: '',
  },
  docname: {
    type: Object,
    default: null,
  },
  open: {
    type: Boolean,
    default: false,
  },
  onUpdate: {
    type: Function,
    default: null,
  },
})

const emit = defineEmits(['reload'])

const assignees = defineModel()
const oldAssignees = ref([])
const assignToMe = ref(false)

const error = ref('')

const { users, getUser } = usersStore()

const removeValue = (value) => {
  if (value === getUser('').name) {
    assignToMe.value = false
  }

  assignees.value = assignees.value.filter(
    (assignee) => assignee.name !== value,
  )
}

const addValue = (value) => {
  if (value === getUser('').name) {
    assignToMe.value = true
  }

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

watch(assignToMe, (val) => {
  let user = getUser('')
  if (val) {
    addValue(user.name)
  } else {
    removeValue(user.name)
  }
})

watch(
  () => props.open,
  (val) => {
    if (val) {
      oldAssignees.value = [...(assignees.value || [])]

      assignToMe.value = assignees.value.some(
        (assignee) => assignee.name === getUser('').name,
      )
    } else {
      updateAssignees()
    }
  },
)

async function updateAssignees() {
  if (JSON.stringify(oldAssignees.value) === JSON.stringify(assignees.value))
    return

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

  if (props.onUpdate) {
    props.onUpdate(
      addedAssignees,
      removedAssignees,
      addAssignees,
      removeAssignees,
    )
  } else {
    if (removedAssignees.length) {
      await removeAssignees.submit(removedAssignees)
    }
    if (addedAssignees.length) {
      addAssignees.submit(addedAssignees)
    }
  }
}

const addAssignees = createResource({
  url: 'frappe.desk.form.assign_to.add',
  makeParams: (addedAssignees) => ({
    doctype: props.doctype,
    name: props.docname,
    assign_to: addedAssignees,
  }),
  onSuccess: () => {
    capture('assign_to', { doctype: props.doctype })
  },
})

const removeAssignees = createResource({
  url: 'crm.api.doc.remove_assignments',
  makeParams: (removedAssignees) => ({
    doctype: props.doctype,
    name: props.docname,
    assignees: removedAssignees,
  }),
})
</script>
