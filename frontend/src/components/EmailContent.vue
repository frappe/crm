<template>
  <iframe
    :srcdoc="htmlContent"
    class="h-screen max-h-[500px] w-full"
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
const props = defineProps({
  content: {
    type: String,
    required: true,
  },
})

const htmlContent = `
<!DOCTYPE html>
<html>
<head>
  <link href="/src/index.css" rel="stylesheet">
  <style>
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
    <div class="email-content prose-f">${props.content}</div>
</body>
</html>
`
</script>
