from dataclasses import dataclass

TOAST_GAP = "https://github.com/frappe/frappe/issues/46005"
LIST_GAP = "G6, the list beyond columns (map 4 of frappe/frappe#45839)"
NO_CRM_HOOK = "No CRM hook: no public script uses it (frappe/frappe#45963 ruling 12)"


@dataclass(frozen=True)
class Entry:
	"""One v1 call. `key` is the anchor of its section in docs/form-scripts-on-desk-v2.md: never rename it."""

	key: str
	call: str
	verb: str | None
	gap: str | None = None


def _catalog(*entries: Entry) -> dict[str, Entry]:
	return {entry.key: entry for entry in entries}


CATALOG = _catalog(
	# Shape
	Entry("child-class", "class CRMProducts { ... }", "<table>: { ... } under the parent's export"),
	Entry("translate", "__()", "import { __ } from 'frappe/i18n'"),
	# Lifecycle handlers, with their aliases
	Entry("on-load", "onLoad() (on_load, onload)", "onOpen(page)"),
	Entry("on-render", "onRender() (on_render, refresh)", "onRefresh(page)"),
	Entry("on-validate", "onValidate() (on_validate, validate)", "beforeSave(page)"),
	Entry("on-save", "onSave() (on_save)", "afterSave(page)"),
	Entry("on-error", "onError() (on_error)", None, "No handler runs on a failed save"),
	Entry(
		"on-before-create",
		"onBeforeCreate() (on_before_create)",
		None,
		"The create dialog runs no handlers; on the full-page new record use beforeSave with page.isNew",
	),
	Entry("on-create-lead", "onCreateLead() (on_create_lead)", None, NO_CRM_HOOK),
	Entry("convert-to-deal", "convertToDeal() (convert_to_deal)", None, NO_CRM_HOOK),
	# Field and row handlers
	Entry(
		"field-handler", "A method named like a field: status()", "A key named like the field: status(page)"
	),
	Entry("this-value", "this.value", "page.doc.<field>"),
	Entry(
		"this-old-value",
		"this.oldValue",
		None,
		"No value before the edit: page.saved.<field> is the last saved value",
	),
	Entry("child-field-handler", "A child class method: qty()", "<table>: { qty(page, row) {} }"),
	Entry("current-row-idx", "this.currentRowIdx", "The row argument"),
	Entry("row-add", "<table>_add()", "<table>: { onAdd(page, row) {} }"),
	Entry("row-remove", "<table>_remove()", "<table>: { onRemove(page) {} }"),
	Entry("remaining-rows", "this.rows in <table>_remove()", "page.rows(table)"),
	Entry("removed-rows", "this.selectedRows in <table>_remove()", None, "onRemove gets no removed rows"),
	Entry(
		"button-field-method",
		"A method named like a Button field",
		None,
		"The record page makes no Button field clickable; page.fields.update(name, { component }) swaps the control",
	),
	# Helpers on `this`
	Entry("doc-trigger", "this.doc.trigger('method')", "A plain function in the module"),
	Entry("this-method-call", "this.<method>()", "A plain function in the module"),
	Entry(
		"get-row", "this.doc.getRow(table, idx), this.getRow(...)", "page.rows(table), or the row argument"
	),
	Entry("row-trigger", "row.trigger('field')", "row.trigger('field')"),
	Entry(
		"header-actions", "this.actions, legacy return { actions }", "page.header.add({ name, label, run })"
	),
	Entry(
		"action-group",
		"An action group: { group, items }, buttonLabel",
		"page.header.add({ name, label, display: 'dropdown' }), then members with group",
	),
	Entry("action-on-click", "onClick(close) on an action", "run(page, value)"),
	Entry(
		"statuses",
		"this.statuses, legacy return { statuses }",
		None,
		NO_CRM_HOOK + "; page.fields.update('status', { link_filters }) narrows the Link search only",
	),
	Entry(
		"set-field-property",
		"this.setFieldProperty(field, prop, value)",
		"page.fields.update(field, { [prop]: value })",
	),
	Entry("field-props", "setFieldProperty with button_color", "page.fields.update(field, { props })"),
	Entry(
		"section-property",
		"setFieldProperty on a Details section",
		"page.form.hide, show, update(name, { label })",
	),
	Entry(
		"panel-section-property",
		"setFieldProperty on a Side Panel section",
		"page.panelSections.hide, show, update(name, { label, opened }), open, close",
	),
	Entry("tab-property", "setFieldProperty on a tab", "page.form.tabs.hide, show, update(name, { label })"),
	Entry(
		"child-column-property",
		"setFieldProperty('table.column', ...)",
		None,
		"page.fields reaches only the parent's own fields",
	),
	Entry("row-property", "setFieldProperty(..., rowName)", None, "Only errors are per row: row.setError"),
	Entry(
		"set-field-properties", "this.setFieldProperties(field, {...})", "page.fields.update(field, {...})"
	),
	Entry("remove-field-property", "this.removeFieldProperty(...)", "State the condition in onRefresh(page)"),
	Entry("get-field", "this.getField(field)", "page.fields.get(field)"),
	Entry(
		"set-field-html", "this.setFieldHtml(field, html)", "page.fields.update(field, { component, props })"
	),
	Entry("get-meta", "this.getMeta(doctype)", "page.meta (own doctype only)"),
	Entry("tabs", "this.tabs (CRM develop)", "page.tabs.add({ name, label, component })"),
	# Injected helpers, bare or read from `this`
	Entry("call", "call(method, params)", "page.call(method, params)"),
	Entry("toast-success", "toast.success", "page.toast.success"),
	Entry("toast-error", "toast.error", "page.toast.error"),
	Entry("toast-info", "toast.info", None, TOAST_GAP),
	Entry("toast-warning", "toast.warning", None, TOAST_GAP),
	Entry("toast-create", "toast.create, legacy createToast", None, TOAST_GAP),
	Entry("toast-callable", "toast(message) (CRM develop)", None, TOAST_GAP),
	Entry(
		"create-dialog", "createDialog(options), legacy $dialog", "page.dialog.confirm, page.dialog.danger"
	),
	Entry("create-dialog-html", "createDialog({ html })", "page.dialog.open(component)"),
	Entry("form-dialog", "formDialog(options)", "page.dialog.form(options)"),
	Entry("router", "router", "page.router"),
	Entry("router-previous-route", "router.previousRoute", None, "A CRM v1 addition to the router"),
	Entry("socket", "socket, legacy $socket", None, "Scripts get no socket"),
	Entry("throw-error", "throwError(message)", "throw new Error(message) in beforeSave(page)"),
	Entry("make-phone-call", "crm.makePhoneCall(number)", None, "Map 5: the act shell.crm.make_a_call"),
	Entry("open-settings", "crm.openSettings(page)", "page.openSettings(prefix, pane, block)"),
	Entry("h-helper", "h() (CRM develop)", "import { h } from 'vue'"),
	Entry("new-document", "this.doc.__newDocument", "page.isNew"),
	# The legacy setupForm shape's own members
	Entry("legacy-doc", "doc", "page.doc"),
	Entry("update-field", "updateField(field, value)", "page.doc.<field> = value, then page.save()"),
	Entry("delete-doc", "deleteDoc()", "page.run('header.delete')"),
	# The setupList shape
	Entry("list-actions", "setupList: return { actions }", None, LIST_GAP),
	Entry("list-bulk-actions", "setupList: return { bulk_actions }", None, LIST_GAP),
	# Not a v1 call
	Entry(
		"dom-access",
		"document., querySelector, MutationObserver",
		None,
		"By design: desk v2 gives scripts surfaces and verbs, not the DOM (frappe/frappe#45963 ruling 14)",
	),
	Entry("frappe-global", "frappe.*", None, "Desk v1 API: CRM v1 has no frappe global"),
	Entry("unread-handler", "afterSubmit(), after_load() and other names", None, "CRM v1 never calls it"),
	Entry(
		"unread-return-key",
		"A returned key CRM v1 never reads: return { sections }",
		None,
		"CRM v1 reads only actions and statuses (setupList: actions and bulk_actions)",
	),
)
