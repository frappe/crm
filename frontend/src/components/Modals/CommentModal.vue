<template>
    <Dialog
        :modelValue="show"
        :title="__('Add Comment')"
        @update:modelValue="handleDialogUpdate"
        @close="handleClose"
        class="comment-dialog"
    >
        <template #body>
            <div class="space-y-6 p-4">
                <!-- User Info -->
                <div class="flex items-center gap-3">
                    <Avatar
                        :label="userInitials"
                        :image="userImage"
                        size="md"
                        class="bg-blue-100"
                    />
                    <div>
                        <div class="font-medium text-gray-900">{{ userName }}</div>
                        <div class="text-sm text-gray-500">{{ userEmail }}</div>
                    </div>
                </div>

                <!-- Comment Input -->
                <div class="relative">
                    <textarea
                        v-model="newComment"
                        class="w-full p-4 border rounded-lg resize-none transition-shadow duration-200 bg-gray-50"
                        :class="{ 'border-gray-300': !newComment.trim(), 'border-gray-400': newComment.trim() }"
                        rows="4"
                        :placeholder="__('Write your comment here...')"
                        @keydown.ctrl.enter="submitComment"
                    ></textarea>
                    <div class="absolute bottom-2 right-2 text-xs text-gray-400">
                        {{ __('Press Ctrl + Enter to submit') }}
                    </div>
                </div>

                <!-- Action Buttons -->
                <div class="flex justify-end gap-3">
                    <Button
                        variant="subtle"
                        @click="handleClose"
                        class="hover:bg-gray-100 transition-colors duration-200"
                    >
                        {{ __('Cancel') }}
                    </Button>
                    <Button
                        variant="solid"
                        :disabled="!newComment.trim()"
                        @click="submitComment"
                        :loading="isSubmitting"
                        class="bg-gray-900 hover:bg-gray-800 text-white transition-colors duration-200"
                    >
                        {{ __('Post Comment') }}
                    </Button>
                </div>
            </div>
        </template>
    </Dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { call } from 'frappe-ui'
import { usersStore } from '@/stores/users'

const props = defineProps({
    show: {
        type: Boolean,
        required: true
    },
    doctype: {
        type: String,
        required: true
    },
    docname: {
        type: String,
        required: true
    }
})

const emit = defineEmits(['update:show', 'comment-added'])
const { getUser } = usersStore()
const currentUser = computed(() => getUser())

const newComment = ref('')
const isSubmitting = ref(false)

// User information
const userName = computed(() => currentUser.value?.full_name || '')
const userEmail = computed(() => currentUser.value?.email || '')
const userImage = computed(() => currentUser.value?.user_image || '')
const userInitials = computed(() => {
    const name = userName.value
    return name
        .split(' ')
        .map(word => word[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
})

function handleDialogUpdate(value) {
    emit('update:show', value)
}

function handleClose() {
    newComment.value = ''
    emit('update:show', false)
}

async function submitComment() {
    if (!newComment.value.trim() || isSubmitting.value) return

    isSubmitting.value = true
    try {
        await call('frappe.desk.form.utils.add_comment', {
            reference_doctype: props.doctype,
            reference_name: props.docname,
            content: newComment.value,
            comment_email: userEmail.value,
            comment_by: userName.value
        })
        
        emit('comment-added')
        handleClose()
    } catch (error) {
        console.error('Error adding comment:', error)
    } finally {
        isSubmitting.value = false
    }
}
</script>

<style scoped>
.comment-dialog :deep(.dialog-container) {
    max-width: 600px;
}

.comment-dialog textarea {
    min-height: 120px;
    font-size: 14px;
    line-height: 1.5;
}

.comment-dialog textarea:focus {
    outline: none;
    border-color: #9ca3af; /* gray-400 */
    box-shadow: none;
}

/* Custom scrollbar for textarea */
.comment-dialog textarea::-webkit-scrollbar {
    width: 8px;
}

.comment-dialog textarea::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 4px;
}

.comment-dialog textarea::-webkit-scrollbar-thumb {
    background: #ccc;
    border-radius: 4px;
}

.comment-dialog textarea::-webkit-scrollbar-thumb:hover {
    background: #999;
}
</style>