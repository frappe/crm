// Evaluate a depends_on-style rule against a doc, matching the SUPPORTED grammar of
// the framework's evaluate_depends_on_value (frappe/public/js/frappe/form/layout.js).
// It PARSES the "eval:" expression rather than executing it, so the builder preview and
// the public page (crm_form.html has an identical inline copy) behave the same and no
// stored expression can run arbitrary JS. Keep the two copies in sync.

function coerce(v) {
  return Array.isArray(v) ? v.length > 0 : !!v
}

function safeEval(src, doc, parent) {
  let i = 0
  const ws = () => {
    while (i < src.length && /\s/.test(src[i])) i++
  }
  const starts = (tok) => {
    ws()
    return src.substr(i, tok.length) === tok
  }
  function primary() {
    ws()
    if (starts('(')) {
      i++
      const e = orExpr()
      ws()
      if (!starts(')')) throw new Error('expected )')
      i++
      return e
    }
    if (starts('!')) {
      i++
      return !coerce(primary())
    }
    const ch = src[i]
    if (ch === '"' || ch === "'") {
      i++
      let str = ''
      while (i < src.length && src[i] !== ch) {
        if (src[i] === '\\') i++
        str += src[i++]
      }
      i++
      return str
    }
    const num = /^-?\d+(?:\.\d+)?/.exec(src.slice(i))
    if (num) {
      i += num[0].length
      return parseFloat(num[0])
    }
    const id = /^[A-Za-z_$][\w$]*/.exec(src.slice(i))
    if (!id) throw new Error('unexpected token')
    i += id[0].length
    if (id[0] === 'true') return true
    if (id[0] === 'false') return false
    if (id[0] === 'null') return null
    let base
    if (id[0] === 'doc') base = doc
    else if (id[0] === 'parent') base = parent
    else throw new Error('unknown identifier: ' + id[0]) // no globals reachable
    for (;;) {
      ws()
      if (src[i] === '.') {
        i++
        const m = /^[A-Za-z_$][\w$]*/.exec(src.slice(i))
        if (!m) throw new Error('bad member')
        i += m[0].length
        base = base == null ? undefined : base[m[0]]
      } else if (src[i] === '[') {
        i++
        const key = orExpr()
        ws()
        if (!starts(']')) throw new Error('expected ]')
        i++
        base = base == null ? undefined : base[key]
      } else break
    }
    return base
  }
  function cmp() {
    const l = primary()
    ws()
    const ops = ['===', '!==', '==', '!=', '<=', '>=', '<', '>']
    for (const op of ops) {
      if (src.substr(i, op.length) === op) {
        i += op.length
        const r = primary()
        switch (op) {
          case '===':
          case '==':
            return l == r // eslint-disable-line eqeqeq
          case '!==':
          case '!=':
            return l != r // eslint-disable-line eqeqeq
          case '<':
            return l < r
          case '<=':
            return l <= r
          case '>':
            return l > r
          case '>=':
            return l >= r
        }
      }
    }
    return l
  }
  function andExpr() {
    let l = cmp()
    while (starts('&&')) {
      i += 2
      l = coerce(l) && coerce(cmp())
    }
    return l
  }
  function orExpr() {
    let l = andExpr()
    while (starts('||')) {
      i += 2
      l = coerce(l) || coerce(andExpr())
    }
    return l
  }
  const out = orExpr()
  ws()
  if (i < src.length) throw new Error('trailing input')
  return out
}

// Resolve a rule to a boolean; `fallback` covers an empty/unsupported/invalid expression.
export function evalRule(expr, doc, fallback) {
  const s = expr ? String(expr).trim() : ''
  if (!s) return fallback
  try {
    if (s.slice(0, 5) === 'eval:') return coerce(safeEval(s.slice(5), doc, doc))
    if (s.slice(0, 3) === 'fn:') return fallback
    return coerce(doc[s])
  } catch (e) {
    return fallback
  }
}
