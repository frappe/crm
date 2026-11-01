import { appendToLead, startNewAccount } from '../../frontend/email/index.js'

export default {
	onOpen: (page) => startNewAccount(page),
	service: (page) => appendToLead(page),
	use_imap: (page) => appendToLead(page),
}
