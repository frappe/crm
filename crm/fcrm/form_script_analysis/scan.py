import json
import re
from dataclasses import dataclass
from functools import cached_property

import frappe

from crm.fcrm.form_script_analysis import patterns as p
from crm.fcrm.form_script_analysis.catalog import CATALOG
from crm.fcrm.form_script_analysis.source import Source


@dataclass(frozen=True)
class Hit:
	line: int
	key: str
	call: str
	verb: str | None
	gap: str | None


@dataclass(frozen=True)
class Analysis:
	shape: str
	hits: tuple[Hit, ...]


@dataclass(frozen=True)
class ClassBody:
	name: str
	start: int
	end: int


def analyse(script: str | None, doctype: str, view: str) -> Analysis:
	"""The v1 shape of a CRM Form Script and each v1 call in it, by line."""
	return Scan(script or "", doctype, view).analysis()


class Scan:
	def __init__(self, script: str, doctype: str, view: str):
		self.source = Source(script)
		self.doctype = doctype
		self.view = view
		self.found: dict[tuple[int, str], tuple[int, str]] = {}

	def analysis(self) -> Analysis:
		shape = self.shape
		self._scan_patterns(self.source.code, shape)
		if shape == p.CLASS:
			self._scan_classes()
		elif shape in (p.SETUP_FORM, p.SETUP_LIST):
			self._scan_setup_function(shape)
		hits = sorted(self.found.items(), key=lambda item: item[1][0])
		return Analysis(shape, tuple(self._hit(line, key, call) for (line, key), (_, call) in hits))

	@cached_property
	def shape(self) -> str:
		code = self.source.code
		if self.view == "List":
			return p.SETUP_LIST if p.SETUP_LIST_NAME.search(code) else p.UNKNOWN
		if self.classes and (self._parent_class or not p.SETUP_FORM_CALL.search(code)):
			return p.CLASS
		if p.SETUP_FORM_CALL.search(code):
			return p.SETUP_FORM
		return p.UNKNOWN

	def add(self, offset: int, key: str, call: str):
		line = self.source.line(offset)
		self.found.setdefault((line, key), (offset, call.strip()))

	def _hit(self, line: int, key: str, call: str) -> Hit:
		entry = CATALOG[key]
		return Hit(line=line, key=key, call=call, verb=entry.verb, gap=entry.gap)

	def _scan_patterns(self, code: str, shape: str):
		for key, shapes, pattern in p.PATTERNS:
			if shape in shapes:
				for match in pattern.finditer(code):
					self.add(match.start(), key, _call_text(code, match, key))

		dialogs = self._dialog_calls(code)
		for key, shapes, pattern in p.ACTION_PATTERNS:
			if shape in shapes:
				for match in pattern.finditer(code):
					if not any(start < match.start() < end for start, end in dialogs):
						self.add(match.start(), key, _call_text(code, match, key))

	def _dialog_calls(self, code: str) -> list[tuple[int, int]]:
		spans = []
		for match in p.DIALOG_CALL.finditer(code):
			start = match.end() - 1
			end = self.source.closing(start)
			spans.append((start, end))
			if match.group(1) != "formDialog":
				for html in p.DIALOG_HTML.finditer(code, start, end):
					self.add(html.start(), "create-dialog-html", "createDialog({ html })")
		return spans

	# Class-based shape

	@cached_property
	def classes(self) -> list[ClassBody]:
		bodies = []
		for match in p.CLASS_DEFINITION.finditer(self.source.code):
			start = match.end() - 1
			bodies.append(ClassBody(match.group(1), start, self.source.closing(start)))
		return bodies

	@cached_property
	def _parent_class(self) -> ClassBody | None:
		name = re.sub(r"\s+", "", self.doctype)
		return next((body for body in self.classes if body.name == name), None)

	def _scan_classes(self):
		methods = {body.name: self._methods(body) for body in self.classes}
		names = {name for found in methods.values() for name, _ in found}
		called = self._called(names)
		for body in self.classes:
			child = body is not self._parent_class
			if child:
				self.add(body.start, "child-class", f"class {body.name}")
			fields = self.meta.child_fields(body.name) if child else self.meta.fields
			for name, offset in methods[body.name]:
				key = self._handler_key(name, fields, child, name in called)
				if key:
					self.add(offset, key, f"{name}()")
		self._scan_set_field_property()

	def _methods(self, body: ClassBody) -> list[tuple[str, int]]:
		code, depth = self.source.code, self.source.depth(body.start) + 1
		return [
			(match.group(1), match.start(1))
			for match in p.METHOD_DEFINITION.finditer(code, body.start + 1, body.end)
			if self.source.depth(match.start()) == depth and match.group(1) not in p.NOT_METHODS
		]

	def _called(self, methods: set[str]) -> set[str]:
		called = {match.group(1) for match in p.TRIGGERED.finditer(self.source.text)}
		for match in p.THIS_CALL.finditer(self.source.code):
			if match.group(1) in methods:
				called.add(match.group(1))
				self.add(match.start(), "this-method-call", f"this.{match.group(1)}()")
		return called

	def _handler_key(self, name: str, fields: dict[str, str], child: bool, called: bool) -> str | None:
		if not child and name in p.LIFECYCLE:
			return p.LIFECYCLE[name]
		table, _, event = name.rpartition("_")
		if event in ("add", "remove") and self.meta.fields.get(table) == "Table":
			return "row-add" if event == "add" else "row-remove"
		if fields.get(name) == "Button":
			return "button-field-method"
		if name in fields:
			return "child-field-handler" if child else "field-handler"
		if not called and (name in p.UNREAD_HANDLERS or (child and name in p.LIFECYCLE)):
			return "unread-handler"
		return None

	def _scan_set_field_property(self):
		for match in p.SET_FIELD_PROPERTY.finditer(self.source.code):
			args = self._arguments(match.start(1))
			target = self.source.literal(*args[0]) if args else None
			call = f"this.setFieldProperty('{target}')" if target else "this.setFieldProperty()"
			for key in self._property_keys(args):
				self.add(match.start(), key, call)

	def _property_keys(self, args: list[tuple[int, int]]) -> list[str]:
		literal = [self.source.literal(*span) for span in args[:2]] + [None, None]
		target, prop = literal[0], literal[1]
		if len(args) >= 4:
			return ["row-property"]
		if target and "." in target:
			return ["child-column-property"]
		if prop == "button_color":
			return ["field-props"]
		if target is None or target in self.meta.fields:
			return ["set-field-property"]
		parts = self.meta.layout_parts(target)
		return parts or ["set-field-property"]

	def _arguments(self, paren: int) -> list[tuple[int, int]]:
		code, end = self.source.code, self.source.closing(paren)
		args, start, level = [], paren + 1, 0
		for i in range(paren + 1, end):
			level += (code[i] in "([{") - (code[i] in ")]}")
			if code[i] == "," and level == 0:
				args.append((start, i))
				start = i + 1
		if code[start:end].strip():
			args.append((start, end))
		return args

	# setupForm and setupList shapes

	def _scan_setup_function(self, shape: str):
		match = next((m for m in p.SETUP_FUNCTION.finditer(self.source.code) if m.group(1) == shape), None)
		if not match:
			return
		params_end = self.source.closing(match.start(2))
		body = self.source.code.find("{", params_end)
		if body == -1:
			return
		if shape == p.SETUP_FORM:
			self._scan_legacy_members(match.start(2) + 1, params_end)
		self._scan_return_keys(shape, body, self.source.closing(body))

	def _scan_legacy_members(self, start: int, end: int):
		params = self.source.code[start:end]
		if params.strip().startswith("{"):
			doc = re.search(r"(?<![\w$.])doc\b", params)
			if doc:
				self.add(start + doc.start(), "legacy-doc", "doc")
			return
		name = re.match(r"\s*([A-Za-z_$][\w$]*)", params)
		if not name:
			return
		# `setupForm(obj)`: read `obj.call(...)` as the bare `call(...)` a destructured script writes.
		member = re.compile(r"(?<![\w$.])" + re.escape(name.group(1)) + r"\.")
		doc = re.search(member.pattern + r"doc\b", self.source.code)
		if doc:
			self.add(doc.start(), "legacy-doc", f"{name.group(1)}.doc")
		bare = member.sub(lambda m: " " * len(m.group()), self.source.code)
		self._scan_patterns(bare, p.SETUP_FORM)

	def _scan_return_keys(self, shape: str, start: int, end: int):
		nested = self.source.function_bodies(start + 1, end)
		for match in p.RETURN_OBJECT.finditer(self.source.code, start, end):
			if any(a < match.start() < b for a, b in nested):
				continue
			for name, offset in self.source.object_keys(match.start(1)):
				key = p.RETURN_KEYS[shape].get(name, "unread-return-key")
				self.add(offset, key, f"return {{ {name} }}")

	@cached_property
	def meta(self) -> "DoctypeMeta":
		return DoctypeMeta(self.doctype)


