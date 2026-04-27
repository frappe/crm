import { call, toast } from 'frappe-ui'
import { globalStore } from '@/stores/global'

export function useRemoveNode({ doctype, nodes, enrichedNodes }) {
  const { $dialog } = globalStore()

  function removeNode(node) {
    const directChildren = enrichedNodes.value.filter(
      (n) => n.reports_to === node.name,
    )

    if (!directChildren.length) {
      confirmSimpleRemove(node)
      return
    }

    $dialog({
      title: __('Remove from hierarchy'),
      message: __('{0} has {1} direct report(s). Choose how to handle them.', [
        node.full_name,
        directChildren.length,
      ]),
      variant: 'danger',
      actions: [
        {
          label: __('Reassign & Delete'),
          variant: 'subtle',
          onClick: ({ close }) =>
            runRemoval(close, () => reassignAndRemove(node, directChildren)),
        },
        {
          label: __('Delete all reports'),
          variant: 'solid',
          theme: 'red',
          onClick: ({ close }) =>
            runRemoval(close, () => removeWithDescendants(node)),
        },
      ],
    })
  }

  function confirmSimpleRemove(node) {
    $dialog({
      title: __('Remove from hierarchy'),
      message: __('Are you sure you want to remove {0} from the hierarchy?', [
        node.full_name,
      ]),
      variant: 'danger',
      actions: [
        {
          label: __('Remove'),
          variant: 'solid',
          theme: 'red',
          onClick: ({ close }) => {
            nodes.delete.submit(node.name, {
              onSuccess: () => {
                toast.success(__('Removed from hierarchy.'))
                close()
              },
              onError: (error) => {
                toast.error(error.messages?.[0] || __('Could not remove.'))
                close()
              },
            })
          },
        },
      ],
    })
  }

  async function runRemoval(close, task) {
    try {
      await task()
      toast.success(__('Removed from hierarchy.'))
      nodes.reload()
    } catch (e) {
      toast.error(e?.messages?.[0] || __('Could not remove.'))
    } finally {
      close()
    }
  }

  async function reassignAndRemove(node, children) {
    for (const child of children) {
      await call('frappe.client.set_value', {
        doctype,
        name: child.name,
        fieldname: 'reports_to',
        value: node.reports_to || '',
      })
    }
    await call('frappe.client.delete', { doctype, name: node.name })
  }

  async function removeWithDescendants(node) {
    const toDelete = []
    const visit = (n) => {
      const kids = enrichedNodes.value.filter((x) => x.reports_to === n.name)
      kids.forEach(visit)
      toDelete.push(n)
    }
    visit(node)
    for (const d of toDelete) {
      await call('frappe.client.delete', { doctype, name: d.name })
    }
  }

  return { removeNode }
}
