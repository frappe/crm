import { dialog, toast } from "frappe-ui";
import { __ } from "frappe/i18n";
import { call, errorText } from "../formsApi";
import { BREAK_TYPES } from "./formModel";

export const targetOptions = [
	{ label: "Lead", value: "CRM Lead" },
	{ label: "Deal", value: "CRM Deal" },
];
export const docLabel = (dt) => targetOptions.find((o) => o.value === dt)?.label || dt;

// Changing the form's target doctype: fetch the new field catalog, confirm what
// would be lost, then rebuild the form and its hidden fields for the new doctype.
export function useDoctypeSwitch({
	form,
	hiddenFields,
	availableFields,
	linkMeta,
	setHiddenFields,
	rebuildModel,
	markDirty,
}) {
	const { ensureLinkMeta } = linkMeta;

	function hiddenDefaultsLost(seed) {
		const next = new Map((seed || []).map((h) => [h.fieldname, String(h.default ?? "")]));
		return hiddenFields.value.some(
			(h) => String(h.default ?? "") !== (next.get(h.fieldname) ?? "")
		);
	}

	async function requestDoctypeChange(newDt) {
		if (!newDt || newDt === form.document_type) return;
		let fields, seed;
		try {
			// fetch both before touching the form, so a failure leaves it unchanged
			[fields, seed] = await Promise.all([
				call("get_form_fields", { document_type: newDt }),
				call("get_hidden_seed", { document_type: newDt }),
			]);
		} catch (e) {
			toast.error(errorText(e, __("Could not change the form type")));
			return;
		}
		const valid = new Set((fields || []).map((f) => f.fieldname));
		const wouldDrop = form.fields.filter(
			(f) => !BREAK_TYPES.includes(f.fieldtype) && !valid.has(f.fieldname)
		).length;
		const losses = [];
		if (wouldDrop)
			losses.push(
				__("Switching to {0} will remove {1} field(s) that don't exist on {0}.", [
					docLabel(newDt),
					wouldDrop,
				])
			);
		if (hiddenDefaultsLost(seed))
			losses.push(
				__("The hidden fields' default values are reset to those of {0}.", [docLabel(newDt)])
			);

		if (!losses.length) {
			commitDoctype(newDt, valid, seed);
			return;
		}
		dialog.confirm({
			title: __("Change form type?"),
			message: [...losses, __("This can't be undone.")].join(" "),
			confirmLabel: wouldDrop ? __("Change & remove fields") : __("Change form type"),
			theme: "red",
			onConfirm: () => commitDoctype(newDt, valid, seed),
		});
	}

	async function commitDoctype(newDt, valid, seed) {
		form.document_type = newDt;
		await availableFields.reload();
		const before = form.fields.length;
		form.fields = form.fields.filter(
			(f) => BREAK_TYPES.includes(f.fieldtype) || valid.has(f.fieldname)
		);
		const dropped = before - form.fields.length;
		// reconcile the fields we kept against the new doctype's real definitions:
		// pick up its options and enforce its mandatory flags
		const catalog = new Map((availableFields.data || []).map((f) => [f.fieldname, f]));
		form.fields.forEach((f) => {
			const c = catalog.get(f.fieldname);
			if (!c) return;
			f.options = c.options;
			if (c.reqd) f.reqd = true;
			if (f.fieldtype === "Link") ensureLinkMeta(f.options);
		});
		// rebuild hidden fields for the new doctype: its system-hidden fields (Status,
		// with the right options + default)
		setHiddenFields(seed);
		rebuildModel();
		markDirty();
		if (dropped) {
			toast.info(__("{0} field(s) removed. Not available on {1}.", [dropped, docLabel(newDt)]));
		}
	}

	return { requestDoctypeChange };
}
