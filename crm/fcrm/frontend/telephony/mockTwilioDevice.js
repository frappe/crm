// A fake `@twilio/voice-sdk` Device and Call: the same methods and events the CRM's call code uses, none of the media.
// A test or walk drives it through `window.__crmTelephonyMock.twilio` (the newest device).

class Emitter {
	#listeners = {}

	on(event, listener) {
		;(this.#listeners[event] ||= []).push(listener)
		return this
	}

	off(event, listener) {
		this.#listeners[event] = (this.#listeners[event] || []).filter((l) => l !== listener)
		return this
	}

	emit(event, ...args) {
		for (const listener of [...(this.#listeners[event] || [])]) listener(...args)
	}
}

export class MockCall extends Emitter {
	constructor(parameters = {}) {
		super()
		this.parameters = parameters
		this.muted = false
		this.state = 'pending'
	}

	accept() {
		this.state = 'open'
		this.emit('accept', this)
	}

	reject() {
		this.state = 'closed'
		this.emit('reject')
	}

	disconnect() {
		this.state = 'closed'
		this.emit('disconnect', this)
	}

	mute(shouldMute = true) {
		this.muted = shouldMute
		this.emit('mute', shouldMute, this)
	}

	isMuted() {
		return this.muted
	}

	status() {
		return this.state
	}

	// The test's side of the line.
	answer() {
		this.emit('messageReceived', { content: { CallStatus: 'in-progress' } })
	}

	cancel() {
		this.state = 'closed'
		this.emit('cancel')
	}

	remoteHangUp() {
		this.disconnect()
	}
}

export class MockDevice extends Emitter {
	constructor(token, options = {}) {
		super()
		this.token = token
		this.options = options
		this.state = 'unregistered'
		this.calls = []
		if (typeof window !== 'undefined') {
			window.__crmTelephonyMock = { ...window.__crmTelephonyMock, twilio: this }
		}
	}

	async register() {
		this.state = 'registered'
		this.emit('registered')
	}

	async unregister() {
		this.state = 'unregistered'
		this.emit('unregistered')
	}

	updateToken(token) {
		this.token = token
	}

	destroy() {
		this.state = 'destroyed'
		this.emit('unregistered')
	}

	async connect({ params = {} } = {}) {
		const call = new MockCall({ ...params, CallSid: `mock-tw-out-${this.calls.length + 1}` })
		this.calls.push(call)
		setTimeout(() => call.accept(), 0)
		return call
	}

	// Rings the device the way Twilio does for an incoming call, and returns the call.
	ring({ from = '+15550100101', to = '+15550100001', callSid } = {}) {
		const call = new MockCall({
			From: from,
			To: to,
			CallSid: callSid || `mock-tw-in-${this.calls.length + 1}`,
		})
		this.calls.push(call)
		this.emit('incoming', call)
		return call
	}
}
