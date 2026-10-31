// Stands in for the desk's `@framework/ui/api` when a test imports a CRM desk contribution; tests mock it.
export function runMethod() {
  return Promise.reject(new Error('runMethod is not mocked'))
}
