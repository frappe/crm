import { io } from 'socket.io-client'
import { socketio_port } from '../../../../sites/common_site_config.json'
import { getCachedListResource } from 'frappe-ui/src/resources/listResource'
import { getCachedResource } from 'frappe-ui/src/resources/resources'
import { reactive, ref } from 'vue'

// Subscription management
const subscriptions = reactive(new Map()) // { doctype:name: Set of callbacks }
const subscriptionQueue = reactive(new Map()) // { doctype:name: priority }
const MAX_SUBSCRIPTIONS = 50

// Priority levels
export const PRIORITY = {
  VIEWPORT: 3,    // Currently visible
  ADJACENT: 2,    // In adjacent columns/pages
  BACKGROUND: 1   // Not currently visible
}

const localTransactions = new Map()

/**
 * Generate a unique transaction ID combining timestamp and random string
 * @returns {string} Unique transaction ID
 */
function generateTransactionId() {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

/**
 * Start a new transaction for document modification
 * @param {string} doctype - Document type
 * @param {string} name - Document name
 * @returns {string} Transaction ID
 */
export function startTransaction(doctype, name) {
  const transactionId = generateTransactionId()
  localTransactions.set(`${doctype}:${name}`, transactionId)
  return transactionId
}

/**
 * End transaction if it matches the current transaction ID
 * @param {string} doctype - Document type
 * @param {string} name - Document name
 * @param {string} transactionId - Transaction ID to check
 */
export function endTransaction(doctype, name, transactionId) {
  const currentId = localTransactions.get(`${doctype}:${name}`)
  if (currentId === transactionId) {
    localTransactions.delete(`${doctype}:${name}`)
  }
}

/**
 * Check if the update is from a local transaction
 * @param {string} doctype - Document type
 * @param {string} name - Document name
 * @param {string} transactionId - Transaction ID to verify
 * @returns {boolean} True if it's a local transaction
 */
export function isLocalTransaction(doctype, name, transactionId) {
  return localTransactions.get(`${doctype}:${name}`) === transactionId
}

export function initSocket() {
  let host = window.location.hostname
  let siteName = window.site_name
  let port = window.location.port ? `:${socketio_port}` : ''
  let protocol = port ? 'http' : 'https'
  let url = `${protocol}://${host}${port}/${siteName}`

  const socket = io(url, {
    withCredentials: true,
    reconnectionAttempts: 5,
  })

  // Handle resource updates
  socket.on('refetch_resource', (data) => {
    if (data.cache_key) {
      let resource = getCachedResource(data.cache_key) || getCachedListResource(data.cache_key)
      if (resource) {
        resource.reload()
      }
    }
  })

  // Handle doc update events from server
  socket.on('doc_update', ({ doctype, name, data }) => {
    const key = `${doctype}:${name}`
    const callbacks = subscriptions.get(key)
    if (callbacks) {
      callbacks.forEach(callback => callback(data))
    }
  })

  // Handle doc update events from other tabs
  window.addEventListener('storage', (event) => {
    if (event.key === 'doc_update') {
      try {
        const { doctype, name, data } = JSON.parse(event.newValue)
        const key = `${doctype}:${name}`
        const callbacks = subscriptions.get(key)
        if (callbacks) {
          callbacks.forEach(callback => callback(data))
        }
      } catch (e) {
        console.error('Error processing cross-tab update:', e)
      }
    }
  })

  // Handle reconnection
  socket.on('connect', () => {
    // Resubscribe to all documents
    const batchResubscribe = async () => {
      const docs = Array.from(subscriptions.keys()).map(key => {
        const [doctype, name] = key.split(':')
        return { doctype, name }
      })
      
      // Resubscribe in batches
      for (let i = 0; i < docs.length; i += MAX_SUBSCRIPTIONS) {
        const batch = docs.slice(i, i + MAX_SUBSCRIPTIONS)
        await Promise.all(
          batch.map(doc => 
            socket.emit('subscribe_doc', doc)
          )
        )
      }
    }
    
    batchResubscribe()
  })

  return socket
}

const socket = initSocket()

// Socket composable for components
export function useSocket() {
  return {
    on(event, callback) {
      socket.on(event, callback)
    },
    off(event, callback) {
      socket.off(event, callback)
    },
    emit(event, data) {
      socket.emit(event, data)
      // If this is a doc update, broadcast to other tabs
      if (event === 'doc_update') {
        localStorage.setItem('doc_update', JSON.stringify(data))
        // Clear immediately to allow future updates of the same document
        setTimeout(() => localStorage.removeItem('doc_update'), 100)
      }
    },
    subscribeToDoc(doctype, name, callback, priority = PRIORITY.BACKGROUND) {
      return subscribeToDoc(doctype, name, callback, priority)
    }
  }
}

export function subscribeToDoc(doctype, name, callback, priority = PRIORITY.BACKGROUND) {
  const key = `${doctype}:${name}`
  
  // Update priority in queue
  const currentPriority = subscriptionQueue.get(key) || 0
  subscriptionQueue.set(key, Math.max(currentPriority, priority))
  
  // If we're already subscribed, just add the callback
  if (subscriptions.has(key)) {
    subscriptions.get(key).add(callback)
    return createCleanupFunction(key, callback)
  }
  
  // Check if we need to manage subscriptions
  if (subscriptions.size >= MAX_SUBSCRIPTIONS) {
    manageSubscriptions()
  }
  
  // Subscribe if we have room or high enough priority
  if (subscriptions.size < MAX_SUBSCRIPTIONS || priority > PRIORITY.BACKGROUND) {
    subscriptions.set(key, new Set([callback]))
    socket.emit('subscribe_doc', { doctype, name })
  }
  
  return createCleanupFunction(key, callback)
}

function createCleanupFunction(key, callback) {
  return () => {
    const subs = subscriptions.get(key)
    if (subs) {
      subs.delete(callback)
      if (subs.size === 0) {
        subscriptions.delete(key)
        subscriptionQueue.delete(key)
        socket.emit('unsubscribe_doc', { 
          doctype: key.split(':')[0], 
          name: key.split(':')[1] 
        })
      }
    }
  }
}

function manageSubscriptions() {
  // Sort subscriptions by priority
  const sortedSubs = Array.from(subscriptionQueue.entries())
    .sort(([, priorityA], [, priorityB]) => priorityB - priorityA)
  
  // Unsubscribe from lowest priority items
  while (subscriptions.size >= MAX_SUBSCRIPTIONS) {
    const [key] = sortedSubs.pop()
    if (subscriptions.has(key)) {
      const [doctype, name] = key.split(':')
      socket.emit('unsubscribe_doc', { doctype, name })
      subscriptions.delete(key)
      subscriptionQueue.delete(key)
    }
  }
}

// Update priorities based on viewport
export function updateSubscriptionPriorities(visibleDocs, adjacentDocs) {
  // Reset all priorities to background
  for (const [key] of subscriptionQueue) {
    subscriptionQueue.set(key, PRIORITY.BACKGROUND)
  }
  
  // Update priorities for visible docs
  visibleDocs.forEach(({ doctype, name }) => {
    const key = `${doctype}:${name}`
    subscriptionQueue.set(key, PRIORITY.VIEWPORT)
  })
  
  // Update priorities for adjacent docs
  adjacentDocs.forEach(({ doctype, name }) => {
    const key = `${doctype}:${name}`
    if (subscriptionQueue.get(key) !== PRIORITY.VIEWPORT) {
      subscriptionQueue.set(key, PRIORITY.ADJACENT)
    }
  })
  
  // Manage subscriptions after priority updates
  manageSubscriptions()
}

