<template>
  <span :class="['inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium', pillClass]">
    <span v-html="iconSvg" class="w-3 h-3 flex-shrink-0" />
    {{ status }}
  </span>
</template>

<script setup>
const props = defineProps({
  status: { type: String, default: '' },
})

const STATUS_MAP = {
  'Paid': {
    pillClass: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    iconSvg: '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
  },
  'Unpaid': {
    pillClass: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
    iconSvg: '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/></svg>',
  },
  'Partly Paid': {
    pillClass: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
    iconSvg: '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.1 2.18A10 10 0 0 1 22 12"/><path d="M10.1 2.18A10 10 0 0 0 2.18 10.1"/><circle cx="12" cy="12" r="3"/></svg>',
  },
  'Overdue': {
    pillClass: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    iconSvg: '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
  },
  'Draft': {
    pillClass: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400',
    iconSvg: '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>',
  },
  'Cancelled': {
    pillClass: 'bg-red-50 text-red-600 dark:bg-red-900/20 dark:text-red-400 border border-red-300 dark:border-red-700',
    iconSvg: '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/></svg>',
  },
  'Submitted': {
    pillClass: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    iconSvg: '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>',
  },
  // Rebate Voucher statuses
  'Pending': {
    pillClass: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
    iconSvg: '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
  },
  'Approved': {
    pillClass: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    iconSvg: '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
  },
  'Rejected': {
    pillClass: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    iconSvg: '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/></svg>',
  },
  // Sales Commission statuses
  'Reported': {
    pillClass: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    iconSvg: '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>',
  },
  'Confirmed': {
    pillClass: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    iconSvg: '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
  },
  // Bank Transaction statuses
  'Unreconciled': {
    pillClass: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
    iconSvg: '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>',
  },
  'Reconciled': {
    pillClass: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    iconSvg: '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
  },
}

const config = STATUS_MAP[props.status] || {
  pillClass: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400',
  iconSvg: '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/></svg>',
}
const { pillClass, iconSvg } = config
</script>
