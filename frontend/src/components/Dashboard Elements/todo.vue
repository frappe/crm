<template>
  <todo-app></todo-app>
<!--  <div class="w-full p-4">-->
<!--    &lt;!&ndash; Widget Header &ndash;&gt;-->
<!--    <div class="flex items-center justify-between pb-3 mb-4 border-b border-gray-100">-->
<!--      <h3 class="text-sm font-medium text-gray-900">Tasks</h3>-->
<!--      <p class="text-xs text-gray-500">{{ completedCount }}/{{ todos.length }} completed</p>-->
<!--    </div>-->

<!--    &lt;!&ndash; Add Task Form - Minimal Version &ndash;&gt;-->
<!--    <div class="py-3 mb-4 flex items-center gap-3">-->
<!--      <input-->
<!--        v-model="newTodo"-->
<!--        @keyup.enter="addTodo"-->
<!--        type="text"-->
<!--        placeholder="Add a task..."-->
<!--        class="flex-1 px-3 py-2 text-sm border-b border-gray-200 focus:outline-none focus:border-blue-500 placeholder-gray-400 bg-transparent transition-colors"-->
<!--      />-->
<!--      <input-->
<!--        v-model="dueDate"-->
<!--        type="date"-->
<!--        :min="today"-->
<!--        class="w-32 px-2 py-1.5 text-xs border-b border-gray-200 focus:outline-none focus:border-blue-500 bg-transparent transition-colors"-->
<!--      />-->
<!--      <button-->
<!--        @click="addTodo"-->
<!--        :disabled="!newTodo.trim()"-->
<!--        class="p-2 text-blue-600 hover:text-blue-800 hover:bg-blue-50 disabled:text-gray-300 disabled:cursor-not-allowed transition-all rounded-md"-->
<!--        aria-label="Add task"-->
<!--      >-->
<!--        <PlusCircle class="w-5 h-5" />-->
<!--      </button>-->
<!--    </div>-->

<!--    &lt;!&ndash; Task List &ndash;&gt;-->
<!--    <div class="max-h-80 overflow-y-auto">-->
<!--      <div v-if="todos.length === 0" class="py-8 text-center">-->
<!--        <div class="text-gray-300 mb-3">-->
<!--          <CheckSquare class="w-8 h-8 mx-auto" />-->
<!--        </div>-->
<!--        <p class="text-sm text-gray-400">No tasks yet</p>-->
<!--      </div>-->

<!--      <div v-else class="space-y-1">-->
<!--        <div-->
<!--          v-for="(todo, index) in sortedTodos"-->
<!--          :key="todo.id"-->
<!--          class="group py-3 px-3 flex items-start gap-3 hover:bg-gray-50 transition-colors rounded-lg"-->
<!--          :class="todo.isOverdue && !todo.completed ? 'border-l-3 border-l-red-400 bg-red-25 pl-4' : ''"-->
<!--        >-->
<!--          &lt;!&ndash; Checkbox &ndash;&gt;-->
<!--          <input-->
<!--            :id="`todo-${todo.id}`"-->
<!--            v-model="todo.completed"-->
<!--            type="checkbox"-->
<!--            class="mt-1 w-4 h-4 text-blue-600 bg-white border-gray-300 rounded focus:ring-blue-500 focus:ring-1"-->
<!--          />-->

<!--          &lt;!&ndash; Task Content &ndash;&gt;-->
<!--          <div class="flex-1 min-w-0">-->
<!--            <label-->
<!--              :for="`todo-${todo.id}`"-->
<!--              :class="[-->
<!--                'block text-sm cursor-pointer transition-all leading-relaxed',-->
<!--                todo.completed-->
<!--                  ? 'text-gray-400 line-through'-->
<!--                  : todo.isOverdue ? 'text-red-700 font-medium' : 'text-gray-700'-->
<!--              ]"-->
<!--            >-->
<!--              {{ todo.text }}-->
<!--            </label>-->

<!--            &lt;!&ndash; Due Date &ndash;&gt;-->
<!--            <div v-if="todo.dueDate" class="flex items-center gap-1.5 mt-1.5">-->
<!--              <Calendar class="w-3 h-3 text-gray-400" />-->
<!--              <span :class="[-->
<!--                'text-xs',-->
<!--                todo.isOverdue && !todo.completed ? 'text-red-600 font-medium' : 'text-gray-500'-->
<!--              ]">-->
<!--                {{ formatDueDate(todo.dueDate) }}-->
<!--                <span v-if="todo.isOverdue && !todo.completed" class="text-red-600 ml-1">-->
<!--                  • Overdue-->
<!--                </span>-->
<!--              </span>-->
<!--            </div>-->
<!--          </div>-->

<!--          &lt;!&ndash; Delete Button &ndash;&gt;-->
<!--          <button-->
<!--            @click="removeTodo(index)"-->
<!--            class="opacity-0 group-hover:opacity-100 p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 focus:opacity-100 focus:outline-none transition-all rounded"-->
<!--            :aria-label="`Delete task: ${todo.text}`"-->
<!--          >-->
<!--            <X class="w-4 h-4" />-->
<!--          </button>-->
<!--        </div>-->
<!--      </div>-->
<!--    </div>-->

<!--    &lt;!&ndash; Widget Footer &ndash;&gt;-->
<!--    <div v-if="todos.length > 0" class="pt-3 mt-4 border-t border-gray-100">-->
<!--      <div class="flex items-center justify-between text-xs px-1">-->
<!--        <span class="text-gray-600">-->
<!--          {{ pendingCount }} pending-->
<!--        </span>-->
<!--        <span v-if="overdueCount > 0" class="text-red-600 font-medium">-->
<!--          {{ overdueCount }} overdue-->
<!--        </span>-->
<!--      </div>-->
<!--    </div>-->
<!--  </div>-->
</template>

