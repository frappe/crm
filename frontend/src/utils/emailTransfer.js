/**
 * Utility functions for email transfer functionality
 */

/**
 * Format email content preview by stripping HTML tags and getting first N characters
 * @param {string} content - HTML content
 * @param {number} maxLength - Maximum length (default: 100)
 * @returns {string} Plain text preview
 */
export function formatEmailPreview(content, maxLength = 100) {
	if (!content) return ""
	
	// Strip HTML tags
	const tempDiv = document.createElement("div")
	tempDiv.innerHTML = content
	const text = tempDiv.textContent || tempDiv.innerText || ""
	
	// Get first N characters
	if (text.length <= maxLength) {
		return text.trim()
	}
	
	return text.substring(0, maxLength).trim() + "..."
}

/**
 * Format date string for display
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date string
 */
export function formatDate(dateString) {
	if (!dateString) return ""
	
	const date = new Date(dateString)
	const now = new Date()
	const diffMs = now - date
	const diffMins = Math.floor(diffMs / 60000)
	const diffHours = Math.floor(diffMs / 3600000)
	const diffDays = Math.floor(diffMs / 86400000)
	
	if (diffMins < 1) {
		return "Just now"
	} else if (diffMins < 60) {
		return `${diffMins} minute${diffMins > 1 ? "s" : ""} ago`
	} else if (diffHours < 24) {
		return `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`
	} else if (diffDays < 7) {
		return `${diffDays} day${diffDays > 1 ? "s" : ""} ago`
	} else {
		// Format as date
		return date.toLocaleDateString(undefined, {
			year: "numeric",
			month: "short",
			day: "numeric",
		})
	}
}

