<template>
  <div class="flex overflow-x-auto h-full dark-scrollbar">
    <Draggable
      v-if="columns"
      :list="columns"
      item-key="column"
      @end="updateColumn"
      :delay="isTouchScreenDevice() ? 200 : 0"
      class="flex sm:mx-2.5 mx-2 pb-3.5"
    >
      <template #item="{ element: column }">
        <div
          v-if="!column.column.delete"
          class="flex flex-col gap-2.5 min-w-72 w-72 hover:bg-surface-gray-2 rounded-lg p-2.5"
        >
          <div class="flex gap-2 items-center group justify-between">
            <div class="flex items-center text-base">
              <NestedPopover>
                <template #target>
                  <Button
                    variant="ghost"
                    size="sm"
                    class="hover:!bg-surface-gray-2"
                  >
                    <IndicatorIcon :class="parseColor(column.column.color)" />
                  </Button>
                </template>
                <template #body="{ close }">
                  <div
                    class="flex flex-col gap-3 px-3 py-2.5 min-w-40 rounded-lg bg-surface-modal shadow-2xl ring-1 ring-black ring-opacity-5 focus:outline-none"
                  >
                    <div class="flex gap-1">
                      <Button
                        variant="ghost"
                        v-for="color in colors"
                        :key="color"
                        @click="() => (column.column.color = color)"
                      >
                        <IndicatorIcon :class="parseColor(color)" />
                      </Button>
                    </div>
                    <div class="flex flex-row-reverse">
                      <Button
                        variant="solid"
                        :label="__('Apply')"
                        @click="updateColumn"
                      />
                    </div>
                  </div>
                </template>
              </NestedPopover>
              <div class="text-ink-gray-9">{{ __(column.column.name) }}</div>
            </div>
            <div class="flex">
              <Dropdown :options="actions(column)">
                <template #default>
                  <Button
                    class="hidden group-hover:flex"
                    icon="more-horizontal"
                    variant="ghost"
                  />
                </template>
              </Dropdown>
              <Button
                icon="plus"
                variant="ghost"
                @click="options.onNewClick(column)"
              />
            </div>
          </div>
          <div class="overflow-y-auto flex flex-col gap-2 h-full dark-scrollbar">
            <Draggable
              :list="column.data"
              group="fields"
              item-key="name"
              class="flex flex-col gap-3.5 flex-1"
              @end="updateColumn"
              :delay="isTouchScreenDevice() ? 200 : 0"
              :data-column="column.column.name"
            >
              <template #item="{ element: fields }">
                <component
                  :is="options.getRoute ? 'router-link' : 'div'"
                  class="relative pt-3 px-3.5 pb-2.5 rounded-lg border bg-surface-white text-base flex flex-col text-ink-gray-9 shadow-sm hover:shadow-md transition-all duration-200 dark:bg-surface-gray-1 dark:border-surface-gray-3 hover:border-gray-300 dark:hover:border-surface-gray-4 dark:hover:bg-surface-gray-2 dark:hover:shadow-lg dark:hover:shadow-gray-900/30"
                  :data-name="fields.name"
                  v-bind="{
                    to: options.getRoute ? options.getRoute(fields) : undefined,
                    onClick: options.onClick
                      ? () => options.onClick(fields)
                      : undefined,
                  }"
                >
                  <div 
                    v-if="updatingCards.has(fields.name)"
                    class="absolute right-2 top-2 z-10"
                  >
                    <FeatherIcon 
                      name="refresh-cw" 
                      class="text-info-500 animate-spin h-4 w-4" 
                    />
                  </div>
                  <slot
                    name="title"
                    v-bind="{ fields, titleField, itemName: fields.name }"
                  >
                    <div class="h-5 flex items-center">
                      <div v-if="fields[titleField]">
                        {{ fields[titleField] }}
                      </div>
                      <div class="text-ink-gray-4" v-else>
                        {{ __('No Title') }}
                      </div>
                    </div>
                  </slot>
                  <div class="border-b h-px my-2.5" />

                  <div class="flex flex-col gap-3.5">
                    <template v-for="value in column.fields" :key="value">
                      <slot
                        name="fields"
                        v-bind="{
                          fields,
                          fieldName: value,
                          itemName: fields.name,
                        }"
                      >
                        <div v-if="fields[value]" class="truncate">
                          {{ fields[value] }}
                        </div>
                      </slot>
                    </template>
                  </div>
                  <div class="border-b h-px mt-2.5 mb-2" />
                  <slot name="actions" v-bind="{ itemName: fields.name }">
                    <div class="flex gap-2 items-center justify-between">
                      <div></div>
                      <Button icon="plus" variant="ghost" @click.stop.prevent />
                    </div>
                  </slot>
                </component>
              </template>
            </Draggable>
            <div
              v-if="column.column.count < column.column.all_count"
              class="flex items-center justify-center"
            >
              <Button
                :label="__('Load More')"
                @click="emit('loadMore', column.column.name)"
              />
            </div>
          </div>
        </div>
      </template>
    </Draggable>
    <div v-if="deletedColumns.length" class="shrink-0 min-w-64">
      <Autocomplete
        value=""
        :options="deletedColumns"
        @change="(e) => addColumn(e)"
      >
        <template #target="{ togglePopover }">
          <Button
            class="w-full mt-2.5 mb-1 mr-5"
            @click="togglePopover()"
            :label="__('Add Column')"
          >
            <template #prefix>
              <FeatherIcon name="plus" class="h-4" />
            </template>
          </Button>
        </template>
      </Autocomplete>
    </div>
  </div>
