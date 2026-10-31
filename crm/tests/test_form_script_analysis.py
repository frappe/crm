import re
from pathlib import Path

from frappe.tests import IntegrationTestCase

from crm.fcrm.doctype.crm_products.crm_products import get_product_details_script
from crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings import get_crm_form_script
from crm.fcrm.doctype.fcrm_settings.fcrm_settings import get_forecasting_script
from crm.fcrm.form_script_analysis import CATALOG, analyse

FIXTURES = Path(__file__).parent / "form_scripts"
FIXTURE_SHAPES = {
	"class_crm_deal.js": ("CRM Deal", "Form", "Class-based"),
	"setup_form_crm_lead.js": ("CRM Lead", "Form", "setupForm"),
	"setup_list_crm_lead.js": ("CRM Lead", "List", "setupList"),
}
HITS_COMMENT = re.compile(r"// hits: (.*)$")

# The guide links each key as an anchor: a renamed key breaks every link to it.
CATALOG_KEYS = (
	"child-class translate on-load on-render on-validate on-save on-error on-before-create on-create-lead "
	"convert-to-deal field-handler this-value this-old-value child-field-handler current-row-idx row-add "
	"row-remove remaining-rows removed-rows button-field-method doc-trigger this-method-call get-row "
	"row-trigger header-actions action-group action-on-click statuses set-field-property field-props "
	"section-property panel-section-property tab-property child-column-property row-property "
	"set-field-properties remove-field-property get-field set-field-html get-meta tabs call toast-success "
	"toast-error toast-info toast-warning toast-create toast-callable create-dialog create-dialog-html "
	"form-dialog router router-previous-route socket throw-error make-phone-call open-settings h-helper "
	"new-document legacy-doc update-field delete-doc list-actions list-bulk-actions dom-access "
	"frappe-global unread-handler unread-return-key"
).split()

STANDARD_SCRIPTS = {
	"Product Details Script for CRM Deal": (
		get_product_details_script("CRM Deal"),
		"CRM Deal",
		{
			"child-class",
			"row-add",
			"row-remove",
			"child-field-handler",
			"get-row",
			"row-trigger",
			"doc-trigger",
			"call",
		},
	),
	"Product Details Script for CRM Lead": (
		get_product_details_script("CRM Lead"),
		"CRM Lead",
		{
			"child-class",
			"row-add",
			"row-remove",
			"child-field-handler",
			"get-row",
			"row-trigger",
			"doc-trigger",
			"call",
		},
	),
	"Forecasting Script": (get_forecasting_script(), "CRM Deal", {"field-handler", "doc-trigger", "call"}),
	"Create Quotation from CRM Deal": (
		get_crm_form_script(),
		"CRM Deal",
		{
			"on-load",
			"new-document",
			"call",
			"doc-trigger",
			"header-actions",
			"translate",
			"action-on-click",
			"toast-error",
		},
	),
}