class DoctypeMeta:
	"""The fields and CRM layout names a script's handlers and setFieldProperty calls are matched against."""

	def __init__(self, doctype: str):
		self.doctype = doctype

	@cached_property
	def fields(self) -> dict[str, str]:
		return _fieldtypes(self.doctype)

	def child_fields(self, class_name: str) -> dict[str, str]:
		for df in frappe.get_meta(self.doctype).get_table_fields():
			if re.sub(r"\s+", "", df.options) == class_name:
				return _fieldtypes(df.options)
		return {}

	def layout_parts(self, name: str) -> list[str]:
		return [key for key, names in self._layout_names.items() if name in names]

	@cached_property
	def _layout_names(self) -> dict[str, set[str]]:
		tabs, sections, panel = set(), set(), set()
		for item in _layout(self.doctype, "Data Fields"):
			if "sections" in item:
				tabs.add(item.get("name"))
				sections.update(section.get("name") for section in item["sections"])
			else:
				sections.add(item.get("name"))
		panel.update(section.get("name") for section in _layout(self.doctype, "Side Panel"))
		return {"tab-property": tabs, "section-property": sections, "panel-section-property": panel}


def _fieldtypes(doctype: str) -> dict[str, str]:
	return {df.fieldname: df.fieldtype for df in frappe.get_meta(doctype).fields}


def _layout(doctype: str, layout_type: str) -> list[dict]:
	layout = frappe.db.get_value("CRM Fields Layout", {"dt": doctype, "type": layout_type}, "layout")
	try:
		items = json.loads(layout or "[]")
	except ValueError:
		return []
	return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def _call_text(code: str, match: re.Match, key: str) -> str:
	"""The call as written: `call()`, `toast.error`, `this.doc.__newDocument`."""
	start = match.start()
	while start > 0 and (code[start - 1].isalnum() or code[start - 1] in "_$."):
		start -= 1
	text = re.sub(r"\s+", "", code[start : match.end()]).rstrip(":.")
	if text.startswith("."):
		return CATALOG[key].call
	return text + ")" if text.endswith("(") else text
