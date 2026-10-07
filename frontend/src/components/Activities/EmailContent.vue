<template>
  <iframe
    ref="iframeRef"
    :srcdoc="htmlContent"
    class="prose-f block h-10 max-h-[500px] w-full"
  />
</template>

<script setup>
import { ref, watch } from 'vue'
import { useColorScheme } from 'frappe-ui'
import {
  DARK_SURFACE,
  parseRgb,
  toCss,
  blend,
  darkModeBackground,
  darkModeText,
} from '@/utils/emailColors'
import emailContentStyles from './emailContent.css?inline'

const props = defineProps({
  content: { type: String, required: true },
})

const iframeRef = ref(null)
const _content = ref(props.content)

const parser = new DOMParser()
const doc = parser.parseFromString(_content.value, 'text/html')

const gmailReplyToContent = doc.querySelectorAll('div.gmail_quote')
const outlookReplyToContent = doc.querySelectorAll('div#appendonsend')
const replyToContent = doc.querySelectorAll('p.reply-to-content')

if (gmailReplyToContent.length) {
  _content.value = parseReplyToContent(doc, 'div.gmail_quote', true)
} else if (outlookReplyToContent.length) {
  _content.value = parseReplyToContent(doc, 'div#appendonsend')
} else if (replyToContent.length) {
  _content.value = parseReplyToContent(doc, 'p.reply-to-content')
}

function parseReplyToContent(doc, selector, forGmail = false) {
  function handleAllInstances(doc) {
    const replyToContentElements = doc.querySelectorAll(selector)
    if (replyToContentElements.length === 0) return
    const replyToContentElement = replyToContentElements[0]
    replaceReplyToContent(replyToContentElement, forGmail)
    handleAllInstances(doc)
  }

  handleAllInstances(doc)

  return doc.body.innerHTML
}

function replaceReplyToContent(replyToContentElement, forGmail) {
  if (!replyToContentElement) return
  let randomId = Math.random().toString(36).substring(2, 7)
  const wrapper = doc.createElement('div')
  wrapper.classList.add('replied-content')

  const collapseLabel = doc.createElement('label')
  collapseLabel.classList.add('collapse')
  collapseLabel.setAttribute('for', randomId)
  collapseLabel.innerHTML = '...'
  wrapper.appendChild(collapseLabel)

  const collapseInput = doc.createElement('input')
  collapseInput.setAttribute('id', randomId)
  collapseInput.setAttribute('class', 'replyCollapser')
  collapseInput.setAttribute('type', 'checkbox')
  wrapper.appendChild(collapseInput)

  if (forGmail) {
    const prevSibling = replyToContentElement.previousElementSibling
    if (prevSibling && prevSibling.tagName === 'BR') {
      prevSibling.remove()
    }
    let cloned = replyToContentElement.cloneNode(true)
    cloned.classList.remove('gmail_quote')
    wrapper.appendChild(cloned)
  } else {
    const allSiblings = Array.from(replyToContentElement.parentElement.children)
    const replyToContentIndex = allSiblings.indexOf(replyToContentElement)
    const followingSiblings = allSiblings.slice(replyToContentIndex + 1)

    if (followingSiblings.length === 0) return

    let clonedFollowingSiblings = followingSiblings.map((sibling) =>
      sibling.cloneNode(true),
    )

    const div = doc.createElement('div')
    div.append(...clonedFollowingSiblings)

    wrapper.append(div)

    // Remove all siblings after the reply-to-content element
    for (let i = replyToContentIndex + 1; i < allSiblings.length; i++) {
      replyToContentElement.parentElement.removeChild(allSiblings[i])
    }
  }

  replyToContentElement.parentElement.replaceChild(
    wrapper,
    replyToContentElement,
  )
}

const htmlContent = `
<!DOCTYPE html>
<html>
<head>
  <style>${emailContentStyles}</style>
</head>
<body>
    <div ref="emailContentRef" class="email-content prose-f">${_content.value}</div>
</body>
</html>
`

const { resolvedColorScheme } = useColorScheme()

const darkModeColors = []

function applyColorScheme() {
  const html = iframeRef.value?.contentDocument?.documentElement
  if (!html) return
  html.setAttribute('data-theme', resolvedColorScheme.value)

  const dark = resolvedColorScheme.value === 'dark'
  for (const { el, property, original, darkColor } of darkModeColors) {
    if (dark) el.style.setProperty(property, darkColor, 'important')
    else if (original.value)
      el.style.setProperty(property, original.value, original.priority)
    else el.style.removeProperty(property)
  }
}

watch(resolvedColorScheme, applyColorScheme)

const BORDER_SIDES = ['top', 'right', 'bottom', 'left']

// Runs once while the iframe is still in light mode, so computed colors are the
// email's own. Inherited text is checked too wherever the background changes.
function collectDarkModeColors(emailContent) {
  darkModeColors.length = 0
  const view = emailContent.ownerDocument.defaultView
  const darkBackgrounds = new Map([[emailContent, DARK_SURFACE]])

  function backgroundInDarkMode(el) {
    if (!darkBackgrounds.has(el)) {
      const own = parseRgb(view.getComputedStyle(el).backgroundColor)
      const behind = backgroundInDarkMode(el.parentElement)
      const visible = own?.a > 0 ? darkModeBackground(own) ?? own : null
      darkBackgrounds.set(el, visible ? blend(visible, behind) : behind)
    }
    return darkBackgrounds.get(el)
  }

  function add(el, property, darkColor) {
    darkModeColors.push({
      el,
      property,
      darkColor: toCss(darkColor),
      original: {
        value: el.style.getPropertyValue(property),
        priority: el.style.getPropertyPriority(property),
      },
    })
  }

  for (const el of emailContent.querySelectorAll(
    '[style], font[color], [bgcolor]',
  )) {
    const computed = view.getComputedStyle(el)
    const background = backgroundInDarkMode(el)
    let backgroundChanged = false

    if (el.style.backgroundColor || el.getAttribute('bgcolor')) {
      const original = parseRgb(computed.backgroundColor)
      const dark = original && darkModeBackground(original)
      if (dark) {
        add(el, 'background-color', dark)
        backgroundChanged = true
      }
    }

    if (el.style.color || el.getAttribute('color') || backgroundChanged) {
      const original = parseRgb(computed.color)
      const dark = original && darkModeText(original, background)
      if (dark) add(el, 'color', dark)
    }

    for (const side of BORDER_SIDES) {
      if (!el.style.getPropertyValue(`border-${side}-style`)) continue
      const original = parseRgb(
        computed.getPropertyValue(`border-${side}-color`),
      )
      const dark = original && darkModeText(original, background)
      if (dark) add(el, `border-${side}-color`, dark)
    }
  }
}

watch(iframeRef, (iframe) => {
  if (iframe) {
    iframe.onload = () => {
      const emailContent =
        iframe.contentWindow.document.querySelector('.email-content')
      let parent = emailContent.closest('html')

      collectDarkModeColors(emailContent)
      applyColorScheme()

      iframe.style.height = parent.offsetHeight + 1 + 'px'

      let replyCollapsers = emailContent.querySelectorAll('.replyCollapser')
      if (replyCollapsers.length) {
        replyCollapsers.forEach((replyCollapser) => {
          replyCollapser.addEventListener('change', () => {
            iframe.style.height = parent.offsetHeight + 1 + 'px'
          })
        })
      }
    }
  }
})
</script>
