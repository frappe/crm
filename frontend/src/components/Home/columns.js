import { recordTitle } from '@/utils/home'

// minmax(0, …) lets cells truncate instead of widening the table past the card
const fr = (n) => `minmax(0,${n}fr)`

// Column definitions shared by Home widgets; `type` picks the renderer in HomeCell.
export const homeColumns = {
  record: () => ({
    key: 'title',
    label: __('Name'),
    width: fr(3),
    getLabel: ({ row }) => recordTitle(row),
  }),
  status: () => ({
    key: 'status',
    label: __('Status'),
    type: 'status',
    width: fr(2),
  }),
  task: () => ({ key: 'title', label: __('Task'), width: fr(3) }),
  taskRecord: () => ({
    key: 'reference_title',
    label: __('Record'),
    width: fr(2),
    getLabel: ({ row }) => row.reference_title || row.reference_docname,
  }),
  taskStatus: () => ({
    key: 'status',
    label: __('Status'),
    type: 'taskStatus',
    width: '5.5rem',
  }),
  priority: () => ({
    key: 'priority',
    label: __('Priority'),
    type: 'priority',
    width: '5.5rem',
  }),
  dueDate: (overdue = false) => ({
    key: 'due_date',
    label: __('Due date'),
    type: 'dueDate',
    width: '9rem',
    overdue,
  }),
  user: (key, label) => ({ key, label, type: 'user', width: fr(2) }),
  timeAgo: (key, label) => ({
    key,
    label,
    type: 'timeAgo',
    width: '6rem',
  }),
}
