// Minimal globals that CRM code expects
globalThis.__ = (msg, args) => {
  if (!args) return msg
  let str = msg
  if (Array.isArray(args)) {
    args.forEach((arg, i) => {
      str = str.replace(`{${i}}`, arg)
    })
  }
  return str
}

globalThis.window = globalThis.window || {}
globalThis.window.sysdefaults = { currency: 'USD' }
