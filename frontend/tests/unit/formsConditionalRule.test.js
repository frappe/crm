import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'
import {
  evaluateRule,
  ruleError,
} from '../../../crm/fcrm/frontend/settings/forms/conditionalRule.js'

// The public page's parser, read out of crm_form.html: Preview must give the same answers.
const html = readFileSync(
  join(
    dirname(fileURLToPath(import.meta.url)),
    '../../../crm/www/crm_form.html',
  ),
  'utf8',
)
const pageSource = html
  .split('// [conditional-eval:start]')[1]
  .split('// [conditional-eval:end]')[0]
// eslint-disable-next-line no-new-func
const { truthy: pageTruthy } = new Function(
  `${pageSource}; return { truthy };`,
)()

const doc = {
  organization: 'Acme',
  first_name: 'Al',
  n: '10',
  qty: 0,
  items: [1],
  empty: [],
  nested: { city: 'Pune' },
}

const RULES = [
  '',
  '   ',
  'organization',
  'missing',
  'items',
  'empty',
  'eval:doc.organization == "Acme"',
  "eval:doc.organization != 'Acme'",
  'eval:doc.n > 5',
  'eval:doc.n <= 10',
  'eval:doc.qty === 0',
  'eval:doc.first_name && doc.organization',
  'eval:doc.missing || doc.qty',
  'eval:!doc.missing',
  'eval:!doc.organization == false',
  'eval:(doc.a || doc.organization) && doc.first_name',
  'eval:doc.nested.city == "Pune"',
  'eval:doc["organization"] == "Acme"',
  'eval:doc.missing.deeper',
  'eval:parent.organization',
  'eval:doc.n == -1',
  'eval:doc.organization == "Ac\\"me"',
  'eval:true',
  'eval:null',
  'eval:doc.organization ==',
  'eval:doc.organization == "Acme" )',
  'eval:window',
  'eval:constructor',
  'eval:doc.x = 1',
  'eval:alert(1)',
  'fn:my_rule',
]

describe('Forms Preview conditional rules', () => {
  describe('match the public page', () => {
    for (const rule of RULES) {
      it(`${JSON.stringify(rule)}`, () => {
        for (const fallback of [true, false]) {
          expect(evaluateRule(rule, doc, fallback)).toBe(
            pageTruthy(rule, doc, fallback),
          )
        }
      })
    }
  })

  describe('never run the rule', () => {
    const attacks = [
      'eval:window',
      'eval:document.cookie',
      'eval:globalThis',
      'eval:fetch("/api/method/logout")',
      'eval:alert(1)',
      'eval:doc.constructor.constructor("return 1")()',
      'eval:(0).constructor.constructor("return 1")()',
      'eval:doc.x = 1',
      'eval:constructor',
      'eval:toString',
    ]
    for (const rule of attacks) {
      it(`refuses ${rule}`, () => {
        expect(evaluateRule(rule, doc, false)).toBe(false)
        expect(evaluateRule(rule, doc, true)).toBe(true)
        expect(ruleError(rule)).toBeTruthy()
      })
    }
    it('cannot write to a global or to the record', () => {
      globalThis.__pwned46920 = false
      const record = { a: 1 }
      evaluateRule('eval:(globalThis.__pwned46920 = true)', record, false)
      evaluateRule('eval:doc.a = 2', record, false)
      expect(globalThis.__pwned46920).toBe(false)
      expect(record.a).toBe(1)
      delete globalThis.__pwned46920
    })
  })

  describe('a rule that does not parse', () => {
    it('does not count as true for the mandatory and read-only rules', () => {
      expect(evaluateRule('eval:doc.qty >', doc, false)).toBe(false)
      expect(evaluateRule('eval:doc.qty ==== 1', doc, false)).toBe(false)
    })
    it('names the problem', () => {
      expect(ruleError('eval:doc.qty >')).toBe('unexpected token')
      expect(ruleError('eval:doc.a )')).toBe('unexpected text after the rule')
      expect(ruleError('eval:(doc.a')).toBe('expected )')
      expect(ruleError('eval:window.x')).toBe('unknown name: window')
      expect(ruleError('fn:my_rule')).toBe(
        'fn: rules do not run on public forms',
      )
    })
    it('has no error when it parses or is empty', () => {
      expect(ruleError('')).toBeNull()
      expect(ruleError(undefined)).toBeNull()
      expect(ruleError('organization')).toBeNull()
      expect(ruleError('eval:doc.n > 5 && !doc.missing')).toBeNull()
    })
  })
})
