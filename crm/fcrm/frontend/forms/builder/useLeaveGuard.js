import { dialog } from "frappe-ui";
import { onBeforeUnmount } from "vue";
import { __ } from "frappe/i18n";

// Back, the browser's back and any other link leave through the router, so the guard asks once.
export function useLeaveGuard(router, dirty) {
	const stopLeaveGuard = router?.beforeEach((to, from) =>
		!dirty.value || sameForm(to, from) ? true : confirmDiscard()
	);
	function blockUnload(event) {
		if (!dirty.value) return;
		event.preventDefault();
		event.returnValue = "";
	}
	window.addEventListener("beforeunload", blockUnload);
	onBeforeUnmount(() => {
		stopLeaveGuard?.();
		window.removeEventListener("beforeunload", blockUnload);
	});
}

function sameForm(to, from) {
	return to.path === from.path && to.query.form === from.query.form;
}

function confirmDiscard() {
	return new Promise((resolve) =>
		dialog.confirm({
			title: __("Discard unsaved changes?"),
			message: __("This form has changes that are not saved."),
			confirmLabel: __("Discard"),
			cancelLabel: __("Keep editing"),
			onConfirm: () => resolve(true),
			onCancel: () => resolve(false),
		})
	);
}
