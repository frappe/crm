<template>
  <NestedPopover>
    <template #target>
      <div class="flex items-center">
        <component
          v-if="assignees?.length"
          :is="assignees?.length == 1 ? 'Button' : 'div'"
        >
          <MultipleAvatar :avatars="assignees" />
        </component>
        <Button v-else :label="__('Assign to')" />
      </div>
    </template>
    <template #body="{ open }">
      <AssignToBody
        v-show="open"
        v-model="assignees"
        :docname="docname"
        :doctype="doctype"
        :open="open"
        :onUpdate="ownerField && saveAssignees"
      />
    </template>
  </NestedPopover>
</template>
<script setup>
import NestedPopover from '@/components/NestedPopover.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import AssignToBody from '@/components/AssignToBody.vue'
import { useDocument } from '@/data/document'
import { toast } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  doctype: String,
  docname: String,
})

const { document } = useDocument(props.doctype, props.docname)

const assignees = defineModel()

const ownerField = computed(() => {
  if (props.doctype === 'CRM Lead') {
    return 'lead_owner'
  } else if (props.doctype === 'CRM Deal') {
    return 'deal_owner'
  } else {
    return null
  }
})

async function saveAssignees(
  addedAssignees,
  removedAssignees,
  addAssignees,
  removeAssignees,
) {
  removedAssignees.length && (await removeAssignees.submit(removedAssignees))
  addedAssignees.length && (await addAssignees.submit(addedAssignees))

  const nextAssignee = assignees.value.find(
    (a) => a.name !== document.doc[ownerField.value],
  )

  let owner = ownerField.value.replace('_', ' ')

  if (
    document.doc[ownerField.value] &&
    removedAssignees.includes(document.doc[ownerField.value])
  ) {
    document.doc[ownerField.value] = nextAssignee ? nextAssignee.name : ''
    document.save.submit()

    if (nextAssignee) {
      toast.info(
        __(
          'Since you removed {0} from the assignee, the {0} has been changed to the next available assignee {1}.',
          [owner, nextAssignee.label || nextAssignee.name],
        ),
      )
    } else {
      toast.info(
        __(
          'Since you removed {0} from the assignee, the {0} has also been removed.',
          [owner],
        ),
      )
    }
  } else if (!document.doc[ownerField.value] && nextAssignee) {
    document.doc[ownerField.value] = nextAssignee ? nextAssignee.name : ''
    toast.info(
      __('Since you added a new assignee, the {0} has been set to {1}.', [
        owner,
        nextAssignee.label || nextAssignee.name,
      ]),
    )
  }
}
</script>
