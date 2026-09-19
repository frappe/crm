import ListIcon from '@/components/Icons/ListIcon.vue'
import GroupByIcon from '@/components/Icons/GroupByIcon.vue'
import KanbanIcon from '@/components/Icons/KanbanIcon.vue'
import { viewsStore } from '@/stores/views'
import { markRaw } from 'vue'

const { getView: getViewDetails } = viewsStore()

function standardView(type) {
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
    viewDetails.icon = standardView(viewType).icon
  }
  return viewDetails || standardView(viewType)
}

export const DEFAULT_PAGE_LENGTH = 20

/**
 * Page size for a list request, defaulting when there is nothing to read yet.
 *
 * List views take their page size from the previous response, so on a cold
 * load the value is undefined. Left as-is it survives into the next "load
 * more", where `page_length + page_length_count` becomes NaN and serialises to
 * null -- which get_data rejects, since null overrides the Python default.
 */
export function resolvePageLength(value) {
  const count = Number(value)
  return Number.isFinite(count) && count > 0
    ? Math.floor(count)
    : DEFAULT_PAGE_LENGTH
}
