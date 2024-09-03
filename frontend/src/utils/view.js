import ListIcon from '@/components/Icons/ListIcon.vue'
import GroupByIcon from '@/components/Icons/GroupByIcon.vue'
import KanbanIcon from '@/components/Icons/KanbanIcon.vue'
import { viewsStore } from '@/stores/views'
import { markRaw } from 'vue'

const { getView: getViewDetails } = viewsStore()

function defaultView(type) {
  let types = {
    list: {
      label: __('List'),
      icon: markRaw(ListIcon),
    },
    group_by: {
      label: __('Group By'),
      icon: markRaw(GroupByIcon),
    },
    kanban: {
      label: __('Kanban'),
      icon: markRaw(KanbanIcon),
    },
  }

  return types[type]
}

export function getView(view, type, doctype) {
  let viewType = type || 'list'
  let viewDetails = getViewDetails(view, viewType, doctype)
  if (viewDetails && !viewDetails.icon) {
    viewDetails.icon = defaultView(viewType).icon
  }
  return viewDetails || defaultView(viewType)
}