<script setup>
import(window.location.origin+"/assets/cn_todo_manager/todoapp/index.js")
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { X, Calendar, CheckSquare, PlusCircle } from 'lucide-vue-next'

// Reactive data
const newTodo = ref('')
const dueDate = ref('')
const todos = ref([])
let nextId = 1

// Get today's date in YYYY-MM-DD format
const today = new Date().toISOString().split('T')[0]

// Mock data
const initializeMockData = () => {
  const yesterday = new Date()
  yesterday.setDate(yesterday.getDate() - 1)

  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)

  const nextWeek = new Date()
  nextWeek.setDate(nextWeek.getDate() + 7)

  todos.value = [
    {
      id: nextId++,
      text: 'Review quarterly budget report',
      completed: false,
      dueDate: yesterday.toISOString().split('T')[0],
      isOverdue: true
    },
    {
      id: nextId++,
      text: 'Call client about project requirements',
      completed: false,
      dueDate: today,
      isOverdue: false
    },
    {
      id: nextId++,
      text: 'Update team on sprint progress',
      completed: true,
      dueDate: yesterday.toISOString().split('T')[0],
      isOverdue: false
    },
    {
      id: nextId++,
      text: 'Prepare presentation for stakeholders',
      completed: false,
      dueDate: tomorrow.toISOString().split('T')[0],
      isOverdue: false
    },
    {
      id: nextId++,
      text: 'Review code changes from team',
      completed: false,
      dueDate: null,
      isOverdue: false
    },
    {
      id: nextId++,
      text: 'Send invoice to accounting',
      completed: true,
      dueDate: null,
      isOverdue: false
    },
    {
      id: nextId++,
      text: 'Schedule team building event',
      completed: false,
      dueDate: nextWeek.toISOString().split('T')[0],
      isOverdue: false
    }
  ]
}

// Computed properties
const completedCount = computed(() => {
  return todos.value.filter(todo => todo.completed).length
})

const pendingCount = computed(() => {
  return todos.value.filter(todo => !todo.completed).length
})

const overdueCount = computed(() => {
  return todos.value.filter(todo => todo.isOverdue && !todo.completed).length
})

const sortedTodos = computed(() => {
  return [...todos.value].sort((a, b) => {
    // Completed tasks go to bottom
    if (a.completed !== b.completed) {
      return a.completed ? 1 : -1
    }

    // Among incomplete tasks, overdue tasks go to top
    if (!a.completed && !b.completed) {
      if (a.isOverdue !== b.isOverdue) {
        return a.isOverdue ? -1 : 1
      }

      // Sort by due date if both have dates
      if (a.dueDate && b.dueDate) {
        return new Date(a.dueDate) - new Date(b.dueDate)
      }

      // Tasks with due dates come before those without
      if (a.dueDate && !b.dueDate) return -1
      if (!a.dueDate && b.dueDate) return 1
    }

    return 0
  })
})

// Check for overdue tasks
const checkOverdueTasks = () => {
  const now = new Date()

  todos.value.forEach(todo => {
    if (todo.dueDate) {
      const dueDateTime = new Date(todo.dueDate)
      dueDateTime.setHours(23, 59, 59)
      todo.isOverdue = now > dueDateTime
    }
  })
}

// Methods
const addTodo = () => {
  if (newTodo.value.trim()) {
    const newTask = {
      id: nextId++,
      text: newTodo.value.trim(),
      completed: false,
      dueDate: dueDate.value || null,
      isOverdue: false
    }

    // Check if it's already overdue
    if (newTask.dueDate) {
      const now = new Date()
      const dueDateTime = new Date(newTask.dueDate)
      dueDateTime.setHours(23, 59, 59)
      newTask.isOverdue = now > dueDateTime
    }

    todos.value.push(newTask)
    newTodo.value = ''
    dueDate.value = ''
  }
}

const removeTodo = (index) => {
  const originalIndex = todos.value.findIndex(todo => todo.id === sortedTodos.value[index].id)
  todos.value.splice(originalIndex, 1)
}

const formatDueDate = (dateString) => {
  if (!dateString) return ''

  const date = new Date(dateString)
  const today = new Date()
  const tomorrow = new Date(today)
  tomorrow.setDate(tomorrow.getDate() + 1)

  // Reset time for comparison
  const dateOnly = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  const todayOnly = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  const tomorrowOnly = new Date(tomorrow.getFullYear(), tomorrow.getMonth(), tomorrow.getDate())

  if (dateOnly.getTime() === todayOnly.getTime()) {
    return 'Today'
  } else if (dateOnly.getTime() === tomorrowOnly.getTime()) {
    return 'Tomorrow'
  } else {
    return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
  }
}

// Initialize mock data and check for overdue tasks
onMounted(() => {
  initializeMockData()
  checkOverdueTasks()
})

// Check for overdue tasks periodically
const intervalId = setInterval(checkOverdueTasks, 60000)

onUnmounted(() => {
  clearInterval(intervalId)
})
</script>

<style scoped>
.bg-gray-25 {
  background-color: #fafafa;
}

.bg-red-25 {
  background-color: #fef2f2;
}

.border-l-3 {
  border-left-width: 3px;
}

.group:hover .group-hover\:opacity-100 {
  opacity: 1;
}

/* Custom scrollbar for webkit browsers */
.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: transparent;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}
</style>