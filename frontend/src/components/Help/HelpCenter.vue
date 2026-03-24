<template>
  <div class="flex flex-col gap-2 overflow-hidden">
    <div class="m-1">
      <TextInput
        ref="searchInput"
        v-model="search"
        :placeholder="__('Search articles...')"
        :debounce="300"
      >
        <template #prefix>
          <FeatherIcon name="search" class="h-4 text-ink-gray-5" />
        </template>
      </TextInput>
    </div>
    <div
      class="flex justify-between items-center text-base text-ink-gray-5 mx-2"
    >
      <div>{{ __('All articles') }}</div>
      <Button variant="ghost" @click="openDocs">
        <FeatherIcon name="arrow-up-right" class="h-4 text-ink-gray-5" />
      </Button>
    </div>
    <div class="flex flex-col gap-1.5 overflow-y-auto">
      <div
        v-for="article in parsedArticles"
        :key="article.title"
        class="flex flex-col gap-1.5"
      >
        <div
          class="flex items-center justify-between p-1.5 hover:bg-surface-gray-1 rounded cursor-pointer"
          @click="article.opened = !article.opened"
        >
          <div class="flex items-center gap-2">
            <FeatherIcon
              :name="article.opened ? 'chevron-down' : 'chevron-right'"
              class="h-4 text-ink-gray-5"
            />
            <div class="text-base text-ink-gray-8">{{ article.title }}</div>
          </div>
        </div>
        <div v-show="article.opened" class="flex flex-col gap-1.5 ml-5">
          <div
            v-for="subArticle in article.subArticles"
            :key="subArticle.name"
            class="group flex items-center justify-between gap-2 p-1.5 hover:bg-surface-gray-1 rounded cursor-pointer"
            @click="() => openDoc(subArticle.name)"
          >
            <div class="flex items-center gap-2">
              <FeatherIcon name="file-text" class="h-4 text-ink-gray-5" />
              <div class="text-base text-ink-gray-8">
                {{ subArticle.title }}
              </div>
            </div>
            <FeatherIcon
              name="arrow-up-right"
              class="h-4 hidden group-hover:flex text-ink-gray-5"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Button, FeatherIcon, TextInput } from 'frappe-ui'
import { computed, onMounted, ref } from 'vue'

const props = defineProps({
  docsLink: {
    type: String,
    default: 'https://docs.frappe.io/crm',
  },
})

const searchInput = ref(null)
const search = ref('')
const articles = defineModel({
  type: Array,
  default: () => [],
})

const parsedArticles = computed(() => {
  if (!search.value) return articles.value

  return articles.value
    .map((article) => {
      const filteredSubArticles = article.subArticles.filter((subArticle) => {
        return subArticle.title
          .toLowerCase()
          .includes(search.value.toLowerCase())
      })

      return {
        ...article,
        subArticles: filteredSubArticles,
      }
    })
    .filter((article) => {
      return (
        article.title.toLowerCase().includes(search.value.toLowerCase()) ||
        article.subArticles.length > 0
      )
    })
})

function openDocs() {
  window.open(props.docsLink, '_blank')
}

function openDoc(name) {
  window.open(`${props.docsLink}/${name}`, '_blank')
}

onMounted(() => {
  searchInput.value?.el?.focus()
})
</script>
