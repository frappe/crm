import { splitPhoneDetails } from '@framework/ui'

// "+14155550123" as "+1 415 555 0123"; a short number is grouped by its last four digits.
export function formatPhone(value) {
	if (!value) return ''
	const { country, number } = splitPhoneDetails(value.replace(/[\s().]/g, ''))
	const digits = number.replace(/\D/g, '')
	const grouped =
		digits.length === 10
			? [digits.slice(0, 3), digits.slice(3, 6), digits.slice(6)]
			: digits.length > 4
			? [digits.slice(0, -4), digits.slice(-4)]
			: [digits]
	return [country?.isd, ...grouped].filter(Boolean).join(' ')
}

function parts(seconds) {
	const s = Math.max(0, Math.round(seconds || 0))
	return [Math.floor(s / 3600), Math.floor((s % 3600) / 60), s % 60]
}

// A player's time, "12:34" or "1:02:03".
export function clock(seconds) {
	const [h, m, s] = parts(seconds)
	const pad = (n) => String(n).padStart(2, '0')
	return h ? `${h}:${pad(m)}:${pad(s)}` : `${m}:${pad(s)}`
}

// A length in words, "12m 34s", so it does not read as a time of day.
export function spoken(seconds) {
	const [h, m, s] = parts(seconds)
	return h ? `${h}h ${m}m` : m ? `${m}m ${s}s` : `${s}s`
}
