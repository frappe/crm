import {
  getClassNames,
  createDocProxy,
  resolveRow,
} from '@/utils/scriptHelpers'

describe('getClassNames', () => {
  it('extracts single class name', () => {
    expect(getClassNames('class CRMLead { }')).toEqual(['CRMLead'])
  })

  it('extracts multiple class names', () => {
    const script = 'class CRMDeal { }\nclass CRMProducts { }'
    expect(getClassNames(script)).toEqual(['CRMDeal', 'CRMProducts'])
  })

  it('handles class with extends', () => {
    expect(getClassNames('class CRMLead extends Base { }')).toEqual(['CRMLead'])
  })

  it('ignores class in single-line comments', () => {
    const script = '// class Ignored { }\nclass CRMLead { }'
    expect(getClassNames(script)).toEqual(['CRMLead'])
  })

  it('ignores class in multi-line comments', () => {
    const script = '/* class Ignored { } */\nclass CRMLead { }'
    expect(getClassNames(script)).toEqual(['CRMLead'])
  })

  it('ignores class in multi-line comment spanning lines', () => {
    const script = `/*
      class Ignored {
        onLoad() {}
      }
    */
    class CRMLead { }`
    expect(getClassNames(script)).toEqual(['CRMLead'])
  })

  it('returns empty array for no classes', () => {
    expect(getClassNames('const x = 1')).toEqual([])
  })

  it('returns empty array for empty string', () => {
    expect(getClassNames('')).toEqual([])
  })

  it('handles class names with underscores and numbers', () => {
    expect(getClassNames('class My_Class_2 { }')).toEqual(['My_Class_2'])
  })

  it('handles mixed comments and classes', () => {
    const script = `
      // class Skipped1 { }
      class CRMDeal { }
      /* class Skipped2 { } */
      class CRMProducts { }
    `
    expect(getClassNames(script)).toEqual(['CRMDeal', 'CRMProducts'])
  })
})

describe('createDocProxy', () => {
  // ─── Read ─────────────────────────────────────────────────────

  it('reads properties from source object', () => {
    const data = { lead_name: 'John', status: 'New' }
    const instance = {}
    const proxy = createDocProxy(data, instance)
    expect(proxy.lead_name).toBe('John')
    expect(proxy.status).toBe('New')
  })

  it('reads properties from source getter function', () => {
    const data = { lead_name: 'John' }
    const instance = {}
    const proxy = createDocProxy(() => data, instance)
    expect(proxy.lead_name).toBe('John')
  })

  it('returns undefined for missing property', () => {
    const proxy = createDocProxy({ a: 1 }, {})
    expect(proxy.b).toBeUndefined()
  })

  it('returns undefined when source is null', () => {
    const proxy = createDocProxy(() => null, {})
    expect(proxy.anything).toBeUndefined()
  })

  // ─── Write ────────────────────────────────────────────────────

  it('writes properties to source object', () => {
    const data = { status: 'New' }
    const proxy = createDocProxy(data, {})
    proxy.status = 'Qualified'
    expect(data.status).toBe('Qualified')
  })

  it('writes properties to source via getter function', () => {
    const data = { status: 'New' }
    const proxy = createDocProxy(() => data, {})
    proxy.status = 'Qualified'
    expect(data.status).toBe('Qualified')
  })

  // ─── trigger() ────────────────────────────────────────────────

  it('trigger calls method on instance', () => {
    const instance = {
      _myMethod: vi.fn().mockReturnValue('result'),
    }
    const proxy = createDocProxy({ name: 'test' }, instance)
    const result = proxy.trigger('_myMethod', 'arg1')
    expect(instance._myMethod).toHaveBeenCalledWith('arg1')
    expect(result).toBe('result')
  })

  it('trigger with non-existent method does not throw', () => {
    const instance = {}
    const proxy = createDocProxy({ name: 'test' }, instance)
    expect(() => proxy.trigger('nonExistent')).not.toThrow()
  })

  it('trigger binds correct this context', () => {
    let capturedThis = null
    const instance = {
      myMethod() {
        capturedThis = this
      },
    }
    const proxy = createDocProxy({ name: 'test' }, instance)
    proxy.trigger('myMethod')
    expect(capturedThis).toBe(instance)
  })

  // ─── has / in operator ────────────────────────────────────────

  it('supports "in" operator', () => {
    const proxy = createDocProxy({ lead_name: 'John' }, {})
    expect('lead_name' in proxy).toBe(true)
    expect('missing' in proxy).toBe(false)
  })

  it('"in" returns false when source is null', () => {
    const proxy = createDocProxy(() => null, {})
    expect('anything' in proxy).toBe(false)
  })

  // ─── ownKeys ──────────────────────────────────────────────────

  it('returns own keys from source', () => {
    const proxy = createDocProxy({ a: 1, b: 2 }, {})
    expect(Object.keys(proxy)).toEqual(['a', 'b'])
  })
})

describe('resolveRow', () => {
  class CRMProducts {
    qty = vi.fn().mockReturnValue('child qty')
  }
  const data = {
    doctype: 'CRM Deal',
    name: 'DEAL-1',
    products: [
      { idx: 1, product_name: 'A' },
      { idx: 2, product_name: 'B' },
    ],
  }
  const getMeta = () => ({
    getFields: () => [{ fieldname: 'products', options: 'CRM Products' }],
  })

  function parentWithChild() {
    const parent = { getRow() {} }
    const child = new CRMProducts()
    parent.doc = createDocProxy(() => data, parent)
    parent._childInstances = [child]
    parent.getRow = function (field, idx) {
      return resolveRow(this, field, idx, getMeta)
    }
    return { parent, child }
  }

  it('does not throw when called through a parent doc proxy', () => {
    const { parent } = parentWithChild()
    expect(() => parent.doc.getRow('products', 1)).not.toThrow()
    expect(parent.doc.getRow('products', 1).product_name).toBe('A')
  })

  it('routes trigger() on a parent-resolved row to the child class', () => {
    const { parent, child } = parentWithChild()
    const row = parent.doc.getRow('products', 2)
    expect(row.trigger('qty')).toBe('child qty')
    expect(child.qty).toHaveBeenCalled()
  })

  it('falls back to the child running row when idx is omitted', () => {
    const { parent, child } = parentWithChild()
    child.currentRowIdx = 2
    expect(parent.doc.getRow('products').product_name).toBe('B')
  })

  it('resolves rows from a child controller without looking up metadata', () => {
    const child = new CRMProducts()
    child.doc = createDocProxy(() => data, {})
    child.currentRowIdx = 1
    const spy = vi.fn(getMeta)
    expect(resolveRow(child, 'products', undefined, spy).product_name).toBe('A')
    expect(spy).not.toHaveBeenCalled()
  })

  it('returns null and warns for an unknown field or row', () => {
    const { parent } = parentWithChild()
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
    expect(parent.doc.getRow('missing', 1)).toBeNull()
    expect(parent.doc.getRow('products', 99)).toBeNull()
    expect(warn).toHaveBeenCalledTimes(2)
    warn.mockRestore()
  })
})
