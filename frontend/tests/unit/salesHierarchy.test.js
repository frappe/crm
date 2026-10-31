import { describe, expect, it } from 'vitest'
import {
  addCandidates,
  managerChoices,
  reportsOf,
  treeRows,
} from '../../../crm/fcrm/frontend/settings/sales-hierarchy/hierarchyTree.js'

const users = [
  {
    name: 'admin@example.com',
    full_name: 'Asha Admin',
    role: 'System Manager',
  },
  { name: 'mia@example.com', full_name: 'Mia Manager', role: 'Sales Manager' },
  { name: 'lee@example.com', full_name: 'Lee Lead', role: 'Sales Manager' },
  { name: 'ravi@example.com', full_name: 'Ravi Rep', role: 'Sales User' },
  { name: 'sam@example.com', full_name: 'Sam Seller', role: 'Sales User' },
  { name: 'new@example.com', full_name: 'Nia New', role: 'Sales User' },
  { name: 'boss@example.com', full_name: 'Bo Boss', role: 'Sales Manager' },
]

// In lft order, as the block lists them.
const nodes = [
  { name: 'n-mia', user: 'mia@example.com', reports_to: null },
  { name: 'n-lee', user: 'lee@example.com', reports_to: 'n-mia' },
  { name: 'n-ravi', user: 'ravi@example.com', reports_to: 'n-lee' },
  { name: 'n-sam', user: 'sam@example.com', reports_to: 'n-mia' },
]

const node = (name) => nodes.find((each) => each.name === name)
const names = (list) => list.map((each) => each.name)

describe('treeRows', () => {
  it('draws each manager before their reports, one level deeper', () => {
    expect(
      treeRows(nodes, users).map((row) => [row.name, row.depth, row.reports]),
    ).toEqual([
      ['n-mia', 0, 2],
      ['n-lee', 1, 1],
      ['n-ravi', 2, 0],
      ['n-sam', 1, 0],
    ])
  })

  it("takes the user's name and role from the CRM users", () => {
    const [mia] = treeRows(nodes, users)
    expect([mia.full_name, mia.role]).toEqual(['Mia Manager', 'Sales Manager'])
  })

  it('keeps the managers above a match, and drops everything else', () => {
    expect(names(treeRows(nodes, users, 'ravi'))).toEqual([
      'n-mia',
      'n-lee',
      'n-ravi',
    ])
    expect(names(treeRows(nodes, users, 'SAM@'))).toEqual(['n-mia', 'n-sam'])
    expect(treeRows(nodes, users, 'nobody')).toEqual([])
  })

  it('draws a node whose manager is gone at the top level', () => {
    const orphan = [
      { name: 'n-sam', user: 'sam@example.com', reports_to: 'n-x' },
    ]
    expect(treeRows(orphan, users).map((row) => row.depth)).toEqual([0])
  })
})

describe('managerChoices', () => {
  it('leaves out the node itself and everyone below it', () => {
    const managers = users.map((user) => ({ ...user, role: 'Sales Manager' }))
    expect(names(managerChoices(nodes, node('n-lee'), managers))).toEqual([
      'n-mia',
      'n-sam',
    ])
  })

  it('keeps a Sales Manager from reporting to a Sales User', () => {
    expect(names(managerChoices(nodes, node('n-lee'), users))).toEqual([
      'n-mia',
    ])
  })

  it('lets a Sales User report only to someone not ranked below them', () => {
    expect(names(managerChoices(nodes, node('n-sam'), users))).toEqual([
      'n-mia',
      'n-lee',
      'n-ravi',
    ])
    expect(names(managerChoices(nodes, node('n-mia'), users))).toEqual([])
  })
})

describe('addCandidates', () => {
  it('offers Sales Managers and Sales Users not yet in the tree', () => {
    expect(names(addCandidates(users, nodes, null))).toEqual([
      'new@example.com',
      'boss@example.com',
    ])
  })

  it('offers only Sales Users under a Sales User', () => {
    expect(names(addCandidates(users, nodes, node('n-ravi')))).toEqual([
      'new@example.com',
    ])
  })
})

describe('reportsOf', () => {
  it("lists a node's direct reports only", () => {
    expect(names(reportsOf(nodes, node('n-mia')))).toEqual(['n-lee', 'n-sam'])
  })
})
