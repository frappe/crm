export function filterEmailActivities(activity) {
  return activity.activity_type === 'communication' && 
         activity.communication_medium !== 'Phone' && 
         activity.communication_medium !== 'Chat'
}

// Add other filter functions as needed 