// Pure helpers for the builder's field model. No Vue, no network.
export const BREAK_TYPES = ["Section Break", "Column Break"];

// a section can hold this many columns before it gets too cramped to build/fill
export const MAX_COLUMNS = 4;

export const TEXTAREA_TYPES = [
	"Small Text",
	"Text",
	"Long Text",
	"Text Editor",
	"HTML Editor",
	"Markdown Editor",
];

export function slugify(v) {
	return (v || "")
		.toString()
		.trim()
		.toLowerCase()
		.replace(/[^a-z0-9]+/g, "-")
		.replace(/^-+|-+$/g, "");
}

export function makeMarker(fieldtype) {
	return {
		fieldname: uid(fieldtype),
		label: "",
		fieldtype,
		options: "",
		reqd: false,
		placeholder: "",
		field_description: "",
	};
}

export function newColumn(colField = null) {
	return { colField, items: [] };
}

function newSection(secField = null) {
	return {
		secField: secField || makeMarker("Section Break"),
		columns: [newColumn()],
		editingLabel: false,
	};
}

// flat fields -> sections of columns of field items
export function buildSections(fields) {
	const secs = [];
	let cur = null;
	const ensureSection = () => {
		// fields before the first explicit Section Break get a synthesized one so
		// the first section is a normal, draggable section like the rest
		if (!cur) {
			cur = newSection();
			secs.push(cur);
		}
		return cur;
	};
	for (const f of fields || []) {
		if (f.fieldtype === "Section Break") {
			cur = newSection(f);
			secs.push(cur);
		} else if (f.fieldtype === "Column Break") {
			ensureSection().columns.push(newColumn(f));
		} else {
			const sec = ensureSection();
			sec.columns[sec.columns.length - 1].items.push(f);
		}
	}
	if (!secs.length) secs.push(newSection()); // empty form → one empty section
	return secs;
}

export function flattenSections(sections) {
	const out = [];
	for (const sec of sections) {
		out.push(sec.secField);
		emitColumns(out, sec.columns);
	}
	return out;
}

// group fields into sections -> columns for the preview
export function groupLayout(fields) {
	const sections = [];
	let cur = { label: null, columns: [[]] };
	for (const f of fields) {
		if (f.fieldtype === "Section Break") {
			sections.push(cur);
			cur = { label: f.label || null, columns: [[]] };
		} else if (f.fieldtype === "Column Break") {
			cur.columns.push([]);
		} else {
			cur.columns[cur.columns.length - 1].push(f);
		}
	}
	sections.push(cur);
	return sections.filter((s) => s.label || s.columns.some((c) => c.length));
}

export function inputType(f) {
	if (f.options === "Email") return "email";
	if (["Int", "Float", "Currency", "Percent"].includes(f.fieldtype)) return "number";
	if (f.fieldtype === "Date") return "date";
	if (f.fieldtype === "Datetime") return "datetime-local";
	if (f.fieldtype === "Time") return "time";
	if (f.fieldtype === "Color") return "color";
	return "text";
}

// a field picked from the target doctype's catalog, as a blank form field
export function newFieldFromCatalog(af) {
	return {
		fieldname: af.fieldname,
		label: af.label,
		fieldtype: af.fieldtype,
		options: af.options,
		reqd: !!af.reqd,
		placeholder: "",
		field_description: "",
		depends_on: "",
		mandatory_depends_on: "",
		read_only_depends_on: "",
	};
}

// a Select field's newline-separated options as a list
export function optionList(options) {
	return (options || "").split("\n").filter(Boolean);
}

export function fieldsFromServer(rows) {
	return (rows || []).map((f) => ({
		name: f.name,
		fieldname: f.fieldname,
		label: f.label,
		fieldtype: f.fieldtype,
		options: f.options,
		reqd: !!f.reqd,
		placeholder: f.placeholder,
		field_description: f.field_description,
		depends_on: f.depends_on || "",
		mandatory_depends_on: f.mandatory_depends_on || "",
		read_only_depends_on: f.read_only_depends_on || "",
	}));
}

export function toSavePayload(form, hiddenFields) {
	return {
		title: form.title,
		route: slugify(form.route),
		document_type: form.document_type,
		description: form.description,
		submit_button_label: form.submit_button_label,
		success_message: form.success_message,
		redirect_url: form.redirect_url,
		allowed_embedding_domains: form.allowed_embedding_domains,
		published: form.published ? 1 : 0,
		fields: form.fields.map((f) => ({
			fieldname: f.fieldname,
			label: f.label,
			fieldtype: f.fieldtype,
			options: f.options,
			reqd: f.reqd ? 1 : 0,
			placeholder: f.placeholder,
			field_description: f.field_description,
			depends_on: f.depends_on || "",
			mandatory_depends_on: f.mandatory_depends_on || "",
			read_only_depends_on: f.read_only_depends_on || "",
		})),
		hidden_fields: hiddenFields.map((h) => ({
			fieldname: h.fieldname,
			label: h.label,
			fieldtype: h.fieldtype,
			options: h.options,
			default: h.default,
		})),
	};
}

// emit a container's columns, normalising column-break markers to position
function emitColumns(out, cols) {
	cols.forEach((col, i) => {
		if (i === 0) {
			col.colField = null;
		} else if (!col.colField) {
			col.colField = makeMarker("Column Break");
		}
		if (col.colField) out.push(col.colField);
		for (const f of col.items) out.push(f);
	});
}

function uid(fieldtype) {
	const p = fieldtype === "Section Break" ? "section_break_" : "column_break_";
	return p + Math.random().toString(36).slice(2, 8);
}
