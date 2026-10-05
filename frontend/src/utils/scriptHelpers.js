/**
 * Extract class names from a CRM Form Script string.
 * Ignores class names inside comments.
 *
 * @param {string} script - raw script source
 * @returns {string[]} array of class names
 */
export function getClassNames(script) {
  const withoutComments = script
    .replace(/\/\/.*$/gm, '') // Remove single-line comments
    .replace(/\/\*[\s\S]*?\*\//g, '') // Remove multi-line comments

  return (
    [...withoutComments.matchAll(/class\s+([A-Za-z0-9_]+)/g)].map(
      (match) => match[1],
    ) || []
  )
}

/**
 * Create a Proxy that wraps document data and routes trigger() calls
 * to controller methods.
 *
 * @param {Function|object} source - either a getter function or a data object
 * @param {object} instance - the controller instance (methods live here)
 * @param {object} [childInstance] - child controller for getRow routing
 * @returns {Proxy}
 */
export function createDocProxy(source, instance, childInstance = null) {
  const isFunction = typeof source === 'function'
  const getCurrentData = () => (isFunction ? source() : source)

  return new Proxy(
    {},
    {
      get(target, prop) {
        const currentDocData = getCurrentData()
        if (!currentDocData) return undefined

        if (prop === 'trigger') {
          if (currentDocData && 'trigger' in currentDocData) {
            console.warn(
              __(
                '⚠️ Avoid using "trigger" as a field name — it conflicts with the built-in trigger() method.',
              ),
            )
          }

          return (methodName, ...args) => {
            const method = instance[methodName]
            if (typeof method === 'function') {
              return method.apply(instance, args)
            } else {
              console.warn(
                __('⚠️ Method "{0}" not found in class.', [methodName]),
              )
            }
          }
        }

        if (prop === 'getRow') {
          return instance.getRow.bind(childInstance || instance)
        }

        return currentDocData[prop]
      },
      set(target, prop, value) {
        const currentDocData = getCurrentData()
        if (!currentDocData) return false

        currentDocData[prop] = value
        return true
      },
      has(target, prop) {
        const currentDocData = getCurrentData()
        if (!currentDocData) return false
        return prop in currentDocData
      },
      ownKeys() {
        const currentDocData = getCurrentData()
        if (!currentDocData) return []
        return Reflect.ownKeys(currentDocData)
      },
      getOwnPropertyDescriptor(target, prop) {
        const currentDocData = getCurrentData()
        if (!currentDocData) return undefined
        return Reflect.getOwnPropertyDescriptor(currentDocData, prop)
      },
    },
  )
}

/**
 * Resolve a child table row into a doc proxy. `ctx` is the controller `getRow` was called on:
 * a child instance, or a parent instance that owns `_childInstances`. A parent gets a proxy
 * that routes `trigger()` to the child class of that table.
 *
 * @param {object} ctx - controller instance `getRow` is bound to
 * @param {string} parentField - child table fieldname on the parent doc
 * @param {number} [idx] - row idx; falls back to the running row of the child controller
 * @param {Function} getMeta - meta store getter, `getMeta(doctype).getFields()`
 * @returns {Proxy|null}
 */
export function resolveRow(ctx, parentField, idx, getMeta) {
  idx = idx || ctx.currentRowIdx

  const children = ctx._childInstances
  let childController = null

  if (children?.length) {
    const { getFields } = getMeta(ctx.doc.doctype)
    const field = getFields().find((f) => f.fieldname === parentField)
    const dt = field?.options?.replace(/\s+/g, '')
    childController = children.find(
      (r) => (r._className || r.constructor.name) === dt,
    )

    if (!idx) idx = childController?.currentRowIdx
  }

  if (!ctx.doc[parentField]) {
    console.warn(__('⚠️ No data found for parent field: {0}', [parentField]))
    return null
  }
  const row = ctx.doc[parentField].find((r) => r.idx === idx)

  if (!row) {
    console.warn(
      __('⚠️ No row found for idx: {0} in parent field: {1}', [
        idx,
        parentField,
      ]),
    )
    return null
  }

  row.parent = row.parent || ctx.doc.name

  return createDocProxy(row, childController || ctx)
}
