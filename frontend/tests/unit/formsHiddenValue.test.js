import { describe, expect, it } from 'vitest'
import {
  initialValue,
  isChecked,
  storedValue,
  valueControl,
} from '../../../crm/fcrm/frontend/forms/builder/hiddenValue.js'

describe('a hidden row value control', () => {
  it.each([
    ['Select', 'select'],
    ['Link', 'select'],
    ['Date', 'date'],
    ['Datetime', 'datetime'],
    ['Time', 'time'],
    ['Int', 'number'],
    ['Float', 'number'],
    ['Currency', 'number'],
    ['Percent', 'number'],
    ['Check', 'checkbox'],
  ])('gives %s a %s control', (fieldtype, control) => {
    expect(valueControl(fieldtype)).toBe(control)
  })

  it.each(['Data', 'Small Text', 'Text', 'Long Text', 'Phone', 'Color'])(
    'keeps %s as text',
    (fieldtype) => expect(valueControl(fieldtype)).toBe('text'),
  )
})

describe('a hidden row stored value', () => {
  it('stores a checkbox as "1" or "0"', () => {
    expect(storedValue('Check', true)).toBe('1')
    expect(storedValue('Check', false)).toBe('0')
    expect(storedValue('Check', 1)).toBe('1')
  })

  it('reads "1" (or 1) as checked and anything else as not', () => {
    expect(isChecked('1')).toBe(true)
    expect(isChecked(1)).toBe(true)
    expect(isChecked('0')).toBe(false)
    expect(isChecked('')).toBe(false)
    expect(isChecked(undefined)).toBe(false)
  })

  it('stores a whole number for an Int, which the server parses with int()', () => {
    expect(storedValue('Int', '42')).toBe('42')
    expect(storedValue('Int', '1.5')).toBe('1')
    expect(storedValue('Int', '1e3')).toBe('1000')
    expect(storedValue('Int', '')).toBe('')
  })

  it('keeps a number input value for Float, Currency and Percent', () => {
    expect(storedValue('Float', '1.25')).toBe('1.25')
    expect(storedValue('Currency', '1000')).toBe('1000')
    expect(storedValue('Percent', '')).toBe('')
  })

  it('keeps the pickers ISO values as they come', () => {
    expect(storedValue('Date', '2026-11-12')).toBe('2026-11-12')
    expect(storedValue('Datetime', '2026-11-12 09:30:00')).toBe(
      '2026-11-12 09:30:00',
    )
    expect(storedValue('Time', '09:30')).toBe('09:30')
    expect(storedValue('Date', '')).toBe('')
  })

  it('keeps text as typed, spaces included', () => {
    expect(storedValue('Data', 'Web ')).toBe('Web ')
    expect(storedValue('Data', null)).toBe('')
  })

  it('starts a Check row unticked, and every other row empty', () => {
    expect(initialValue('Check')).toBe('0')
    expect(initialValue('Date')).toBe('')
    expect(initialValue('Data')).toBe('')
  })
})
