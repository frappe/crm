export const SIDEBAR_SECTIONS = [
  { key: 'dashboard',          label: 'Dashboard',           icon: 'layout-dashboard', hash: '#/dashboard' },
  { key: 'inbox',              label: 'Inbox',               icon: 'inbox',             hash: '#/inbox',       badge: true },
  { key: 'receivables',        label: 'Receivables',         icon: 'receipt',           hash: '#/receivables' },
  { key: 'payables',           label: 'Payables',            icon: 'credit-card',       hash: '#/payables' },
  { key: 'expenses',           label: 'Expenses',            icon: 'wallet',            hash: '#/expenses' },
  { key: 'assets',             label: 'Assets',              icon: 'building-2',        hash: '#/assets' },
  { key: 'banking',            label: 'Banking',             icon: 'landmark',          hash: '#/banking' },
  { key: 'liabilities',        label: 'Liabilities',         icon: 'scale',             hash: '#/liabilities' },
  { key: 'general_ledger',     label: 'General Ledger',      icon: 'book-open',         hash: '#/general-ledger' },
  { key: 'reports',            label: 'Reports',             icon: 'bar-chart-2',       hash: '#/reports' },
  { key: 'partner_commission', label: 'Partner & Commission',icon: 'handshake',         hash: '#/partner-commission' },
  { key: 'setup',              label: 'Setup',               icon: 'settings',          hash: '#/setup',       financeManagerOnly: true },
]
