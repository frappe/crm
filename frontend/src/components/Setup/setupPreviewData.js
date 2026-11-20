import { h } from 'vue'

const avatar = (name) => `/assets/crm/images/demo/${name}.svg`

export const SAMPLE_LEAD = {
  id: 'CRM-LEAD-2026-00042',
  name: 'Daniel Ortiz',
  organization: 'Northwind',
  email: 'daniel.ortiz@example.com',
  subject: __('Re: Pricing for 40 seats'),
  message: [
    __('Hi,'),
    __(
      'We are rolling out to our sales team next month. Could you share pricing for 40 seats and whether onboarding is included?',
    ),
    __('Thanks, Daniel'),
  ],
}

const SAMPLE_AVATARS = {
  [SAMPLE_LEAD.name]: avatar('daniel'),
  'sam@example.com': avatar('sam'),
  'maya@example.com': avatar('maya'),
  'priya@example.com': avatar('priya'),
  'leo@example.com': avatar('leo'),
}

export const avatarUrl = (person) => SAMPLE_AVATARS[person]

export const nameOf = (email) => {
  const local = email.split('@')[0]
  return local.charAt(0).toUpperCase() + local.slice(1)
}

export const STATUS_COLOR = {
  New: 'text-ink-gray-5',
  Contacted: 'text-ink-amber-6',
  Nurture: 'text-ink-blue-5',
  Qualified: 'text-ink-green-6',
  Unqualified: 'text-ink-red-5',
}

const lead = (name, organization, status, owner, modified) => ({
  name,
  organization,
  status,
  owner,
  modified,
  email: `${name
    .split(' ')[0]
    .toLowerCase()}@${organization.toLowerCase()}.com`,
})

export const SAMPLE_LEADS = [
  lead('Ava Thompson', 'Globex', 'Qualified', 'sam@example.com', '25m'),
  lead('Noah Patel', 'Initech', 'Contacted', 'maya@example.com', '1h'),
  lead('Mia Rossi', 'Umbrella', 'New', 'priya@example.com', '3h'),
  lead('Lucas Meyer', 'Hooli', 'Nurture', 'leo@example.com', '5h'),
  lead('Zara Khan', 'Vandelay', 'Unqualified', 'sam@example.com', '1d'),
  lead('Ethan Brooks', 'Stark', 'Contacted', 'priya@example.com', '2d'),
  lead('Chloe Martin', 'Wayne', 'Qualified', 'leo@example.com', '3d'),
]

export const IMPORTED_LEADS = [
  lead('Omar Haddad', 'Tyrell', 'New', '', 'now'),
  lead('Sofia Alvarez', 'Cyberdyne', 'New', '', 'now'),
  lead('Liam Walsh', 'Soylent', 'New', '', 'now'),
  lead('Hana Sato', 'Massive', 'New', '', 'now'),
  lead('Felix Braun', 'Aperture', 'New', '', 'now'),
]

export const StatusDot = () =>
  h('svg', { class: 'size-4 shrink-0', viewBox: '0 0 16 16' }, [
    h('circle', { cx: 8, cy: 8, r: 3.5, fill: 'currentColor' }),
  ])
