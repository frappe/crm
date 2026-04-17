import { getClassNames, createDocProxy } from '@/utils/scriptHelpers'

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
