import bisect
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
	offset: int
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
		if shape == p.SETUP_FORM or (shape == p.CLASS and self._has_setup_form):
			# CRM v1 also runs a setupForm that a class-based Form script holds.
			if shape == p.CLASS:
				self._scan_patterns(self.source.code, p.SETUP_FORM)
			self._scan_setup_function(p.SETUP_FORM)
		if shape == p.SETUP_LIST:
			self._scan_setup_function(p.SETUP_LIST)
		hits = sorted(self.found.items(), key=lambda item: item[1][0])
		return Analysis(shape, tuple(self._hit(line, key, call) for (line, key), (_, call) in hits))

	@cached_property
	def shape(self) -> str:
		if self.view == "List":
			return p.SETUP_LIST if p.SETUP_LIST_NAME.search(self.source.code) else p.UNKNOWN
		if self.classes and (self._parent_class or not self._has_setup_form):
			return p.CLASS
		return p.SETUP_FORM if self._has_setup_form else p.UNKNOWN

	@cached_property
	def _has_setup_form(self) -> bool:
		return bool(p.SETUP_FORM_CALL.search(self.source.code))

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

		dialogs = Spans(self._dialog_calls(code))
		actions = Spans(self._spans(p.ACTION_ARRAY, code))
		for key, shapes, pattern in p.ACTION_PATTERNS:
			if shape in shapes:
				for match in pattern.finditer(code):
					if match.start() in actions and match.start() not in dialogs:
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

	def _spans(self, pattern: re.Pattern, code: str) -> list[tuple[int, int]]:
		return [(match.start(1), self.source.closing(match.start(1))) for match in pattern.finditer(code)]

	# Class-based shape

	@cached_property
	def classes(self) -> list[ClassBody]:
		bodies = []
		for match in p.CLASS_DEFINITION.finditer(self.source.code):
			start = match.end() - 1
			bodies.append(ClassBody(match.group(1), match.start(), start, self.source.closing(start)))
		return bodies

	@cached_property
	def _parent_class(self) -> ClassBody | None:
		name = re.sub(r"\s+", "", self.doctype)
		return next((body for body in self.classes if body.name == name), None)

	def _scan_classes(self):
		for body in self.classes:
			methods = self._methods(body)
			called = self._called(body, {name for name, _ in methods})
			child = body is not self._parent_class
			if child:
				self.add(body.offset, "child-class", f"class {body.name}")
			fields = self.meta.child_fields(body.name) if child else self.meta.fields
			for name, offset in methods:
				key = self._handler_key(body, name, fields, name in called)
				if key:
					self.add(offset, key, f"{name}()")
		self._scan_set_field_property()

	def _methods(self, body: ClassBody) -> list[tuple[str, int]]:
		depth = self.source.depth(body.start) + 1
		return [
			(match.group(1), match.start(1))
			for match in p.METHOD_DEFINITION.finditer(self.source.code, body.start + 1, body.end)
			if self.source.depth(match.start()) == depth and match.group(1) not in p.NOT_METHODS
		]

	def _called(self, body: ClassBody, methods: set[str]) -> set[str]:
		"""Methods of this class the script calls itself. `trigger` always reaches the parent class."""
		called = set()
		if body is self._parent_class:
			called = {match.group(1) for match in p.TRIGGERED.finditer(self.source.text)}
		for match in p.THIS_CALL.finditer(self.source.code, body.start, body.end):
			if match.group(1) in methods:
				called.add(match.group(1))
				self.add(match.start(), "this-method-call", f"this.{match.group(1)}()")
		return called

	def _handler_key(self, body: ClassBody, name: str, fields: dict[str, str], called: bool) -> str | None:
		child = body is not self._parent_class
		if not child and name in p.LIFECYCLE:
			return p.LIFECYCLE[name]
		table, _, event = name.rpartition("_")
		if child and event in ("add", "remove") and self.meta.table_class(table) == body.name:
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
			for key in self._property_keys(args, target):
				self.add(match.start(), key, call)

	def _property_keys(self, args: list[tuple[int, int]], target: str | None) -> list[str]:
		prop = self.source.literal(*args[1]) if len(args) > 1 else None
		if len(args) >= 4:
			return ["row-property"]
		if target and "." in target:
			return ["child-column-property"]
		if prop == "button_color":
			return ["field-props"]
		if target is None or target in self.meta.fields:
			return ["set-field-property"]
		return self.meta.layout_parts(target) or ["set-field-property"]

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
		code = self.source.code
		match = next((m for m in p.SETUP_FUNCTION.finditer(code) if m.group(1) == shape), None)
		if not match:
			return
		params_end = self.source.closing(match.start(2))
		if shape == p.SETUP_FORM:
			self._scan_legacy_members(match.start(2) + 1, params_end)
		arrow_object = p.ARROW_OBJECT.match(code, params_end + 1)
		if arrow_object:
			self._add_return_keys(shape, arrow_object.start(1))
			return
		body = code.find("{", params_end)
		if body != -1:
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
		nested = Spans(self.source.function_bodies(start + 1, end))
		for match in p.RETURN_OBJECT.finditer(self.source.code, start, end):
			if match.start() not in nested:
				self._add_return_keys(shape, match.start(1))

	def _add_return_keys(self, shape: str, obj: int):
		for name, offset in self.source.object_keys(obj):
			key = p.RETURN_KEYS[shape].get(name, "unread-return-key")
			self.add(offset, key, f"return {{ {name} }}")

	@cached_property
	def meta(self) -> "DoctypeMeta":
		return DoctypeMeta(self.doctype)


