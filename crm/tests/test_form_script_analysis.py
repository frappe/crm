import re
import time
from pathlib import Path
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.fcrm.doctype.crm_products.crm_products import get_product_details_script
from crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings import get_crm_form_script
from crm.fcrm.doctype.fcrm_settings.fcrm_settings import get_forecasting_script
from crm.fcrm.form_script_analysis import CATALOG, analyse, scan

FIXTURES = Path(__file__).parent / "form_scripts"
FIXTURE_SHAPES = {
	"class_crm_deal.js": ("CRM Deal", "Form", "Class-based"),
	"setup_form_crm_lead.js": ("CRM Lead", "Form", "setupForm"),
	"setup_list_crm_lead.js": ("CRM Lead", "List", "setupList"),
}
HITS_COMMENT = re.compile(r"// hits: (.*)$")
READ_LAYOUT = scan._layout
# CRM Deal's default layouts (crm/install.py), so a site's own layout edits do not change the hits.
LAYOUTS = {
	("CRM Deal", "Data Fields"): [{"name": "first_tab", "sections": [{"name": "details_section"}]}],
	("CRM Deal", "Side Panel"): [{"name": "contacts_section"}, {"name": "organization_section"}],
}

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
	def setUp(self):
		layout = patch(
			"crm.fcrm.form_script_analysis.scan._layout",
			lambda doctype, layout_type: LAYOUTS.get((doctype, layout_type), []),
		)
		layout.start()
		self.addCleanup(layout.stop)

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

	def test_a_doctype_that_is_gone(self):
		for doctype in ("No Such Doctype 45966", ""):
			with self.subTest(doctype=doctype):
				analysis = analyse("class Foo {\n  onLoad() {}\n  status() {}\n}", doctype, "Form")
				self.assertEqual(found(analysis), {(1, "child-class"), (2, "unread-handler")})

	def test_row_events_reach_only_the_tables_child_class(self):
		script = "class CRMDeal {\n  products_add() {}\n}\nclass CRMProducts {\n  contacts_add() {}\n  products_remove() {}\n}"
		self.assertEqual(found(analyse(script, "CRM Deal", "Form")), {(4, "child-class"), (6, "row-remove")})

	def test_a_broken_layout(self):
		script = "class CRMDeal { onRender() { this.setFieldProperty('custom_part', 'hidden', 1) } }"
		get_value = frappe.db.get_value
		for layout in (
			"{",
			'[{"name": "t", "sections": null}]',
			'[{"sections": ["x"]}]',
			'[{"name": ["x"]}]',
			"[1]",
		):

			def read(doctype, *args, layout=layout, **kwargs):
				return layout if doctype == "CRM Fields Layout" else get_value(doctype, *args, **kwargs)

			with (
				self.subTest(layout=layout),
				patch.object(scan, "_layout", READ_LAYOUT),
				patch.object(frappe.db, "get_value", read),
			):
				keys = {hit.key for hit in analyse(script, "CRM Deal", "Form").hits}
				self.assertEqual(keys, {"on-render", "set-field-property"})

	def test_unbalanced_and_adversarial_scripts_stay_fast(self):
		cases = {
			"unclosed arrows": "function setupForm({ doc }) {\n" + "const f = () => {\n" * 5000,
			"unclosed calls": "class CRMDeal {\n onLoad() {\n" + "this.setFieldProperty(\n" * 3000,
			"deep nesting": "class CRMDeal { onLoad() {" + "{" * 3000 + "}" * 3000 + "} }",
			"modifiers": "class CRMDeal {\n" + "async " * 8000 + "\n}",
			"class headers": "class a " * 50000,
			"divisions": "class CRMDeal { onLoad() { x = " + "(a) / " * 5000 + "1 } }",
		}
		for name, script in cases.items():
			with self.subTest(case=name):
				start = time.monotonic()
				analyse(script, "CRM Deal", "Form")
				self.assertLess(time.monotonic() - start, 2)

	def test_regex_literals(self):
		cases = [
			"if (x) /'/.test(y); call('a')",
			"n++ / total; call('a')",
			"async function f() { await /'/.test(x); call('a') }",
			"call(/* x */ /'/); call('a')",
		]
		for line in cases:
			with self.subTest(line=line):
				script = f"function setupForm({{ doc }}) {{\n  {line}\n}}"
				self.assertIn((2, "call"), found(analyse(script, "CRM Lead", "Form")))

	def test_setup_list_return_forms(self):
		for script in (
			"const setupList = ({ list }) => ({ actions: [], bulk_actions: [] })",
			"function setupList({ list }) { return ({ actions: [], 'bulk_actions': [] }) }",
		):
			with self.subTest(script=script):
				keys = {hit.key for hit in analyse(script, "CRM Lead", "List").hits}
				self.assertEqual(keys, {"list-actions", "list-bulk-actions"})

	def test_action_keys_count_only_inside_actions(self):
		script = """class CRMDeal {
  onLoad() {
    call('x', { group: 'a', onClick: 1 })
    this.tabs = [{ component: { render: () => h('button', { onClick: () => {} }) } }]
    this.actions.push({ group: 'b', onClick: () => {} })
  }
}"""
		keys = {key for line, key in found(analyse(script, "CRM Deal", "Form")) if line in (3, 4, 5)}
		self.assertEqual(
			keys, {"call", "tabs", "h-helper", "header-actions", "action-group", "action-on-click"}
		)
		actions = {
			line for line, key in found(analyse(script, "CRM Deal", "Form")) if key.startswith("action-")
		}
		self.assertEqual(actions, {5})

	def test_setup_form_needs_its_parenthesis(self):
		self.assertEqual(analyse("function setupForm ({ doc }) {}", "CRM Lead", "Form").shape, "Unknown")

	def test_helpers_a_shape_is_not_given(self):
		script = "function setupForm({ doc }) {\n  throwError('x'); createDialog({}); formDialog({}); socket.on()\n}"
		self.assertEqual(found(analyse(script, "CRM Lead", "Form")), {(1, "legacy-doc")})

	def test_a_class_script_that_also_holds_setup_form(self):
		script = "class CRMLead {}\nfunction setupForm({ doc }) {\n  updateField('status', 'New')\n  return { actions: [] }\n}"
		analysis = analyse(script, "CRM Lead", "Form")
		self.assertEqual(analysis.shape, "Class-based")
		self.assertEqual(found(analysis), {(2, "legacy-doc"), (3, "update-field"), (4, "header-actions")})

	def test_trigger_reaches_only_the_parent_class(self):
		script = "class CRMDeal {\n  onLoad() { this.doc.trigger(`after_save`) }\n  after_save() {}\n}\nclass CRMProducts {\n  after_save() {}\n}"
		hits = found(analyse(script, "CRM Deal", "Form"))
		self.assertNotIn((3, "unread-handler"), hits)
		self.assertIn((6, "unread-handler"), hits)

	def test_methods_with_calls_in_default_parameters(self):
		script = "class CRMDeal {\n  onLoad(a = f()) {}\n}"
		self.assertEqual(found(analyse(script, "CRM Deal", "Form")), {(2, "on-load")})

	def test_child_class_hit_is_on_the_class_line(self):
		script = "class CRMDeal {}\nclass CRMProducts\n{\n}"
		self.assertEqual(found(analyse(script, "CRM Deal", "Form")), {(2, "child-class")})


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
