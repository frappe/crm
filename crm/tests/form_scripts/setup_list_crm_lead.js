// A setupList CRM Form Script on the CRM Lead list (frappe/frappe#45966).
// A `hits:` comment lists the catalog keys the analysis finds on its line.
function setupList({ list, call, toast }) {
  return {
    actions: [ // hits: list-actions
      { label: __('Reload'), onClick: () => list.reload() }, // hits: translate
    ],
    bulk_actions: [ // hits: list-bulk-actions
      {
        label: __('Mark as contacted'), // hits: translate
        onClick: async ({ selections, unselectAll }) => {
          for (const name of selections) {
            await call('frappe.client.set_value', { // hits: call
              doctype: 'CRM Lead',
              name,
              fieldname: 'status',
              value: 'Contacted',
            })
          }
          toast.success(__('Leads marked as contacted')) // hits: toast-success, translate
          unselectAll()
          list.reload()
        },
      },
    ],
  }
}
