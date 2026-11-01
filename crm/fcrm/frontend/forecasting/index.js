// Forecasting on CRM Deal's record page: a status change sets the deal's probability while FCRM Settings has it on
// and the v1 "Forecasting Script" row is enabled.
import { listDocuments } from '@framework/ui/api'
import { standardScriptEnabled } from '../form_script/standardScript.js'
import { forecastProbability as forecastAfter, forecastOnSave, readForecasting } from './forecasting.js'

const READS = { probabilities: readProbabilities, scriptEnabled: standardScriptEnabled }

export function addForecasting(page) {
	readForecasting(page, READS)
}

/** The `status` handler: `handler`'s job first, then the picked status's probability. */
export function forecastProbability(handler) {
	return forecastAfter(handler, READS)
}

/** The `beforeSave` handler: a header status pick sets the deal's probability as a form edit does. */
export const forecastStatusOnSave = forecastOnSave(READS)

function readProbabilities() {
	return listDocuments('CRM Deal Status', { fields: ['name', 'probability'], limit: 100 }).then((reply) =>
		Object.fromEntries(reply.data.map((status) => [status.name, status.probability ?? 0])),
	)
}
