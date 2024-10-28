<template>
  <div>
    <div class="flex flex-wrap gap-1">
      <Button
        ref="dealElements"
        v-for="value in values"
        :key="value"
        :label="value"
        theme="gray"
        variant="subtle"
        class="rounded"
        @keydown.delete.capture.stop="removeLastValue"
      >
        <template #suffix>
          <FeatherIcon
            class="h-3.5"
            name="x"
            @click.stop="removeValue(value)"
          />
        </template>
      </Button>
      <div class="basis-full">
        <Combobox v-model="selectedValue" nullable>
          <Popover class="w-full" v-model:show="showOptions">
            <template #target="{ togglePopover }">
              <ComboboxInput
                ref="search"
                class="search-input form-input w-full border-none bg-white hover:bg-white focus:border-none focus:!shadow-none focus-visible:!ring-0"
                type="text"
                :value="query"
                placeholder="Search"
                @change="
                  (e) => {
                    query = e.target.value
                    showOptions = true
                  }
                "
                autocomplete="off"
                @focus="() => togglePopover()"
                @keydown.delete.capture.stop="removeLastValue"
              />
            </template>
            <template #body="{ isOpen }">
              <div v-show="isOpen">
                <div class="mt-1 rounded-lg bg-white py-1 text-base shadow-2xl">
                  <ComboboxOptions
                    class="my-1 max-h-[12rem] overflow-y-auto px-1.5"
                    static
                  >
                    <ComboboxOption
                      v-for="option in options"
                      :value="option"
                      v-slot="{ active }"
                    >
                      <li
                        :class="[
                          'flex cursor-pointer items-center rounded px-2 py-1 text-base',
                          { 'bg-gray-100': active },
                        ]"
                      >
                        <div class="flex flex-col gap-1 p-1 text-gray-800">
                          <div class="text-base font-medium">
                            {{ option }}
                          </div>
                          <div class="text-sm text-gray-600">
                            {{ option }}
                          </div>
                        </div>
                      </li>
                    </ComboboxOption>
                  </ComboboxOptions>
                </div>
              </div>
            </template>
          </Popover>
        </Combobox>
      </div>
    </div>
    <ErrorMessage class="mt-2 pl-2" v-if="error" :message="error" />
  </div>
</template>

<script setup>
import {
  Combobox,
  ComboboxInput,
  ComboboxOptions,
  ComboboxOption,
} from '@headlessui/vue'
import UserAvatar from '@/components/UserAvatar.vue'
import Popover from '@/components/frappe-ui/Popover.vue'
import { createResource } from 'frappe-ui'
import { ref, computed, nextTick } from 'vue'
import { watchDebounced } from '@vueuse/core'
import DealElement from '../frappe-ui/DealElement.vue'

const props = defineProps({
  dealName: {
    type: String,
    required: true,
  },
  validate: {
    type: Function,
    default: null,
  },
  errorMessage: {
    type: Function,
    default: (value) => `${value} is an Invalid value`,
  },
})

const values = defineModel()

const dealElements = ref([])
const search = ref(null)
const error = ref(null)
const query = ref('')
const text = ref('')
const showOptions = ref(false)

const selectedValue = computed({
  get: () => query.value,
  set: (val) => {
    query.value = ''
    if (val) {
      showOptions.value = false
      addValue(val)
    }
  },
})

watchDebounced(
  query,
  (val) => {
    val = val || ''
    if (text.value === val && options?.length) return
    text.value = val
    reload(val)
  },
  { debounce: 300, immediate: true },
)

const filterOptions = createResource({
  url: 'crm.fcrm.doctype.crm_deal.api.get_deal_elements',
  transform: (data) => {
    // Access the actual data from the proxy object
    const actualData = unwrapProxy(data);
    
    return actualData.map((option) => option.name);
  },
});

const options = computed(() => {
  let searchedContacts = filterOptions || [];
  return searchedContacts.data;
})

function reload(val) {
  filterOptions.update({
    params: { txt: val },
  })
  filterOptions.reload()
}

const addValue = (value) => {
  console.log(value);
  
  error.value = null
  if (value) {
    const splitValues = value.split(',')
    splitValues.forEach((value) => {
      value = value.trim()
      if (value) {
        // check if value is not already in the values array
        if (!values.value?.includes(value)) {
          // check if value is valid
          if (value && props.validate && !props.validate(value)) {
            error.value = props.errorMessage(value)
            return
          }
          // add value to values array
          if (!values.value) {
            values.value = [value]
            updateDeal(values.value, props.dealName);
          } else {
            values.value.push(value)
            updateDeal(values.value, props.dealName);
          }
          value = value.replace(value, '')
        }
      }
    })
    !error.value && (value = '')
  }
}

const removeValue = (value) => {
  values.value = values.value.filter((v) => v !== value)
  updateDeal(values.value, props.dealName, value);

}

const removeLastValue = () => {
  if (query.value) return

  let dealElementRef = dealElements.value[dealElements.value.length - 1]?.$el
  if (document.activeElement === dealElementRef) {
    values.value.pop()
    updateDeal(values.value, props.dealName);
    nextTick(() => {
      if (values.value.length) {
        dealElementRef = dealElements.value[dealElements.value.length - 1].$el
        dealElementRef?.focus()
      } else {
        setFocus()
      }
    })
  } else {
    dealElementRef?.focus()
  }
}

function setFocus() {
  search.value.$el.focus()
}
/**
 *  Convert proxy object into array
 * @param proxyData 
 */
 function unwrapProxy(proxyData) {
  if (Array.isArray(proxyData)) {
    return proxyData.map((item) => unwrapProxy(item));
  } 
  else if (proxyData !== null && typeof proxyData === 'object') {
    return Object.keys(proxyData).reduce((acc, key) => {
      acc[key] = unwrapProxy(proxyData[key]);
      return acc;
    }, {});
  }
  return proxyData;
}
function updateDeal(dealData, dealName, val="") {
  if(val){
    dealData = dealData.filter((v) => v !== val)
  }
  createResource({
    url: 'crm.fcrm.doctype.crm_deal.api.update_crm_deal_elements',
    params: {
      doctype: 'CRM Deal',
      name: dealName,
      deal_elements: dealData,
    },
    auto: true,
    onSuccess: () => {
      deal.reload()
      reload.value = true
      createToast({
        title: __('Deal updated'),
        icon: 'check',
        iconClasses: 'text-green-600',
      })
      callback?.()
    },
    onError: (err) => {
      createToast({
        title: __('Error updating deal'),
        text: __(err.messages?.[0]),
        icon: 'x',
        iconClasses: 'text-red-600',
      })
    },
  })
}
defineExpose({ setFocus })
</script>
