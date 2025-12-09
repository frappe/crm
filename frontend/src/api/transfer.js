import { call } from "frappe-ui"
import { toast } from "frappe-ui"

/**
 * Get communications for transfer
 * @param {string} doctype - Document type (e.g., "CRM Lead")
 * @param {string} name - Document name
 * @returns {Promise<Array>} Array of communication records
 */
export async function getCommunicationsForTransfer(doctype, name) {
	try {
		const result = await call("crm.api.email_transfer.get_communications_for_transfer", {
			doctype,
			name,
		})
		return result || []
	} catch (error) {
		console.error("Error fetching communications:", error)
		toast.error(error.messages?.[0] || "Error fetching communications")
		throw error
	}
}

/**
 * Transfer CRM Lead to HD Ticket
 * @param {string} leadName - Lead document name
 * @param {Array<string>} communicationIds - Array of communication IDs to transfer
 * @param {boolean} deleteSource - Whether to delete source lead (default: true)
 * @returns {Promise<Object>} Transfer result with ticket_name, ticket_url, etc.
 */
export async function transferToHelpdesk(leadName, communicationIds = [], deleteSource = true) {
	try {
		const result = await call("crm.api.email_transfer.transfer_to_helpdesk", {
			lead_name: leadName,
			communication_ids: communicationIds,
			delete_source: deleteSource,
		})
		
		if (result.success) {
			toast.success(result.message || "Successfully transferred to HD Ticket")
			return result
		} else {
			throw new Error(result.message || "Transfer failed")
		}
	} catch (error) {
		console.error("Error transferring to helpdesk:", error)
		toast.error(error.messages?.[0] || error.message || "Error transferring to helpdesk")
		throw error
	}
}

