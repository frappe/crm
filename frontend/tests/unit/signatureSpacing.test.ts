import { describe, it, expect } from 'vitest'
import { Editor } from '@tiptap/core'
import Paragraph from '@tiptap/extension-paragraph'
import { buildEditorExtensions } from '@/components/editor/config'
import { composeSignatureContent } from '@/utils'

const CustomParagraph = Paragraph.extend({
  addAttributes() {
    return { class: { default: null } }
  },
})

function renderInComposer(html: string) {
  const editor = new Editor({
    extensions: buildEditorExtensions({
      starterKit: { paragraph: false },
      extra: [CustomParagraph],
    }),
    content: html,
  })
  const out = editor.getHTML()
  editor.destroy()
  return out
}

describe('composeSignatureContent', () => {
  const serverSignature =
    '<br><p class="signature"><p>Hi,</p>\n<p><strong>Example Name</strong></p>\n<p>Job Title</p></p>'

  it('inserts the signature without an empty paragraph between every line', () => {
    const rendered = renderInComposer(
      composeSignatureContent(serverSignature, '<p></p>'),
    )

    expect(rendered).not.toContain('<p><br></p><p>')
    expect((rendered.match(/<p>Hi,<\/p>/g) || []).length).toBe(1)
  })

  it('keeps the existing email body after the signature', () => {
    const content = composeSignatureContent(serverSignature, '<p>draft</p>')

    expect(content).toContain('<p>draft</p>')
    expect(content.indexOf('signature')).toBeLessThan(content.indexOf('draft'))
  })
})
