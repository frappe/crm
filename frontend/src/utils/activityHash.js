// "#notes/<note>" opens the Notes tab at that note; "#<name>" is a tab or a timeline row.
export function parseActivityHash(hash) {
  const [tab, anchor = tab] = (hash || '').replace(/^#/, '').split('/')
  return { tab, anchor }
}

export function activityHashFor(hit) {
  return hit.source_doctype === 'FCRM Note'
    ? `#notes/${hit.hash}`
    : `#${hit.hash}`
}
