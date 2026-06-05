<template>
    <div>
        <label class="text-xs font-medium uppercase tracking-wide text-ink-gray-5">
            {{ label }}
        </label>

        <!-- Readonly -->
        <div v-if="readonly" class="mt-1 text-sm text-ink-gray-9">
            {{ modelValue || value || '-' }}
        </div>

        <!-- Checkbox -->
        <div v-else-if="type === 'checkbox'" class="mt-2">
            <input type="checkbox" :checked="!!modelValue" @change="onChange($event.target.checked ? 1 : 0)"
                class="h-4 w-4 rounded border-outline-gray-3" />
        </div>

        <!-- Select -->
        <select v-else-if="type === 'select'" :value="modelValue" @change="onChange($event.target.value)"
            class="mt-1 w-full rounded border border-outline-gray-2 bg-surface-white px-2 py-1.5 text-sm focus:border-outline-gray-4 focus:outline-none">
            <option v-for="opt in options" :key="opt" :value="opt">{{ opt }}</option>
        </select>

        <!-- Textarea -->
        <textarea v-else-if="type === 'textarea'" :value="modelValue" @blur="onChange($event.target.value)"
            class="mt-1 w-full rounded border border-outline-gray-2 bg-surface-white px-2 py-1.5 text-sm focus:border-outline-gray-4 focus:outline-none"
            rows="3" />

        <!-- Link / Autocomplete -->
        <Autocomplete v-else-if="type === 'link'" :modelValue="modelValue" :options="linkOptions" class="mt-1"
            @update:modelValue="(v) => onChange(v?.value || v)" />

        <!-- Default (text/number/date) -->
        <input v-else :type="inputType" :value="modelValue"
            @blur="onChange(inputType === 'number' ? Number($event.target.value) : $event.target.value)"
            class="mt-1 w-full rounded border border-outline-gray-2 bg-surface-white px-2 py-1.5 text-sm focus:border-outline-gray-4 focus:outline-none" />
    </div>
    <div v-if="readonly" class="mt-1 text-sm text-ink-gray-9 px-2 py-1.5 bg-surface-gray-2 rounded">
        {{ modelValue || value || '-' }}
    </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Autocomplete, createResource } from 'frappe-ui'

const props = defineProps({
    label: String,
    modelValue: [String, Number, Boolean],
    value: [String, Number, Boolean],
    type: { type: String, default: 'text' },
    options: Array,
    doctype: String,
    readonly: Boolean,
})

const emit = defineEmits(['update:modelValue', 'save'])

const linkOptions = ref([])

const inputType = computed(() => {
    if (props.type === 'number') return 'number'
    if (props.type === 'date') return 'date'
    if (props.type === 'datetime') return 'datetime-local'
    return 'text'
})

if (props.type === 'link' && props.doctype) {
    createResource({
        url: 'frappe.client.get_list',
        params: {
            doctype: props.doctype,
            fields: ['name'],
            limit_page_length: 50,
        },
        auto: true,
        onSuccess(data) {
            linkOptions.value = data.map((d) => ({ label: d.name, value: d.name }))
        },
    })
}

function onChange(val) {
    emit('update:modelValue', val)
    emit('save', val)
}
</script>