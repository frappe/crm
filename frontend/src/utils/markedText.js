// Search snippets are user text with only <mark> added, so everything else stays a text node.
export function markedParts(text) {
  return String(text || '')
    .split(/<mark>(.*?)<\/mark>/s)
    .map((part, index) => ({ text: part, marked: index % 2 === 1 }))
    .filter((part) => part.text)
}

export function stripMarks(text) {
  return markedParts(text)
    .map((part) => part.text)
    .join('')
}
