import { reactive } from 'vue'
import { toast } from 'frappe-ui'

export function useDragDrop({ onReparent }) {
  const dragState = reactive({ source: null, hover: null, blocked: false })

  function isDescendant(srcNode, name) {
    const stack = [...(srcNode.children || [])]
    while (stack.length) {
      const n = stack.pop()
      if (n.name === name) return true
      stack.push(...(n.children || []))
    }
    return false
  }

  function canDrop(src, tgt) {
    if (!src || !tgt || src.name === tgt.name) return false
    if (src.role_rank < tgt.role_rank) return false
    if (isDescendant(src, tgt.name)) return false
    return true
  }

  function onDragStart(e, node) {
    if (!node.reports_to) {
      e.preventDefault()
      return
    }
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', node.name)
    dragState.source = node
  }

  function onDragEnd() {
    dragState.source = null
    dragState.hover = null
    dragState.blocked = false
  }

  function onDragOver(e, node) {
    if (!dragState.source) return
    const ok = canDrop(dragState.source, node)
    dragState.hover = node.name
    dragState.blocked = !ok
    e.dataTransfer.dropEffect = ok ? 'move' : 'none'
  }

  function onDragLeave(node) {
    if (dragState.hover === node.name) {
      dragState.hover = null
      dragState.blocked = false
    }
  }

  async function onDrop(target) {
    const src = dragState.source
    onDragEnd()
    if (!src || !target || src.name === target.name) return
    if (!canDrop(src, target)) {
      toast.error(
        src.role_rank < target.role_rank
          ? __('A {0} cannot report to a {1}.', [
              src.role_label,
              target.role_label,
            ])
          : __('Cannot move a manager under one of their own reports.'),
      )
      return
    }
    await onReparent(src.name, target.name)
  }

  function rowClasses(node) {
    if (dragState.source?.name === node.name) return 'opacity-40'
    if (dragState.hover === node.name) {
      return dragState.blocked
        ? 'bg-surface-red-1 outline outline-1  outline-red-400'
        : 'bg-surface-blue-1 outline outline-1  outline-blue-600'
    }
    return ''
  }

  const handlers = { onDragStart, onDragEnd, onDragOver, onDragLeave, onDrop }

  return { handlers, rowClasses }
}
