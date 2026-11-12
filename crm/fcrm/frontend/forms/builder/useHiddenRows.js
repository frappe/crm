import { computed, nextTick, reactive } from "vue";
import { newFieldFromCatalog } from "./formModel";
import { initialValue, settledValue, storedValue } from "./hiddenValue";

// The Hidden fields block: the form's hidden entries, plus a "missing" row for every
// record-required field that is neither on the form nor hidden with a value.
export function useHiddenRows({
	form,
	hiddenFields,
	availableFields,
	availableFieldOptions,
	linkMeta,
	markDirty,
}) {
	// rows given an empty control by "Set a value" or "Add hidden field"
	const editingHidden = reactive(new Set());

	const catalogField = (fieldname) =>
		(availableFields.data || []).find((f) => f.fieldname === fieldname);

	const hiddenRows = computed(() => {
		const onForm = new Set(form.fields.map((f) => f.fieldname));
		const listed = new Set(hiddenFields.value.map((h) => h.fieldname));
		const missing = (availableFields.data || [])
			.filter((f) => f.reqd && !f.default && !onForm.has(f.fieldname) && !listed.has(f.fieldname))
			.map((f) => ({ ...hiddenEntry(f), missing: true }));
		return [...hiddenFields.value, ...missing];
	});

	function hiddenEntry(f) {
		return {
			fieldname: f.fieldname,
			label: f.label,
			fieldtype: f.fieldtype,
			options: f.options || "",
			default: initialValue(f.fieldtype),
		};
	}

	const isBlank = (h) => !String(h.default || "").trim();
	const isRequired = (h) => {
		const f = catalogField(h.fieldname);
		return !f || (!!f.reqd && !f.default); // not in the catalog: a system-managed mandatory field
	};
	const isMissingRow = (h) =>
		!!h.missing || (isBlank(h) && isRequired(h) && !editingHidden.has(h.fieldname));

	const unpublishableRows = () => hiddenRows.value.filter((h) => h.missing || isBlank(h));
	const stopEditing = () => editingHidden.clear();

	// system-managed fields (Status, …) are hidden-only: not in the catalog, so never put on the form
	const canAddToForm = (h) => !!catalogField(h.fieldname);

	const cloneHidden = (h) => newFieldFromCatalog(catalogField(h.fieldname) || h);

	const hiddenPickerOptions = computed(() => {
		const listed = new Set(hiddenRows.value.map((h) => h.fieldname));
		return availableFieldOptions.value.filter((o) => !listed.has(o.value));
	});

	function addHiddenEntry(f, index = hiddenFields.value.length) {
		if (!hiddenFields.value.some((h) => h.fieldname === f.fieldname))
			hiddenFields.value.splice(index, 0, hiddenEntry(f));
		if (f.fieldtype === "Link") linkMeta.ensureLinkOptions(f.options);
		editingHidden.add(f.fieldname);
		markDirty();
	}

	function focusHiddenValue(fieldname) {
		nextTick(() =>
			document
				.querySelector(`[data-hidden-fieldname="${fieldname}"]`)
				?.querySelector("input, select, button")
				?.focus()
		);
	}

	function setHiddenValue(h) {
		addHiddenEntry(h);
		focusHiddenValue(h.fieldname);
	}

	function addHiddenField(option) {
		if (!option?.af) return;
		addHiddenEntry(option.af);
		focusHiddenValue(option.af.fieldname);
	}

	// a field dropped into the block (from the form or the panel's list) becomes a hidden entry
	function onHiddenChange({ added }) {
		if (!added) return;
		const el = added.element;
		const f = el.af || catalogField(el.fieldname) || el;
		addHiddenEntry(f, Math.min(added.newIndex, hiddenFields.value.length));
	}

	function setHiddenDefault(h, value) {
		h.default = storedValue(h.fieldtype, value);
		markDirty();
	}

	function settleHiddenDefault(h) {
		const value = settledValue(h.fieldtype, h.default);
		if (value !== h.default) setHiddenDefault(h, value);
	}

	const settleHiddenDefaults = () => hiddenFields.value.forEach(settleHiddenDefault);

	return {
		hiddenRows,
		catalogField,
		isMissingRow,
		unpublishableRows,
		stopEditing,
		canAddToForm,
		cloneHidden,
		hiddenPickerOptions,
		addHiddenEntry,
		setHiddenValue,
		setHiddenDefault,
		settleHiddenDefault,
		settleHiddenDefaults,
		addHiddenField,
		onHiddenChange,
	};
}