DEAL = ("CRM Deal", "Form")
LEAD_FORM = ("CRM Lead", "Form")
# One script per catalog entry with no counterpart: (doctype, view, script).
NO_COUNTERPART = {
	"on-error": (*DEAL, "class CRMDeal { onError() {} }"),
	"on-before-create": (*DEAL, "class CRMDeal { on_before_create() {} }"),
	"on-create-lead": (*LEAD_FORM, "class CRMLead { onCreateLead() {} }"),
	"convert-to-deal": (*LEAD_FORM, "class CRMLead { convert_to_deal() {} }"),
	"this-old-value": (*DEAL, "class CRMDeal { status() { if (this.oldValue) return } }"),
	"removed-rows": (
		*DEAL,
		"class CRMDeal {}\nclass CRMProducts { products_remove() { this.selectedRows } }",
	),
	"button-field-method": ("CRM Holiday List", "Form", "class CRMHolidayList { add_to_holidays() {} }"),
	"statuses": (*DEAL, "class CRMDeal { onLoad() { this.statuses = [] } }"),
	"child-column-property": (
		*DEAL,
		"class CRMDeal { onRender() { this.setFieldProperty('products.rate', 'read_only', 1) } }",
	),
	"row-property": (
		*DEAL,
		"class CRMDeal { onRender() { this.setFieldProperty('products', 'hidden', 1, 'row-1') } }",
	),
	"toast-info": (*DEAL, "class CRMDeal { onLoad() { toast.info('Hi') } }"),
	"toast-warning": (*DEAL, "class CRMDeal { onLoad() { this.toast.warning('Hi') } }"),
	"toast-create": (*LEAD_FORM, "function setupForm({ createToast }) { createToast({ title: 'Hi' }) }"),
	"toast-callable": (*DEAL, "class CRMDeal { onLoad() { toast('Hi') } }"),
	"router-previous-route": (*DEAL, "class CRMDeal { onLoad() { router.previousRoute } }"),
	"socket": (*LEAD_FORM, "function setupForm({ $socket }) { $socket.on('x', () => {}) }"),
	"make-phone-call": (*DEAL, "class CRMDeal { onLoad() { crm.makePhoneCall(this.doc.mobile_no) } }"),
	"dom-access": (*LEAD_FORM, "function setupForm() { document.querySelector('.x').remove() }"),
	"frappe-global": (*DEAL, "frappe.ui.form.on('CRM Deal', { refresh() {} })"),
	"unread-handler": (*DEAL, "class CRMDeal { afterSubmit() {} }"),
	"unread-return-key": (*LEAD_FORM, "function setupForm({ doc }) { return { sections: [] } }"),
}


