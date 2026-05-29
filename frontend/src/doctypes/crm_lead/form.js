export class CRMLead {
  onRender() {
    const existingActions = Array.isArray(this.actions) ? this.actions : []
    const realEstateActionNames = new Set([
      'real_estate_list_resale_unit',
      'real_estate_link_interested_property',
    ])

    const actions = existingActions.filter(
      (action) => !realEstateActionNames.has(action.name),
    )

    if (this.doc.party_type === 'Seller') {
      actions.push({
        name: 'real_estate_list_resale_unit',
        label: __('List Resale Unit'),
        group: __('Actions'),
        onClick: async (close) => {
          await this.openResaleUnitDialog()
          close?.()
        },
      })
    }

    if ((this.doc.party_type || 'Buyer') === 'Buyer') {
      actions.push({
        name: 'real_estate_link_interested_property',
        label: __('Link Interested Property'),
        group: __('Actions'),
        onClick: async (close) => {
          await this.linkInterestedPropertyDialog()
          close?.()
        },
      })
    }

    this.actions = actions
  }

  async openResaleUnitDialog() {
    if (!this.doc?.name) {
      this.toast.error(__('Please save the lead before listing a resale unit.'))
      return
    }

    const data = await this.formDialog({
      title: __('List Resale Unit'),
      size: 'md',
      submitLabel: __('Create Resale Unit'),
      fields: [
        {
          fieldname: 'project',
          label: __('Project'),
          fieldtype: 'Link',
          options: 'Real Estate Project',
          reqd: 1,
        },
        {
          fieldname: 'unit_number',
          label: __('Unit Number'),
          fieldtype: 'Data',
          reqd: 1,
        },
        {
          fieldname: 'price',
          label: __('Price'),
          fieldtype: 'Currency',
        },
      ],
    })

    if (!data) return

    const unit = await this.call(
      'real_estate_crm_customs.api.create_resale_unit',
      {
        owner_lead: this.doc.name,
        project: data.project,
        unit_number: data.unit_number,
        price: data.price,
      },
    )

    if (unit?.name) {
      this.toast.success(__('Resale unit {0} created successfully.', [unit.name]))
    }
  }

  async linkInterestedPropertyDialog() {
    if (!this.doc?.name) {
      this.toast.error(__('Please save the lead before linking interested properties.'))
      return
    }

    const data = await this.formDialog({
      title: __('Link Interested Property'),
      size: 'md',
      submitLabel: __('Link Unit'),
      fields: [
        {
          fieldname: 'unit',
          label: __('Available Unit'),
          fieldtype: 'Link',
          options: 'Real Estate Unit',
          reqd: 1,
          link_filters: JSON.stringify({ status: 'Available' }),
        },
      ],
    })

    if (!data?.unit) return

    const duplicate = (this.doc.interested_in_units || []).some(
      (row) => row.unit === data.unit,
    )
    if (duplicate) {
      this.toast.error(__('This unit is already linked to the lead.'))
      return
    }

    const updatedLead = await this.call(
      'real_estate_crm_customs.api.link_interested_unit',
      {
        lead: this.doc.name,
        unit: data.unit,
      },
    )

    if (updatedLead?.interested_in_units) {
      this.doc.interested_in_units = updatedLead.interested_in_units
    }

    this.toast.success(__('Interested property linked successfully.'))
  }
}
