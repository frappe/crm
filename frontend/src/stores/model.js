import { __ } from '@/translation'

export const STANDARD_FIELDS = [
  { fieldname: 'name', fieldtype: 'Link', label: __('Name') },
  { fieldname: 'creation', fieldtype: 'Datetime', label: __('Created On') },
  {
    fieldname: 'modified',
    fieldtype: 'Datetime',
    label: __('Last Updated On'),
  },
  {
    fieldname: 'modified_by',
    fieldtype: 'Link',
    label: __('Last Updated By'),
    options: 'User',
  },
  {
    fieldname: 'owner',
    fieldtype: 'Link',
    label: __('Owner'),
    options: 'User',
  },
  { fieldname: '_assign', fieldtype: 'Text', label: __('Assigned To') },
  { fieldname: '_liked_by', fieldtype: 'Data', label: __('Like') },
]

export const NO_VALUE_TYPE = [
  'Section Break',
  'Column Break',
  'Tab Break',
  'HTML',
  'Table',
  'Table MultiSelect',
  'Button',
  'Image',
  'Fold',
  'Heading',
]
