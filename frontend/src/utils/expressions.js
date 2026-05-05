/**
 * Pure expression evaluation helpers.
 * Extracted from utils/index.js to be independently importable
 * without pulling in UI dependencies (icons, components, etc.).
 */

const BLOCKED_PATTERNS = [
  /\bimport\s*\(/,
  /\brequire\s*\(/,
  /\bfetch\s*\(/,
  /\bXMLHttpRequest\b/,
  /\bdocument\s*\.\s*cookie\b/,
  /\blocalStorage\b/,
  /\bsessionStorage\b/,
  /\beval\s*\(/,
  /\bFunction\s*\(/,
]

function validateExpression(code) {
  for (const pattern of BLOCKED_PATTERNS) {
    if (pattern.test(code)) {
      console.warn('Blocked potentially unsafe expression:', code)
      return false
    }
  }
  return true
}

export function _eval(code, context = {}) {
  let variable_names = Object.keys(context)
  let variables = Object.values(context)
  code = `'use strict'; let out = ${code}; return out`
  if (!validateExpression(code)) {
    return undefined
  }
  try {
    let expression_function = new Function(...variable_names, code)
    return expression_function(...variables)
  } catch (error) {
    console.log('Error evaluating the following expression:')
    console.error(code)
    throw error
  }
}

export function evaluateDependsOnValue(expression, doc) {
  if (!expression) return true
  if (!doc) return true

  let out

  if (typeof expression === 'boolean') {
    out = expression
  } else if (typeof expression === 'function') {
    out = expression(doc)
  } else if (expression.substr(0, 5) == 'eval:') {
    try {
      out = _eval(expression.substr(5), { doc })
    } catch {
      out = true
    }
  } else {
    let value = doc[expression]
    if (Array.isArray(value)) {
      out = !!value.length
    } else {
      out = !!value
    }
  }

  return out
}

export function evaluateExpression(expression, doc, parent) {
  if (!expression) return false
  if (!doc) return false

  let out
  if (typeof expression === 'boolean') {
    out = expression
  } else if (typeof expression === 'function') {
    out = expression(doc)
  } else if (expression.substr(0, 5) == 'eval:') {
    try {
      out = _eval(expression.substr(5), { doc, parent })
      if (parent && parent.istable && expression.includes('is_submittable')) {
        out = true
      }
    } catch {
      out = true
    }
  } else {
    let value = doc[expression]
    if (Array.isArray(value)) {
      out = !!value.length
    } else {
      out = !!value
    }
  }

  return out
}
