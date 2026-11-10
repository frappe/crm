import { listDocuments, runMethod } from "@framework/ui/api";
import { toast } from "frappe-ui";
import { __ } from "frappe/i18n";

const NO_RESULT = ["set_published", "delete_form"];

/** Calls a `crm.api.form` method and returns its value. */
export async function call(method, args = {}) {
	const read = method.startsWith("list_") || method.startsWith("get_");
	const { data } = await runMethod(`crm.api.form.${method}`, args, {
		http: read ? "GET" : "POST",
		nullable: NO_RESULT.includes(method),
	});
	return data;
}

export async function recordNames(doctype) {
	const { data } = await listDocuments(doctype, {
		fields: ["name"],
		order_by: "name asc",
		limit: 500,
	});
	return data.map((row) => row.name);
}

export function errorText(error, fallback) {
	return error?.messages?.[0] || error?.message || fallback;
}

export async function copyToClipboard(text) {
	try {
		await navigator.clipboard.writeText(text);
		toast.success(__("Copied to clipboard"));
	} catch {
		toast.error(__("Could not copy to the clipboard"));
	}
}
