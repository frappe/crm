// Role keys used in visibleRoles:
//   'ar'  = Finance Manager + AR Accountant (Accounts User/Manager)
//   'ap'  = Finance Manager + AP Accountant (Accounts User/Manager)
//   'fm'  = Finance Manager only
//   'all' = all finance roles (Finance Manager + AR + AP)
export const SIDEBAR_SECTIONS = [
  { key: 'dashboard',          label: 'Dashboard',            icon: 'layout-dashboard', hash: '#/dashboard',           visibleRoles: 'all' },
  { key: 'inbox',              label: 'Inbox',                icon: 'inbox',             hash: '#/inbox',               visibleRoles: 'all', badge: true },
  { key: 'receivables',        label: 'Receivables',          icon: 'receipt',           hash: '#/receivables',         visibleRoles: 'ar' },
  { key: 'payables',           label: 'Payables',             icon: 'credit-card',       hash: '#/payables',            visibleRoles: 'ap' },
  { key: 'expenses',           label: 'Expenses',             icon: 'wallet',            hash: '#/expenses',            visibleRoles: 'ap' },
  { key: 'assets',             label: 'Assets',               icon: 'building-2',        hash: '#/assets',              visibleRoles: 'fm' },
  { key: 'banking',            label: 'Banking',              icon: 'landmark',          hash: '#/banking',             visibleRoles: 'all' },
  { key: 'liabilities',        label: 'Liabilities',          icon: 'scale',             hash: '#/liabilities',         visibleRoles: 'fm' },
  { key: 'general_ledger',     label: 'General Ledger',       icon: 'book-open',         hash: '#/general-ledger',      visibleRoles: 'fm' },
  { key: 'reports',            label: 'Reports',              icon: 'bar-chart-2',       hash: '#/reports',             visibleRoles: 'all' },
  { key: 'partner_commission', label: 'Partner & Commission', icon: 'handshake',         hash: '#/partner-commission',  visibleRoles: 'all' },
  { key: 'setup',              label: 'Setup',                icon: 'settings',          hash: '#/setup',               visibleRoles: 'fm' },
]
