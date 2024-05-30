<template>
  <iframe
    ref="iframeRef"
    :srcdoc="htmlContent"
    class="prose-f block h-screen max-h-[500px] w-full"
    style="
      mask-image: linear-gradient(
        to bottom,
        black calc(100% - 30px),
        transparent 100%
      );
    "
  />
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  content: {
    type: String,
    required: true,
  },
})

const iframeRef = ref(null)

const htmlContent = `
<!DOCTYPE html>
<html>
<head>
  <style>

    .prose-f {
      --tw-prose-body: #383838;
      color: var(--tw-prose-body);
      font-weight: 420;
      letter-spacing: 0.02em;
      max-width: none;
      font-size: 14px;
      line-height: 1.6;
    }

    .email-content {
        word-break: break-word;
    }
    .email-content
        :is(:where(table):not(:where([class~='not-prose'], [class~='not-prose']
            *))) {
    table-layout: auto;
    }

    .email-content
        :where(table):not(:where([class~='not-prose'], [class~='not-prose'] *)) {
    width: unset;
    table-layout: auto;
    text-align: unset;
    margin-top: unset;
    margin-bottom: unset;
    font-size: unset;
    line-height: unset;
    }

    /* tr */

    .email-content
        :where(tbody tr):not(:where([class~='not-prose'], [class~='not-prose']
            *)) {
    border-bottom-width: 0;
    border-bottom-color: transparent;
    }

    /* td */

    .email-content
        :is(:where(td):not(:where([class~='not-prose'], [class~='not-prose'] *))) {
    position: unset;
    border-width: 0;
    border-color: transparent;
    padding: 0;
    }

    .email-content
        :where(tbody td):not(:where([class~='not-prose'], [class~='not-prose']
            *)) {
    vertical-align: revert;
    }

    /* image */
    .email-content
        :is(:where(img):not(:where([class~='not-prose'], [class~='not-prose']
            *))) {
    border-width: 0;
    }

    .email-content
        :where(img):not(:where([class~='not-prose'], [class~='not-prose'] *)) {
    margin: 0;
    }

    /* before & after */

    .email-content
        :where(blockquote
        p:first-of-type):not(:where([class~='not-prose'], [class~='not-prose']
            *))::before {
    content: none;
    }

    .email-content
        :where(blockquote
        p:last-of-type):not(:where([class~='not-prose'], [class~='not-prose']
            *))::after {
    content: none;
    }
  </style>
</head>
<body>
    <div ref="emailContentRef" class="email-content prose-f">${props.content}</div>
</body>
</html>
`

watch(iframeRef, (iframe) => {
  if (iframe) {
    iframe.onload = () => {
      const emailContent =
        iframe.contentWindow.document.querySelector('.email-content')
      iframe.style.height = emailContent.offsetHeight + 25 + 'px'

      let fileName = ''
      // read file name on path /src and get the file name of the css file to inject in the iframe
      // /assets/crm/frontend/assets/*.css
      const files = import.meta.globEager('/*/*')
      for (const file in files) {
        debugger
        fileName = file
      }


      // inject link in head of iframe
      const head = iframe.contentWindow.document.head
      const link = document.createElement('link')
      link.rel = 'stylesheet'
      link.href = '/src/index.css'
      head.appendChild(link)
    }
  }
})
</script>
