import { call, toast } from 'frappe-ui'

export function useRemoveNode({ doctype, nodes, enrichedNodes }) {
  async function removeNode(node, mode = 'simple') {
    try {
      if (mode === 'reassign') {
        await reassignAndRemove(node)
      } else if (mode === 'cascade') {
        await removeWithDescendants(node)
      } else {
        await call('frappe.client.delete', { doctype, name: node.name })
      }
      toast.success(__('Removed from hierarchy.'))
      nodes.reload()
    } catch (e) {
      toast.error(e?.messages?.[0] || __('Could not remove.'))
    }
  }

  async function reassignAndRemove(node) {
    const children = enrichedNodes.value.filter(
      (n) => n.reports_to === node.name,
    )
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
