import { formatCurrency } from '@/utils/numberFormat'

// formatCurrency takes its currency metadata from window.sysdefaults.currency and
// window.currency_info (a name -> Currency record map). Both are stubs a real
// page load populates; here they stand in for a site configured with PLN.
const PLN = { symbol: 'zł', symbol_on_right: 1 }

function setCurrencyInfo(info) {
  window.currency_info = info
}

afterEach(() => {
  window.currency_info = undefined
  window.sysdefaults = { currency: 'USD' }
})

describe('formatCurrency', () => {
  describe('symbol placement', () => {
    it('puts the symbol on the left by default', () => {
      setCurrencyInfo({ USD: { symbol: '$', symbol_on_right: 0 } })
      expect(formatCurrency(1234.5, '#,###.##', 'USD', 2)).toBe('$ 1,234.50')
    })

    it('puts the symbol on the right when symbol_on_right is set', () => {
      setCurrencyInfo({ PLN })
      expect(formatCurrency(1234.5, '# ###,##', 'PLN', 2)).toBe('1 234,50 zł')
    })

    it('applies symbol_on_right to a zero value', () => {
      setCurrencyInfo({ PLN })
      expect(formatCurrency(0, '# ###,##', 'PLN', 2)).toBe('0,00 zł')
    })

    it('keeps the sign in front when the symbol is on the right', () => {
      setCurrencyInfo({ PLN })
      expect(formatCurrency(-5, '# ###,##', 'PLN', 2)).toBe('-5,00 zł')
    })
  })

  describe('symbol lookup', () => {
    it('prefers the Currency record over the browser locale', () => {
      // Intl.NumberFormat('en-US') renders PLN as the code "PLN", not the symbol.
      setCurrencyInfo({ PLN })
      expect(formatCurrency(0, '# ###,##', 'PLN', 2)).toContain('zł')
      expect(formatCurrency(0, '# ###,##', 'PLN', 2)).not.toContain('PLN')
    })

    it('falls back to the currency code when no symbol is configured', () => {
      setCurrencyInfo({ XYZ: { symbol: '', symbol_on_right: 0 } })
      expect(formatCurrency(10, '#,###.##', 'XYZ', 2)).toBe('XYZ 10.00')
    })

    it('falls back to the browser locale when the currency is unknown', () => {
      setCurrencyInfo({})
      expect(formatCurrency(10, '#,###.##', 'EUR', 2)).toContain('€')
    })

    it('reads symbol_on_right as a string, the way a Check field serialises', () => {
      setCurrencyInfo({ PLN: { symbol: 'zł', symbol_on_right: '1' } })
      expect(formatCurrency(5, '# ###,##', 'PLN', 2)).toBe('5,00 zł')
    })
  })

  // The boot payload is the only path that gets every currency right. The Intl
  // fallback below it cannot: en-US has no symbol for PLN/SEK/CZK/HUF, so those
  // render as bare ISO codes whenever currency_info is missing.
  describe('production path, driven by the boot payload', () => {
    const boot = {
      USD: { symbol: '$', symbol_on_right: 0 },
      EUR: { symbol: '€', symbol_on_right: 0 },
      CHF: { symbol: 'CHF', symbol_on_right: 0 },
      PLN: { symbol: 'zł', symbol_on_right: 1 },
      SEK: { symbol: 'kr', symbol_on_right: 1 },
      CZK: { symbol: 'Kč', symbol_on_right: 1 },
      HUF: { symbol: 'Ft', symbol_on_right: 1 },
    }

    it('places each currency symbol on its configured side', () => {
      setCurrencyInfo(boot)
      for (const [code, record] of Object.entries(boot)) {
        const out = formatCurrency(1234.5, '#,###.##', code, 2)
        if (record.symbol_on_right) {
          expect(out.endsWith(record.symbol)).toBe(true)
        } else {
          expect(out.startsWith(record.symbol)).toBe(true)
        }
      }
    })

    it('resolves symbols the Intl fallback gets wrong', () => {
      setCurrencyInfo(boot)
      for (const code of ['PLN', 'SEK', 'CZK', 'HUF']) {
        expect(formatCurrency(5, '#,###.##', code, 2)).not.toContain(code)
      }
    })
  })

  describe('hide_currency_symbol', () => {
    it('omits the symbol when hide_currency_symbol is set', () => {
      setCurrencyInfo({ USD: { symbol: '$', symbol_on_right: 0 } })
      window.sysdefaults.hide_currency_symbol = 1
      expect(formatCurrency(1234.5, '#,###.##', 'USD', 2)).toBe('1,234.50')
    })

    it('still prints the symbol when hide_currency_symbol is off', () => {
      setCurrencyInfo({ USD: { symbol: '$', symbol_on_right: 0 } })
      window.sysdefaults.hide_currency_symbol = 0
      expect(formatCurrency(1234.5, '#,###.##', 'USD', 2)).toBe('$ 1,234.50')
    })
  })

  describe('number formatting', () => {
    it('applies the number_format passed for the currency', () => {
      setCurrencyInfo({ PLN })
      expect(formatCurrency(1234.5, '# ###,##', 'PLN', 2)).toBe('1 234,50 zł')
    })

    it('respects the requested precision', () => {
      setCurrencyInfo({ USD: { symbol: '$', symbol_on_right: 0 } })
      expect(formatCurrency(1.005, '#,###.##', 'USD', 3)).toBe('$ 1.005')
    })

    it('formats a plain number when no currency is given', () => {
      expect(formatCurrency(1234.5, '#,###.##', '', 2)).toBe('1,234.50')
    })
  })
})
