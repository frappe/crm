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
          return instance.getRow.bind(
            childInstance || instance._childInstances || instance,
          )
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
