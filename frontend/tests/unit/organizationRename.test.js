import { describe, expect, it, vi } from 'vitest'
import { renameFromOrganizationName } from '../../../crm/fcrm/frontend/organization/rename.js'

function fakePage(organizationName, overrides = {}) {
  return {
    doctype: 'CRM Organization',
    docname: 'Org 45895',
    isNew: false,
    doc: { name: 'Org 45895', organization_name: organizationName },
    saved: { name: 'Org 45895', organization_name: 'Org 45895' },
    rename: vi.fn(() => Promise.resolve('renamed')),
    save: vi.fn(() => Promise.resolve()),
    ...overrides,
  }
}

describe('renameFromOrganizationName', () => {
  it('renames to the edited name, without merging', async () => {
    const page = fakePage('Org 45895 Renamed')
    await renameFromOrganizationName(page)
    expect(page.rename).toHaveBeenCalledWith('Org 45895 Renamed')
    expect(page.save).not.toHaveBeenCalled()
  })

  it('trims the edited name', async () => {
    const page = fakePage('  Org 45895 Renamed ')
    await renameFromOrganizationName(page)
    expect(page.rename).toHaveBeenCalledWith('Org 45895 Renamed')
  })

  it('does nothing when the name is unchanged', async () => {
    const page = fakePage(' Org 45895 ')
    await renameFromOrganizationName(page)
    expect(page.rename).not.toHaveBeenCalled()
    expect(page.save).not.toHaveBeenCalled()
  })

  it('puts the record name back and saves it when the rename is refused after its save', async () => {
    const page = fakePage('Taken 45895')
    page.rename = vi.fn(() => {
      page.saved.organization_name = 'Taken 45895'
      return Promise.resolve(null)
    })
    await renameFromOrganizationName(page)
    expect(page.doc.organization_name).toBe('Org 45895')
    expect(page.save).toHaveBeenCalledOnce()
  })

  it('saves nothing more when the save itself was refused', async () => {
    const page = fakePage('Taken 45895', {
      rename: vi.fn(() => Promise.resolve(null)),
    })
    await renameFromOrganizationName(page)
    expect(page.doc.organization_name).toBe('Org 45895')
    expect(page.save).not.toHaveBeenCalled()
  })

  it('restores a cleared name instead of renaming', async () => {
    const page = fakePage('  ')
    await renameFromOrganizationName(page)
    expect(page.rename).not.toHaveBeenCalled()
    expect(page.doc.organization_name).toBe('Org 45895')
  })

  it('leaves a new record alone, which takes its name at the first save', async () => {
    const page = fakePage('New Org 45895', { isNew: true, docname: undefined })
    await renameFromOrganizationName(page)
    expect(page.rename).not.toHaveBeenCalled()
    expect(page.doc.organization_name).toBe('New Org 45895')
  })
})
