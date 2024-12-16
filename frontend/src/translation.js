import { createResource } from 'frappe-ui'
import { ref } from 'vue'

// Create a reactive translation store
const translations = ref({});
const isInitialized = ref(false);

// Default translation function
export const __ = (str) => {
  if (!str) return '';
  return translations.value[str] || str;
};

// Add retry logic and better error handling
async function fetchTranslations() {
  const maxRetries = 3;
  let retryCount = 0;

  while (retryCount < maxRetries) {
    try {
      const response = createResource({
        url: 'crm.api.get_translations',
        onError: (error) => {
          console.warn('Translation fetch warning:', error);
          return {};
        },
        cache: ['translations'],
      });

      await response.fetch();
      translations.value = response.data || {};
      isInitialized.value = true;
      return translations.value;
    } catch (error) {
      retryCount++;
      if (retryCount === maxRetries) {
        console.warn('Translation fetch failed after retries:', error);
        isInitialized.value = true;
        return {};
      }
      await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, retryCount)));
    }
  }
}

// Single export for the translation plugin
export default {
  install: (app) => {
    // Register the translation function globally
    app.config.globalProperties.__ = __;
    app.provide('__', __);

    // Load translations in the background
    fetchTranslations().then(() => {
      // No need to update the function reference since we're using a reactive store
      console.log('Translations loaded');
    }).catch(error => {
      console.warn('Translation plugin initialization warning:', error);
    });
  },
};

// Export initialization status
export const translationsReady = isInitialized;