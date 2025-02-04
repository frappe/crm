<template>
    <div class="timeline-view">
        <!-- Filters -->
        <div class="flex justify-between mb-4">
            <div class="flex gap-2">
                <Button v-for="filter in availableFilters" :key="filter" size="sm"
                    :variant="activeFilters.includes(filter) ? 'solid' : 'subtle'" @click="toggleFilter(filter)">
                    {{ __(filter) }}
                </Button>
            </div>
            <Button variant="solid" size="sm" @click="showCommentModal = true">
                {{ __('New Comment') }}
            </Button>
        </div>

        <!-- Timeline -->
        <div class="space-y-4">
            <template v-for="(group, date) in groupedActivities" :key="date">
                <TimelineGroup :date="date" :group="group" />
            </template>
        </div>

        <!-- Comment Modal -->
        <CommentModal
            v-model:show="showCommentModal"
            :doctype="props.doctype"
            :docname="props.docname"
            @comment-added="handleCommentAdded"
        />
    </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { usersStore } from '@/stores/users'
import TimelineGroup from './TimelineGroup.vue'
import CommentModal from '../Modals/CommentModal.vue'

const { getUser } = usersStore()
const showCommentModal = ref(false)

const props = defineProps({
    items: {
        type: Array,
        default: () => []
    },
    filters: {
        type: Array,
        default: () => ['emails', 'notes', 'comments']
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

const emit = defineEmits(['filter-change', 'comment-added'])

const availableFilters = computed(() => props.filters)
const activeFilters = ref([...props.filters])

const groupedActivities = computed(() => {
    return props.items
        .filter(item => activeFilters.value.includes(item.type + 's'))
        .reduce((groups, activity) => {
            const date = activity.timestamp.split('T')[0]
            groups[date] = groups[date] || []
            groups[date].push(activity)
            return groups
        }, {})
})

function toggleFilter(filter) {
    const index = activeFilters.value.indexOf(filter)
    if (index === -1) {
        activeFilters.value.push(filter)
    } else {
        activeFilters.value.splice(index, 1)
    }
    emit('filter-change', activeFilters.value)
}

function handleCommentAdded() {
    showCommentModal.value = false
    emit('comment-added')
}
</script>

<style scoped>
.timeline-view {
    @apply p-4;
}
</style>