</template>

<style>
.remote-update-highlight {
  animation: remote-update 2.5s ease;
}

@keyframes remote-update {
  0% {
    background: linear-gradient(45deg, transparent, var(--info-100), transparent);
    border-color: var(--info-300);
  }
  15% {
    background: linear-gradient(45deg, transparent, var(--info-200), transparent);
    border-color: var(--info-500);
  }
  85% {
    background: linear-gradient(45deg, transparent, var(--info-100), transparent);
    border-color: var(--info-300);
  }
  100% {
    background: transparent;
    border-color: var(--surface-border);
  }
}
</style>

<script setup>
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
import NestedPopover from '@/components/NestedPopover.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import { isTouchScreenDevice, colors, parseColor } from '@/utils'
import Draggable from 'vuedraggable'
import { Dropdown } from 'frappe-ui'
import { computed, onMounted, onUnmounted, watch, nextTick, ref } from 'vue'
import { useSocket, PRIORITY, startTransaction, endTransaction, isLocalTransaction } from '@/socket'
import { FeatherIcon, call } from 'frappe-ui'

const props = defineProps({
  options: {
    type: Object,
    default: () => ({
      getRoute: null,
      onClick: null,
      onNewClick: null,
    }),
  },
})

const emit = defineEmits(['update', 'loadMore'])
const kanban = defineModel()
const socket = useSocket()

// Track active subscriptions
const subscriptions = new Map()

// Track cards being updated
const updatingCards = ref(new Set())

// Flag to track if view needs refresh
const needsRefresh = ref(false)

// Store event handlers for cleanup
let docCreatedHandler = null;
let docDeletedHandler = null;

const titleField = computed(() => {
  return kanban.value?.data?.title_field
})

const columns = computed(() => {
  if (!kanban.value?.data?.data || kanban.value.data.view_type != 'kanban')
    return []
  let _columns = kanban.value.data.data

  let has_color = _columns.some((column) => column.column?.color)
  if (!has_color) {
    _columns.forEach((column, i) => {
      column.column['color'] = colors[i % colors.length]
    })
  }
  return _columns
})

async function updateColumn(d) {
  let toColumn = d?.to?.dataset.column
  let fromColumn = d?.from?.dataset.column
  let itemName = d?.item?.dataset.name

  let _columns = []
  columns.value.forEach((col) => {
    col.column['order'] = col.data.map((d) => d.name)
    if (col.column.page_length) {
      delete col.column.page_length
    }
    _columns.push(col.column)
  })

  let data = { kanban_columns: _columns }
  const doctype = kanban.value.params.doctype

  if (toColumn != fromColumn) {
    // Start transaction for card movement
    const transactionId = startTransaction(doctype, itemName)
    data = { 
      item: itemName, 
      to: toColumn, 
      kanban_columns: _columns,
      // Include transaction ID in server request
      _transaction: transactionId 
    }
    
    try {
      await emit('update', data)
    } finally {
      // Clean up transaction after server response
      endTransaction(doctype, itemName, transactionId)
    }
  } else {
    emit('update', data)
  }
}

