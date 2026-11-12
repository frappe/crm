import { dialog, toast } from "frappe-ui";
import { reactive } from "vue";
import { __ } from "frappe/i18n";
import { call, recordNames } from "../formsApi";

// Per Link target doctype: its record names (preview and hidden-field dropdowns) and
// whether a guest can select it (the Link-field warning on the canvas and in the panel).
export function useLinkMeta() {
	// cache of Link option lists (e.g. CRM Lead Status names)
	const linkOptions = reactive({});
	const guestSelect = reactive({});
	const grantingSelect = reactive({});
	const grantRefused = reactive({});
	let grantConfirmOpen = false;

	// resolve both the preview options and the guest-access state for a Link target
	function ensureLinkMeta(doctype) {
		ensureLinkOptions(doctype);
		ensureGuestSelect(doctype);
	}

	// the grant is site-wide, not scoped to this form, so the author confirms it by name
	function grantGuestSelect(doctype) {
		if (!doctype || grantRefused[doctype] || grantingSelect[doctype] || grantConfirmOpen) return;
		grantConfirmOpen = true;
		dialog.confirm({
			title: __("Give Guest access to {0}?", [doctype]),
			message: __(
				"Guest gets the Select permission on {0} for the whole site. Anyone, signed in or not, can then search and list all {0} records with their names, titles and owners, not only through this form.",
				[doctype]
			),
			confirmLabel: __("Grant"),
			cancelLabel: __("Cancel"),
			onConfirm: () => {
				grantConfirmOpen = false;
				return grantGuestSelectNow(doctype);
			},
			onCancel: () => (grantConfirmOpen = false),
		});
	}

	async function ensureLinkOptions(doctype) {
		if (!doctype || linkOptions[doctype]) return;
		linkOptions[doctype] = [];
		try {
			linkOptions[doctype] = await recordNames(doctype);
		} catch {
			linkOptions[doctype] = [];
		}
	}

	// fail-open on error so a failed check doesn't nag
	async function ensureGuestSelect(doctype) {
		if (!doctype || doctype in guestSelect) return;
		guestSelect[doctype] = true;
		try {
			const res = await call("link_field_guest_access", { doctype });
			guestSelect[doctype] = !!res?.guest_can_select;
			grantRefused[doctype] = !!res?.grant_refused;
		} catch {
			guestSelect[doctype] = true;
		}
	}

	async function grantGuestSelectNow(doctype) {
		grantingSelect[doctype] = true;
		try {
			const res = await call("grant_guest_link_access", { doctype });
			guestSelect[doctype] = !!res?.guest_can_select;
			if (guestSelect[doctype]) {
				// records are now guest-visible — refresh the preview dropdown
				delete linkOptions[doctype];
				ensureLinkOptions(doctype);
				toast.success(__("Guests can now select {0} records.", [doctype]));
			}
		} catch (e) {
			toast.error(e?.messages?.[0] || __("Could not grant guest access."));
		} finally {
			grantingSelect[doctype] = false;
		}
	}

	return {
		linkOptions,
		guestSelect,
		grantingSelect,
		grantRefused,
		ensureLinkMeta,
		ensureLinkOptions,
		grantGuestSelect,
	};
}
