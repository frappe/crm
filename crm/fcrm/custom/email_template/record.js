import { startCopyDisabled } from '../../frontend/email/index.js'

export default {
	onOpen: (page) => startCopyDisabled(page),
}
