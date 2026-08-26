import { computed, reactive } from 'vue'
import { toast } from 'frappe-ui'

export function useDragDrop({ onReparent }) {
  const dragState = reactive({
    source: null,
    hover: null,
    hoverNode: null,
    x: 0,
    y: 0,
  })

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
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', node.name)
    dragState.source = node
  }

  function onDragEnd() {
    dragState.source = null
    dragState.hover = null
    dragState.hoverNode = null
  }

  function onDragOver(e, node) {
    if (!dragState.source) return
    dragState.hover = node.name
    dragState.hoverNode = node
    dragState.x = e.clientX
    dragState.y = e.clientY
    e.dataTransfer.dropEffect = 'move'
  }

  function onDragLeave(node) {
    if (dragState.hover === node.name) {
      dragState.hover = null
      dragState.hoverNode = null
    }
  }

  async function onDrop(target) {
    const src = dragState.source
    onDragEnd()
    if (!src || !target || src.name === target.name) return
    if (src.reports_to === target.name) {
      toast.info(__('No changes made'))
      return
    }
    if (!canDrop(src, target)) {
      toast.error(
        src.role_rank < target.role_rank
          ? __('A {0} cannot report to a {1}', [
              src.role_label,
              target.role_label,
            ])
          : __('Cannot move a manager under one of their own reports'),
      )
      return
    }
    await onReparent(src.name, target.name)
  }

  function rowClasses(node) {
    const src = dragState.source
    if (!src) return ''
    if (src.name === node.name) return 'opacity-40'
    if (!canDrop(src, node)) {
      return 'opacity-50 [&_span]:line-through'
    }
    if (dragState.hover === node.name) {
      return 'border-b !border-blue-500 rounded-none'
    }
    return ''
  }

  const dragLabel = computed(() => {
    const src = dragState.source
    const tgt = dragState.hoverNode
    if (!src || !tgt) return null
    if (src.name === tgt.name) return null
    if (src.reports_to === tgt.name) return null
    if (!canDrop(src, tgt)) return null
    return __('Move under {0}', [tgt.full_name])
  })

  const handlers = { onDragStart, onDragEnd, onDragOver, onDragLeave, onDrop }

  return { handlers, rowClasses, dragState, dragLabel }
}
