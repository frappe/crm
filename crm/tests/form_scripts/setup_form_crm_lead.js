// A legacy setupForm CRM Form Script on CRM Lead (frappe/frappe#45966).
// A `hits:` comment lists the catalog keys the analysis finds on its line.
function setupForm({ doc, $dialog, router, toast, call, updateField, deleteDoc }) { // hits: legacy-doc
  if (doc.__newDocument) return {} // hits: new-document

  async function checkEmail() {
    const count = await call('frappe.client.get_count', { // hits: call
      doctype: 'CRM Lead',
      filters: { email: doc.email, name: ['!=', doc.name] },
    })
    if (count) toast.error(__('Another lead has this email')) // hits: toast-error, translate
    else toast.success(__('No other lead has this email')) // hits: toast-success, translate
  }

  function confirmDelete() {
    $dialog({ // hits: create-dialog
      title: __('Delete lead'), // hits: translate
      message: __('Delete this lead?'), // hits: translate
      actions: [
        {
          label: __('Delete'), // hits: translate
          theme: 'red',
          variant: 'solid',
          onClick: ({ close }) => {
            close()
            deleteDoc() // hits: delete-doc
          },
        },
      ],
    })
  }

  return {
    actions: [ // hits: header-actions
      {
        label: __('Mark as contacted'), // hits: translate
        onClick: async () => { // hits: action-on-click
          await updateField('status', 'Contacted') // hits: update-field
          toast.success(__('Lead marked as contacted')) // hits: toast-success, translate
        },
      },
      {
        group: __('More'), // hits: action-group, translate
        items: [
          { label: __('Check email'), onClick: () => checkEmail() }, // hits: translate, action-on-click
          { label: __('All deals'), onClick: () => router.push({ name: 'Deals' }) }, // hits: translate, action-on-click, router
          { label: __('Delete'), onClick: () => confirmDelete() }, // hits: translate, action-on-click
        ],
      },
    ],
  }
}