// Helper function to highlight remote updates
function highlightRemoteUpdate(element, cardName) {
  if (!element) return
  
  // Should already be added to updatingCards when update begins
  // Now just add the animation class
  element.classList.add('remote-update-highlight')
  
  setTimeout(() => {
    element.classList.remove('remote-update-highlight')
    // Remove card from updating list after animation completes
    updatingCards.value.delete(cardName)
  }, 2500)
}

// Subscribe to updates for visible cards
function subscribeToVisibleCards() {
  // Safety check - ensure we have doctype
  const doctype = kanban.value?.params?.doctype
  if (!doctype) return

  // Unsubscribe from all current subscriptions
  for (const unsubscribe of subscriptions.values()) {
    unsubscribe()
  }
  subscriptions.clear()

  // Subscribe to all visible cards
  columns.value.forEach(column => {
    if (!column.column.delete) {
      column.data.forEach(card => {
        const unsubscribe = socket.subscribeToDoc(doctype, card.name, async (data) => {
          // Skip processing if update is from local transaction
          if (data._transaction && isLocalTransaction(doctype, card.name, data._transaction)) {
            return
          }
          
          // Handle document deletion
          if (data.event === 'deleted') {
            // Find and remove the card from its column
            const sourceColumn = columns.value.find(col => 
              col.data.some(c => c.name === card.name)
            );
            
            if (sourceColumn) {
              sourceColumn.data = sourceColumn.data.filter(c => 
                c.name !== card.name
              );
            }
            return;
          }
          
          // If received a modification notification
          if (data.event === 'modified') {
            // Show update indicator
            updatingCards.value.add(card.name)
            
            try {
              // Request current document data
              const updatedDoc = await call('frappe.client.get', {
                doctype: doctype,
                name: card.name
              });
              
              // Check if status has changed
              if (updatedDoc.status !== card.status) {
                // Find target column
                const targetColumn = columns.value.find(col => 
                  col.column.name === updatedDoc.status
                );
                
                if (targetColumn) {
                  // Remove card from current column
                  const sourceColumn = columns.value.find(col => 
                    col.data.some(c => c.name === card.name)
                  );
                  if (sourceColumn) {
                    sourceColumn.data = sourceColumn.data.filter(c => 
                      c.name !== card.name
                    );
                  }
                  
                  // Update card data
                  Object.assign(card, updatedDoc);
                  
                  // Add card to target column and sort according to order_by
                  targetColumn.data.push(card);
                  
                  // Sort the column data according to the current order_by parameter
                  const order_by = kanban.value?.params?.order_by;
                  if (order_by) {
                    const [field, direction] = order_by.split(' ');
                    targetColumn.data.sort((a, b) => {
                      if (direction === 'desc') {
                        return a[field] > b[field] ? -1 : 1;
                      } else {
                        return a[field] < b[field] ? -1 : 1;
                      }
                    });
                  }
                } 
              } else {
                // Just update card data
                Object.assign(card, updatedDoc);
              }
              
              // Highlight updated card
              await nextTick();
              const cardElement = document.querySelector(`[data-name="${card.name}"]`);
              highlightRemoteUpdate(cardElement, card.name);
            } catch (error) {
              console.error('Error fetching updated document:', error);
              // Remove update indicator in case of error
              updatingCards.value.delete(card.name);
            }
          }
        }, PRIORITY.VIEWPORT);
        
        subscriptions.set(card.name, unsubscribe);
      });
    }
  });
}

