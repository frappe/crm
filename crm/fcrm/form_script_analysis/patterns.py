import re

CLASS = "Class-based"
SETUP_FORM = "setupForm"
SETUP_LIST = "setupList"
UNKNOWN = "Unknown"

SCRIPTED = (CLASS, SETUP_FORM, SETUP_LIST)
ANY = (*SCRIPTED, UNKNOWN)

BARE = r"(?<![\w$.])"
INJECTED = BARE + r"(?:this\.)?"  # CRM v1 also copies every injected helper onto the class instance

LIFECYCLE = {
	"onLoad": "on-load",
	"on_load": "on-load",
	"onload": "on-load",
	"onRender": "on-render",
	"on_render": "on-render",
	"refresh": "on-render",
	"onValidate": "on-validate",
	"on_validate": "on-validate",
	"validate": "on-validate",
	"onSave": "on-save",
	"on_save": "on-save",
	"onError": "on-error",
	"on_error": "on-error",
	"onBeforeCreate": "on-before-create",
	"on_before_create": "on-before-create",
	"onCreateLead": "on-create-lead",
	"on_create_lead": "on-create-lead",
	"convertToDeal": "convert-to-deal",
	"convert_to_deal": "convert-to-deal",
}

# Desk v1 form events and look-alikes that CRM v1 never calls.
UNREAD_HANDLERS = {
	"setup",
	"onload_post_render",
	"after_load",
	"afterLoad",
	"before_save",
	"beforeSave",
	"after_save",
	"afterSave",
	"before_submit",
	"beforeSubmit",
	"on_submit",
	"onSubmit",
	"after_submit",
	"afterSubmit",
	"before_cancel",
	"after_cancel",
}

RETURN_KEYS = {
	SETUP_FORM: {"actions": "header-actions", "statuses": "statuses"},
	SETUP_LIST: {"actions": "list-actions", "bulk_actions": "list-bulk-actions"},
}


def _patterns(*rows: tuple[str, tuple[str, ...], str]) -> tuple[tuple[str, tuple[str, ...], re.Pattern], ...]:
	return tuple((key, shapes, re.compile(pattern)) for key, shapes, pattern in rows)


PATTERNS = _patterns(
	("translate", SCRIPTED, BARE + r"__\s*\("),
	("call", SCRIPTED, INJECTED + r"call\s*\("),
	("toast-success", SCRIPTED, INJECTED + r"toast\.success\b"),
	("toast-error", SCRIPTED, INJECTED + r"toast\.error\b"),
	("toast-info", SCRIPTED, INJECTED + r"toast\.info\b"),
	("toast-warning", SCRIPTED, INJECTED + r"toast\.warning\b"),
	("toast-create", SCRIPTED, INJECTED + r"toast\.create\b|" + BARE + r"createToast\b"),
	("toast-callable", SCRIPTED, INJECTED + r"toast\s*\("),
	("create-dialog", SCRIPTED, INJECTED + r"createDialog\s*\(|" + BARE + r"\$dialog\s*\("),
	("form-dialog", SCRIPTED, INJECTED + r"formDialog\s*\("),
	("router", SCRIPTED, INJECTED + r"router\.(?!previousRoute\b)"),
	("router-previous-route", SCRIPTED, INJECTED + r"router\.previousRoute\b"),
	("socket", SCRIPTED, INJECTED + r"\$?socket\s*\."),
	("throw-error", (CLASS, SETUP_FORM), INJECTED + r"throwError\s*\("),
	("make-phone-call", (CLASS,), INJECTED + r"crm\.makePhoneCall\b"),
	("open-settings", (CLASS,), INJECTED + r"crm\.openSettings\b"),
	("h-helper", (CLASS,), INJECTED + r"h\s*\("),
	("new-document", (CLASS, SETUP_FORM), r"\.__newDocument\b"),
	("update-field", (SETUP_FORM,), BARE + r"updateField\s*\("),
	("delete-doc", (SETUP_FORM,), BARE + r"deleteDoc\s*\("),
	("this-value", (CLASS,), r"\bthis\.value\b"),
	("this-old-value", (CLASS,), r"\bthis\.oldValue\b"),
	("current-row-idx", (CLASS,), r"\bthis\.currentRowIdx\b"),
	("remaining-rows", (CLASS,), r"\bthis\.rows\b"),
	("removed-rows", (CLASS,), r"\bthis\.selectedRows\b"),
	("doc-trigger", (CLASS,), r"\bthis\.doc\.trigger\s*\("),
	("row-trigger", (CLASS,), r"(?<!this\.doc)\.trigger\s*\("),
	("get-row", (CLASS,), r"\bthis\.(?:doc\.)?getRow\s*\("),
	("header-actions", (CLASS,), r"\bthis\.actions\b"),
	("statuses", (CLASS,), r"\bthis\.statuses\b"),
	("set-field-properties", (CLASS,), r"\bthis\.setFieldProperties\s*\("),
	("remove-field-property", (CLASS,), r"\bthis\.removeFieldProperty\s*\("),
	("get-field", (CLASS,), r"\bthis\.getField\s*\("),
	("set-field-html", (CLASS,), r"\bthis\.setFieldHtml\s*\("),
	("get-meta", (CLASS,), r"\bthis\.getMeta\s*\("),
	("tabs", (CLASS,), r"\bthis\.tabs\b"),
	(
		"dom-access",
		ANY,
		BARE
		+ r"(?:window\.)?document\.|\bquerySelector(?:All)?\s*\(|\bgetElements?By\w+\s*\(|\bMutationObserver\b",
	),
	("frappe-global", ANY, BARE + r"frappe\."),
)

# Keys a dialog's own options also use: inside a dialog call they are not header actions.
ACTION_PATTERNS = _patterns(
	("action-group", (CLASS, SETUP_FORM), BARE + r"(?:group|buttonLabel)\s*:"),
	("action-on-click", (CLASS, SETUP_FORM), BARE + r"onClick\s*[:(]"),
)
DIALOG_CALL = re.compile(INJECTED + r"(createDialog|formDialog)\s*\(|" + BARE + r"(\$dialog)\s*\(")
DIALOG_HTML = re.compile(BARE + r"html\s*[:,}]")

CLASS_DEFINITION = re.compile(r"\bclass\s+([A-Za-z_$][\w$]*)[^{]*\{")
METHOD_DEFINITION = re.compile(
	r"(?<![\w$.])(?:static\s+|async\s+|get\s+|set\s+|\*\s*)*([A-Za-z_$][\w$]*)\s*(?:\([^()]*\)\s*\{|=\s*(?:async\s*)?(?:\([^()]*\)|[\w$]+)\s*=>)"
)
NOT_METHODS = {"if", "for", "while", "switch", "catch", "with", "function", "return"}
THIS_CALL = re.compile(r"\bthis\.([A-Za-z_$][\w$]*)\s*\(")
TRIGGERED = re.compile(r"\.trigger\(\s*['\"]([\w$]+)")
SET_FIELD_PROPERTY = re.compile(r"\bthis\.setFieldProperty\s*(\()")
SETUP_FORM_CALL = re.compile(r"\bsetupForm\s*\(")
SETUP_LIST_NAME = re.compile(r"\bsetupList\b")
SETUP_FUNCTION = re.compile(r"\b(setupForm|setupList)\s*(?:=\s*(?:async\s*)?(?:function\s*)?)?(\()")
RETURN_OBJECT = re.compile(r"\breturn\s*(\{)")
