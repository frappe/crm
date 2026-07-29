import { call, toast } from 'frappe-ui'
import { validateEmail, validatePhone } from '@/utils'

// Shared email/mobile/address side-panel field logic for Contact.vue (desktop)
// and MobileContact.vue. Emails and phones render as `Dropdown` fields; new
// entries are created through PrimaryDropdown's own draft rows, so an incomplete
// value never reaches contact.doc (and never leaks into an auto-save).

interface ContactDoc {
  name: string
  email_id?: string
  mobile_no?: string
  email_ids?: { name: string; email_id: string }[]
  phone_nos?: { name: string; phone: string }[]
}

interface ContactDocument {
  doc: ContactDoc
  reload: () => Promise<unknown>
}

interface DropdownOption {
  name: string
  value: string
  selected: boolean
  onClick?: () => void
  onSave: (option: DropdownOption) => void
  onDelete: (option: DropdownOption) => void
}

type SidePanelField = Record<string, unknown> & { fieldname?: string }

export function useContactFields(contact: ContactDocument) {
  // 'email' | 'mobile_no' (setAsPrimary) and 'email' | 'phone' (createNew)
  const isEmailField = (field: string) => field === 'email'
  const isEmailDoctype = (doctype: string) => doctype === 'Contact Email'

  async function reloadWithToast(message: string) {
    await contact.reload()
    toast.success(message)
  }

  async function setAsPrimary(field: string, value: string) {
    const updated = await call('crm.api.contact.set_as_primary', {
      contact: contact.doc.name,
      field,
      value,
    })
    if (updated)
      reloadWithToast(
        isEmailField(field)
          ? __('Primary email address updated')
          : __('Primary mobile number updated'),
      )
  }

  async function createNew(field: string, value: string) {
    if (!value) return false
    const created = await call('crm.api.contact.create_new', {
      contact: contact.doc.name,
      field,
      value,
    })
    if (created)
      reloadWithToast(
        isEmailField(field)
          ? __('Email address added')
          : __('Mobile number added'),
      )
    return Boolean(created)
  }

  async function editOption(
    doctype: string,
    name: string,
    fieldname: string,
    value: string,
  ) {
    const updated = await call('frappe.client.set_value', {
      doctype,
      name,
      fieldname,
      value,
    })
    if (updated)
      reloadWithToast(
        isEmailDoctype(doctype)
          ? __('Email address updated')
          : __('Mobile number updated'),
      )
    return Boolean(updated)
  }

  async function deleteOption(doctype: string, name: string) {
    await call('frappe.client.delete', { doctype, name })
    reloadWithToast(
      isEmailDoctype(doctype)
        ? __('Email address removed')
        : __('Mobile number removed'),
    )
  }

  const validateEmailOption = (value: string) =>
    validateEmail(value) ? '' : __('Please enter a valid email address')

  const validatePhoneOption = (value: string) =>
    validatePhone(value) ? '' : __('Please enter a valid phone number')

  function emailOptions(): DropdownOption[] {
    return (contact.doc?.email_ids || []).map((email) => ({
      name: email.name,
      value: email.email_id,
      selected: email.email_id === contact.doc.email_id,
      onClick: () => setAsPrimary('email', email.email_id),
      onSave: (option) =>
        editOption('Contact Email', option.name, 'email_id', option.value),
      onDelete: async (option) => {
        contact.doc.email_ids = contact.doc.email_ids?.filter(
          (e) => e.name !== option.name,
        )
        await deleteOption('Contact Email', option.name)
      },
    }))
  }

  function phoneOptions(): DropdownOption[] {
    return (contact.doc?.phone_nos || []).map((phone) => ({
      name: phone.name,
      value: phone.phone,
      selected: phone.phone === contact.doc.mobile_no,
      onClick: () => setAsPrimary('mobile_no', phone.phone),
      onSave: (option) =>
        editOption('Contact Phone', option.name, 'phone', option.value),
      onDelete: async (option) => {
        contact.doc.phone_nos = contact.doc.phone_nos?.filter(
          (p) => p.name !== option.name,
        )
        await deleteOption('Contact Phone', option.name)
      },
    }))
  }

  return function transformField(
    field: SidePanelField,
    {
      showAddressModal,
    }: { showAddressModal?: (address?: string) => void } = {},
  ): SidePanelField {
    if (field.fieldname === 'email_id') {
      return {
        ...field,
        read_only: false,
        fieldtype: 'Dropdown',
        itemPlaceholder: 'john@doe.com',
        validate: validateEmailOption,
        options: emailOptions(),
        onCreate: (value: string) => createNew('email', value),
      }
    }
    if (field.fieldname === 'mobile_no') {
      return {
        ...field,
        read_only: false,
        fieldtype: 'Dropdown',
        validate: validatePhoneOption,
        options: phoneOptions(),
        onCreate: (value: string) => createNew('phone', value),
      }
    }
    if (field.fieldname === 'address') {
      return {
        ...field,
        create: (_value: unknown, close?: () => void) => {
          showAddressModal?.()
          close?.()
        },
        edit: (address: string) => showAddressModal?.(address),
      }
    }
    return field
  }
}
