import { describe, expect, it } from 'vitest'
import {
  crmRole,
  givenRoles,
  listedUsers,
  removable,
  roleChoices,
  withImpliedRoles,
} from '../../../crm/fcrm/frontend/settings/users/crmUsers.js'

const admin = { name: 'admin@example.com', role: 'System Manager' }
const manager = { name: 'manager@example.com', role: 'Sales Manager' }
const rep = {
  name: 'rep@example.com',
  full_name: 'Ravi Rep',
  role: 'Sales User',
}

describe('roleChoices', () => {
  it('lets a System Manager set any CRM role', () => {
    expect(roleChoices(admin, rep)).toEqual([
      'System Manager',
      'Sales Manager',
      'Sales User',
    ])
    expect(roleChoices(admin, manager)).toEqual([
      'System Manager',
      'Sales Manager',
      'Sales User',
    ])
  })

  it('lets a Sales Manager only demote to Sales User', () => {
    expect(
      roleChoices(manager, { ...manager, name: 'other@example.com' }),
    ).toEqual(['Sales Manager', 'Sales User'])
    expect(roleChoices(manager, rep)).toEqual(['Sales User'])
  })

  it('never offers to change your own role', () => {
    expect(roleChoices(admin, admin)).toEqual([])
    expect(roleChoices(manager, manager)).toEqual([])
  })

  it("locks a System Manager's role for a Sales Manager", () => {
    expect(roleChoices(manager, admin)).toEqual([])
  })
})

describe('removable', () => {
  it('never offers to remove yourself', () => {
    expect(removable(admin, admin)).toBe(false)
  })

  it('lets a Sales Manager remove a Sales User but not a System Manager', () => {
    expect(removable(manager, rep)).toBe(true)
    expect(removable(manager, admin)).toBe(false)
    expect(removable(admin, manager)).toBe(true)
  })
})

describe('givenRoles', () => {
  it('lets only a System Manager add managers and admins', () => {
    expect(givenRoles(admin)).toEqual([
      'System Manager',
      'Sales Manager',
      'Sales User',
    ])
    expect(givenRoles(manager)).toEqual(['Sales User'])
  })
})

describe('listedUsers', () => {
  const users = [{ name: 'Administrator', role: 'System Manager' }, admin, rep]

  it('leaves out Administrator', () => {
    expect(listedUsers(users)).toEqual([admin, rep])
  })

  it('matches the query by email or full name, in any case', () => {
    expect(listedUsers(users, 'ravi')).toEqual([rep])
    expect(listedUsers(users, ' ADMIN@ ')).toEqual([admin])
    expect(listedUsers(users, 'nobody')).toEqual([])
  })
})

describe('crmRole', () => {
  it('reads the highest CRM role among the roles held', () => {
    expect(crmRole(['All', 'Sales User', 'System Manager'])).toBe(
      'System Manager',
    )
    expect(crmRole(['Sales User', 'Sales Manager'])).toBe('Sales Manager')
    expect(crmRole(['Guest'])).toBe('')
  })
})

describe('withImpliedRoles', () => {
  it('adds the CRM roles below the highest one picked', () => {
    expect(withImpliedRoles(['System Manager'])).toEqual([
      'System Manager',
      'Sales Manager',
      'Sales User',
    ])
    expect(withImpliedRoles(['Sales User', 'Sales Manager'])).toEqual([
      'Sales User',
      'Sales Manager',
    ])
    expect(withImpliedRoles(['Sales User'])).toEqual(['Sales User'])
  })

  it('leaves other roles as they are', () => {
    expect(withImpliedRoles(['Accounts User'])).toEqual(['Accounts User'])
  })
})
