const RECORD_NAME = /(?<![[\w/-])`?(CRM-(DEAL|LEAD)-\d{4}-\d+)`?(?![\w\]])/g
const RECORD_PATHS = { DEAL: 'deals', LEAD: 'leads' }

/** Turns bare deal and lead names in Flow's markdown into links to their CRM pages. */
export function linkRecordNames(markdown = '') {
  return markdown.replace(
    RECORD_NAME,
    (_, name, kind) => `[${name}](/crm/${RECORD_PATHS[kind]}/${name})`,
  )
}

/** A left click with no key held, which the page may handle as its own navigation. */
export function isPlainClick(event) {
  return (
    event.button === 0 &&
    !event.metaKey &&
    !event.ctrlKey &&
    !event.shiftKey &&
    !event.altKey
  )
}