class TestFormScriptAnalysis(IntegrationTestCase):
	def test_catalog_keys_do_not_change(self):
		self.assertEqual(list(CATALOG), CATALOG_KEYS)

	def test_each_fixture_has_its_shape_and_the_commented_hits(self):
		for name, (doctype, view, shape) in FIXTURE_SHAPES.items():
			with self.subTest(fixture=name):
				script = (FIXTURES / name).read_text()
				analysis = analyse(script, doctype, view)
				self.assertEqual(analysis.shape, shape)
				self.assertEqual(found(analysis), commented_hits(script))

	def test_fixtures_use_every_entry_with_a_counterpart(self):
		used = {key for name in FIXTURE_SHAPES for _, key in found(analyse_fixture(name))}
		with_counterpart = {key for key, entry in CATALOG.items() if entry.verb}
		self.assertEqual(with_counterpart - used, set())

	def test_standard_scripts_fit_page_verbs(self):
		for name, (script, doctype, keys) in STANDARD_SCRIPTS.items():
			with self.subTest(script=name):
				analysis = analyse(script, doctype, "Form")
				self.assertEqual(analysis.shape, "Class-based")
				self.assertEqual({hit.key for hit in analysis.hits}, keys)
				self.assertTrue(all(hit.verb for hit in analysis.hits))

	def test_product_details_lines(self):
		script = get_product_details_script("CRM Deal")
		lines = script.splitlines()
		for hit in analyse(script, "CRM Deal", "Form").hits:
			self.assertIn(hit.call.split(".")[-1].rstrip("()"), lines[hit.line - 1])

	def test_entries_with_no_counterpart(self):
		for key, (doctype, view, script) in NO_COUNTERPART.items():
			with self.subTest(key=key):
				hits = [hit for hit in analyse(script, doctype, view).hits if hit.key == key]
				self.assertEqual(len(hits), 1)
				self.assertIsNone(hits[0].verb)
				self.assertEqual(hits[0].gap, CATALOG[key].gap)
				self.assertTrue(hits[0].gap)

	def test_every_catalog_entry_has_a_test_hit(self):
		hit = {key for name in FIXTURE_SHAPES for _, key in found(analyse_fixture(name))}
		hit |= set(NO_COUNTERPART)
		self.assertEqual(set(CATALOG) - hit, set())

	def test_toast_gaps_link_the_page_toast_issue(self):
		for key in ("toast-info", "toast-warning", "toast-create", "toast-callable"):
			self.assertEqual(CATALOG[key].gap, "https://github.com/frappe/frappe/issues/46005")

	def test_lifecycle_aliases(self):
		script = "class CRMDeal {\n on_load() {}\n onload() {}\n refresh() {}\n on_render() {}\n validate() {}\n on_save() {}\n}"
		hits = [(hit.call, hit.key) for hit in analyse(script, "CRM Deal", "Form").hits]
		self.assertEqual(
			hits,
			[
				("on_load()", "on-load"),
				("onload()", "on-load"),
				("refresh()", "on-render"),
				("on_render()", "on-render"),
				("validate()", "on-validate"),
				("on_save()", "on-save"),
			],
		)

	def test_shapes(self):
		cases = [
			("class CRMDeal {}", "Form", "Class-based"),
			("class CRMProducts { qty() {} }", "Form", "Class-based"),
			("function setupForm({ doc }) { return {} }", "Form", "setupForm"),
			("function setupList({ list }) { return {} }", "Form", "Unknown"),
			("function setupForm({ doc }) { return {} }", "List", "Unknown"),
			("class CRMDeal {}", "List", "Unknown"),
			("frappe.ui.form.on('CRM Deal', {})", "Form", "Unknown"),
			("// class CRMDeal {}\nconst s = 'setupForm('", "Form", "Unknown"),
			("", "Form", "Unknown"),
		]
		for script, view, shape in cases:
			with self.subTest(script=script, view=view):
				self.assertEqual(analyse(script, "CRM Deal", view).shape, shape)
		self.assertEqual(analyse(None, "CRM Deal", "Form"), analyse("", "CRM Deal", "Form"))

	def test_comments_strings_and_regexes_are_not_calls(self):
		script = """class CRMDeal {
  onLoad() {
    // toast.info('a')
    /* call('b') */
    const text = "toast.info('c')" + 'frappe.d' + `call(${'e'})`
    const pattern = /document\\.f/g
  }
}"""
		self.assertEqual(found(analyse(script, "CRM Deal", "Form")), {(2, "on-load")})

	def test_template_expressions_are_code(self):
		script = "class CRMDeal { onLoad() { const a = `x ${toast.info(`y ${call('z')}`)} w` } }"
		keys = {hit.key for hit in analyse(script, "CRM Deal", "Form").hits}
		self.assertEqual(keys, {"on-load", "toast-info", "call"})

	def test_setup_form_with_an_object_parameter(self):
		script = "function setupForm(obj) {\n  obj.call('x')\n  return { actions: [], statuses: obj.doc.statuses }\n}"
		self.assertEqual(
			found(analyse(script, "CRM Lead", "Form")),
			{(2, "call"), (3, "header-actions"), (3, "statuses"), (3, "legacy-doc")},
		)

	def test_a_nested_function_return_is_not_the_setup_return(self):
		script = "function setupForm({ doc }) {\n  const fields = () => { return { label: 1 } }\n  return { actions: [] }\n}"
		self.assertEqual(
			found(analyse(script, "CRM Lead", "Form")), {(1, "legacy-doc"), (3, "header-actions")}
		)

	def test_a_method_called_from_the_script_is_a_helper_not_a_handler(self):
		script = "class CRMDeal {\n  onLoad() { this.setup() }\n  setup() {}\n}"
		self.assertEqual(
			found(analyse(script, "CRM Deal", "Form")), {(2, "on-load"), (2, "this-method-call")}
		)

	def test_onclick_inside_a_dialog_is_not_a_header_action(self):
		script = "class CRMDeal { onLoad() { createDialog({ actions: [{ group: 1, onClick: () => {} }] }) } }"
		keys = {hit.key for hit in analyse(script, "CRM Deal", "Form").hits}
		self.assertEqual(keys, {"on-load", "create-dialog"})


def analyse_fixture(name):
	doctype, view, _ = FIXTURE_SHAPES[name]
	return analyse((FIXTURES / name).read_text(), doctype, view)


def found(analysis):
	return {(hit.line, hit.key) for hit in analysis.hits}


def commented_hits(script):
	expected = set()
	for line, text in enumerate(script.splitlines(), 1):
		comment = HITS_COMMENT.search(text)
		if comment:
			expected.update((line, key.strip()) for key in comment.group(1).split(","))
	return expected
