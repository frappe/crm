import { createApp, h } from 'vue'
import MarkedText from '@/components/CommandPalette/MarkedText.vue'
import { markedParts, stripMarks } from '@/utils/markedText'

function render(snippet) {
  const root = document.createElement('div')
  const app = createApp({
    render: () => h('div', h(MarkedText, { text: snippet })),
  })
  app.mount(root)
  const html = root.innerHTML
  const marks = [...root.querySelectorAll('mark')].map(
    (mark) => mark.textContent,
  )
  const tags = [...root.querySelectorAll('*')].map((node) => node.tagName)
  const text = root.textContent
  app.unmount()
  return { html, marks, tags, text }
}

describe('markedParts', () => {
  it('splits text around mark tags', () => {
    expect(markedParts('the <mark>pricing</mark> call')).toEqual([
      { text: 'the ', marked: false },
      { text: 'pricing', marked: true },
      { text: ' call', marked: false },
    ])
  })

  it('keeps every other tag as plain text', () => {
    expect(markedParts('<img src=x onerror=alert(1)><mark>hi</mark>')).toEqual([
      { text: '<img src=x onerror=alert(1)>', marked: false },
      { text: 'hi', marked: true },
    ])
  })

  it('reads empty input as no parts', () => {
    expect(markedParts(null)).toEqual([])
  })
})

describe('stripMarks', () => {
  it('drops mark tags and keeps their text', () => {
    expect(stripMarks('Re: <mark>Pricing</mark> tiers')).toBe(
      'Re: Pricing tiers',
    )
  })
})

describe('MarkedText', () => {
  it('adds no whitespace around a highlight', () => {
    expect(render('the <mark>pricing</mark> call').text).toBe(
      'the pricing call',
    )
  })

  it('renders only mark elements from a hostile snippet', () => {
    const { marks, tags, html } = render(
      '<script>alert(1)</script> <img src=x onerror=alert(1)> <mark>pricing</mark>',
    )
    expect(tags).toEqual(['DIV', 'MARK'])
    expect(marks).toEqual(['pricing'])
    expect(html).toContain('&lt;img src=x onerror=alert(1)&gt;')
  })
})
