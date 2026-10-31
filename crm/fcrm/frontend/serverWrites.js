// The server writes a CRM section runs on the saved record, kept free of the desk's imports so it is unit-tested.
import { ref } from 'vue'
import { saveRecord } from './saveRecord.js'

/** Runs whitelisted methods that change the saved record, one at a time; each resolves true once it is done. */
export class ServerWrites {
	constructor(page, staleMessage) {
		this.page = page
		this.staleMessage = staleMessage
		this.busy = ref(false)
		this.stale = false
	}

	async run(method, args, done) {
		if (this.busy.value) return false
		if (this.stale) {
			this.page.toast.error(this.staleMessage)
			return false
		}
		this.busy.value = true
		try {
			return await this.#write(method, args, done)
		} finally {
			this.busy.value = false
		}
	}

	async #write(method, args, done) {
		// The server saves the record: a draft goes first, and the re-read keeps the next save from conflicting.
		if (!(await saveRecord(this.page))) return false
		try {
			await this.page.call(method, args)
		} catch (error) {
			this.page.toast.error(error?.message || String(error))
			return false
		}
		// Edits typed during the call sit on the old copy: a re-read would drop them, a save conflicts.
		if (this.page.isDirty) {
			this.stale = true
			this.page.toast.error(this.staleMessage)
			return true
		}
		await this.page.reload()
		this.page.toast.success(done)
		return true
	}
}
