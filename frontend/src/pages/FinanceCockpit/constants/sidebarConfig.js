// CRM-Finance sidebar — 7 sections
// iconClass must be a full static lucide-* Tailwind class (JIT requires static strings).
export const SIDEBAR_SECTIONS = [
  { key: 'dashboard',          label: 'Dashboard',            iconClass: 'lucide-layout-dashboard', hash: '#/dashboard',           visibleRoles: 'all' },
  { key: 'quotes',             label: 'Quotes',               iconClass: 'lucide-file-text',        hash: '#/quotes',              visibleRoles: 'all' },
  { key: 'orders',             label: 'Orders',               iconClass: 'lucide-shopping-cart',    hash: '#/orders',              visibleRoles: 'all' },
  { key: 'invoices',           label: 'Invoices',             iconClass: 'lucide-receipt',          hash: '#/invoices',            visibleRoles: 'all' },
  { key: 'payments',           label: 'Payments',             iconClass: 'lucide-banknote',         hash: '#/payments',            visibleRoles: 'all' },
  { key: 'partner_commission', label: 'Partner & Commission', iconClass: 'lucide-handshake',        hash: '#/partner-commission',  visibleRoles: 'all' },
  { key: 'reports',            label: 'Reports',              iconClass: 'lucide-bar-chart-2',      hash: '#/reports',             visibleRoles: 'all' },
]