class Spans:
	"""Offset ranges, for a fast "is this offset inside any of them" test."""

	def __init__(self, spans: list[tuple[int, int]]):
		merged = []
		for start, end in sorted(spans):
			if merged and start <= merged[-1][1]:
				merged[-1][1] = max(merged[-1][1], end)
			else:
				merged.append([start, end])
		self.starts = [start for start, _ in merged]
		self.ends = [end for _, end in merged]

	def __contains__(self, offset: int) -> bool:
		i = bisect.bisect_right(self.starts, offset) - 1
		return i >= 0 and offset < self.ends[i]


class DoctypeMeta:
	"""The fields and CRM layout names a script's handlers and setFieldProperty calls are matched against."""

	def __init__(self, doctype: str):
		self.doctype = doctype

	@cached_property
	def fields(self) -> dict[str, str]:
		return {df.fieldname: df.fieldtype for df in self._docfields}

	def child_fields(self, class_name: str) -> dict[str, str]:
		table = self._tables.get(class_name)
		return {df.fieldname: df.fieldtype for df in _docfields(table.options)} if table else {}

	def table_class(self, fieldname: str) -> str | None:
		"""The class name CRM v1 routes a Table field's row events to."""
		return next((name for name, df in self._tables.items() if df.fieldname == fieldname), None)

	def layout_parts(self, name: str) -> list[str]:
		return [key for key, names in self._layout_names.items() if name in names]

	@cached_property
	def _docfields(self) -> list:
		return _docfields(self.doctype)

	@cached_property
	def _tables(self) -> dict:
		return {re.sub(r"\s+", "", df.options or ""): df for df in self._docfields if df.fieldtype == "Table"}

	@cached_property
	def _layout_names(self) -> dict[str, set[str]]:
		tabs, sections = [], []
		for item in _layout(self.doctype, "Data Fields"):
			if "sections" in item:
				tabs.append(item.get("name"))
				sections += [section.get("name") for section in _dicts(item["sections"])]
			else:
				sections.append(item.get("name"))
		panel = [section.get("name") for section in _layout(self.doctype, "Side Panel")]
		parts = {"tab-property": tabs, "section-property": sections, "panel-section-property": panel}
		return {key: {name for name in names if isinstance(name, str)} for key, names in parts.items()}


def _docfields(doctype: str | None) -> list:
	# A row can name a doctype that is gone (its app uninstalled): the patch must not stop on it.
	if not doctype or not frappe.db.exists("DocType", doctype):
		return []
	return frappe.get_meta(doctype).fields


def _layout(doctype: str, layout_type: str) -> list[dict]:
	layout = frappe.db.get_value("CRM Fields Layout", {"dt": doctype, "type": layout_type}, "layout")
	try:
		return _dicts(json.loads(layout or "[]"))
	except ValueError:
		return []


def _dicts(items) -> list[dict]:
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