// Listen for document creation events
function setupDocCreationListener() {
  const doctype = kanban.value?.params?.doctype;
  if (!doctype) return;
  
  // Listen for document creation events using CustomEvent
  const handleDocCreated = (event) => {
    const { doctype: eventDoctype, name } = event.detail;
    console.log(`[KanbanView] Received document creation event: ${eventDoctype}/${name}`);
    
    if (eventDoctype === doctype) {
      // Set flag to refresh view on next user interaction or after a delay
      needsRefresh.value = true;
      console.log(`[KanbanView] Setting refresh flag for ${doctype}`);
      
      // Refresh the view after a short delay to avoid too many refreshes
      // if multiple documents are created in quick succession
      setTimeout(() => {
        if (needsRefresh.value) {
          console.log(`[KanbanView] Refreshing view for ${doctype}`);
          refreshView();
          needsRefresh.value = false;
        }
      }, 1000);
    }
  };
  
  // Add event listener
  window.addEventListener('crm:doc_created', handleDocCreated);
  console.log(`[KanbanView] Set up document creation listener for ${doctype}`);
  
  // Store the handler for cleanup
  return handleDocCreated;
}

// Listen for document deletion events
function setupDocDeletionListener() {
  const doctype = kanban.value?.params?.doctype;
  if (!doctype) return;
  
  // Listen for document deletion events using CustomEvent
  const handleDocDeleted = (event) => {
    const { doctype: eventDoctype, name } = event.detail;
    console.log(`[KanbanView] Received document deletion event: ${eventDoctype}/${name}`);
    
    if (eventDoctype === doctype) {
      // Check if the document is in any column
      let found = false;
      
      columns.value.forEach(column => {
        if (!column.column.delete) {
          // Find the card in the column
          const cardIndex = column.data.findIndex(card => card.name === name);
          
          if (cardIndex !== -1) {
            console.log(`[KanbanView] Removing deleted card ${name} from column ${column.column.name}`);
            // Remove the card from the column
            column.data.splice(cardIndex, 1);
            found = true;
          }
        }
      });
      
      // If we didn't find the card in any column, it might be outside our view
      // We'll refresh the view to ensure consistency
      if (!found) {
        console.log(`[KanbanView] Deleted card ${name} not found in current view, refreshing`);
        needsRefresh.value = true;
        
        setTimeout(() => {
          if (needsRefresh.value) {
            refreshView();
            needsRefresh.value = false;
          }
        }, 1000);
      }
    }
  };
  
  // Add event listener
  window.addEventListener('crm:doc_deleted', handleDocDeleted);
  console.log(`[KanbanView] Set up document deletion listener for ${doctype}`);
  
  // Store the handler for cleanup
  return handleDocDeleted;
}

// Refresh the kanban view to get new documents
function refreshView() {
  console.log(`[KanbanView] Reloading kanban view`);
  kanban.value.reload();
}

// Watch for changes in visible cards and doctype
watch([
  () => columns.value.map(col => col.data.map(card => card.name)).flat(),
  () => kanban.value?.params?.doctype
], () => {
  subscribeToVisibleCards();
}, { deep: true })

onMounted(() => {
  subscribeToVisibleCards();
  // Setup document creation and deletion listeners
  docCreatedHandler = setupDocCreationListener();
  docDeletedHandler = setupDocDeletionListener();
})

onUnmounted(() => {
  // Cleanup all subscriptions
  for (const unsubscribe of subscriptions.values()) {
    unsubscribe();
  }
  subscriptions.clear();
  
  // Remove document event listeners
  if (docCreatedHandler) {
    window.removeEventListener('crm:doc_created', docCreatedHandler);
  }
  if (docDeletedHandler) {
    window.removeEventListener('crm:doc_deleted', docDeletedHandler);
  }
})

const deletedColumns = computed(() => {
  return columns.value
    .filter((col) => col.column['delete'])
    .map((col) => {
      return { label: col.column.name, value: col.column.name }
    })
})

function actions(column) {
  return [
    {
      group: __('Options'),
      hideLabel: true,
      items: [
        {
          label: __('Delete'),
          icon: 'trash-2',
          onClick: () => {
            column.column['delete'] = true
            updateColumn()
          },
        },
      ],
    },
  ]
}

function addColumn(e) {
  let column = columns.value.find((col) => col.column.name == e.value)
  column.column['delete'] = false
  updateColumn()
}
</script>
