import {
	appendToLead,
	fillNewAccount,
	startNewAccount,
} from '../../frontend/email/index.js'

export default {
	onOpen: (page) => startNewAccount(page),
	beforeSave: (page) => fillNewAccount(page),
	service: (page) => appendToLead(page),
	use_imap: (page) => appendToLead(page),
}
