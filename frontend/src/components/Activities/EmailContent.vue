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
  parseRgb,
  invertLightness,
  isUnreadableOnDark,
  isTooLightForDark,
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

function applyColorScheme() {
  const html = iframeRef.value?.contentDocument?.documentElement
  html?.setAttribute('data-theme', resolvedColorScheme.value)
}

watch(resolvedColorScheme, applyColorScheme)

const BORDER_SIDES = ['Top', 'Right', 'Bottom', 'Left']

function markColorsForDarkMode(emailContent) {
  const view = emailContent.ownerDocument.defaultView
  const elements = emailContent.querySelectorAll(
    '[style*="color"], [style*="background"], [style*="border"], font[color], [bgcolor]',
  )
  for (const el of elements) {
    const computed = view.getComputedStyle(el)

    if (el.style.color || el.getAttribute('color')) {
      const color = parseRgb(computed.color)
      if (color && isUnreadableOnDark(color)) {
        el.style.setProperty('--dark-color', invertLightness(color))
        el.setAttribute('data-dark-color', '')
      }
    }

    if (el.style.backgroundColor || el.getAttribute('bgcolor')) {
      const background = parseRgb(computed.backgroundColor)
      if (background && isTooLightForDark(background)) {
        el.style.setProperty('--dark-background', invertLightness(background))
        el.setAttribute('data-dark-background', '')
      }
    }

    const border = BORDER_SIDES.filter((side) => el.style[`border${side}Style`])
      .map((side) => parseRgb(computed[`border${side}Color`]))
      .find((color) => color && isUnreadableOnDark(color))
    if (border) {
      el.style.setProperty('--dark-border', invertLightness(border))
      el.setAttribute('data-dark-border', '')
    }
  }
}

watch(iframeRef, (iframe) => {
  if (iframe) {
    iframe.onload = () => {
      const emailContent =
        iframe.contentWindow.document.querySelector('.email-content')
      let parent = emailContent.closest('html')

      markColorsForDarkMode(emailContent)
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
