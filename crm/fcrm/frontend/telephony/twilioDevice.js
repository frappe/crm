// The one place that picks the Twilio `Device`. `loadVoiceSdk` is `() => import('@twilio/voice-sdk')`, so the real chunk loads only for a real device.

/** The `Device` class for a `generate_access_token` answer: the fake one when the server says mock mode, else the SDK's. */
export async function loadTwilioDevice(tokenData, loadVoiceSdk) {
	if (tokenData?.mock) {
		const { MockDevice } = await import('./mockTwilioDevice.js')
		return MockDevice
	}
	return (await loadVoiceSdk()).Device
}
