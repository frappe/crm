import { toast } from "frappe-ui";
import { ref, reactive, computed } from "vue";
import { __ } from "frappe/i18n";
import { call, errorText } from "../formsApi";
import { fieldTypeIcon } from "../fieldTypeIcon";
import {
	fieldsFromServer,
	afterSubmitOf,
	buildSections,
	flattenSections,
	makeMarker,
	newColumn,
	newFieldFromCatalog,
	slugify,
	toSavePayload,
} from "./formModel";
import { docLabel, targetOptions, useDoctypeSwitch } from "./useDoctypeSwitch";
import { useHiddenRows } from "./useHiddenRows";
import { settledValue } from "./hiddenValue";
import { useLinkMeta } from "./useLinkMeta";

// The form being edited: load, dirty, save, publish and every structural edit.
// `form.fields` (flat) is the source of truth, derived into a draggable list of
// `sections`, each holding columns of field items. Every section (including the
// first) is a real Section Break, so they all behave identically. After any drag
// or structural change we re-flatten to form.fields.
export function useFormDraft({ name, onSaved }) {
	const linkMeta = useLinkMeta();
	const { ensureLinkMeta, ensureLinkOptions } = linkMeta;

	const loaded = ref(false);
	const loadError = ref("");
	const saving = ref(false);
	const dirty = ref(false);
	// while a draft still has an auto-generated route, keep it in sync with the
	// title; once the user edits the route (or the form is published) we stop
	const routeEdited = ref(false);
	// "Open form" and "Copy link" use the route the server holds, not the one being typed
	const savedRoute = ref("");
	const sections = ref([]);
	// fields kept off the form. Each carries a value applied to every record the form creates.
	const hiddenFields = ref([]);

	const form = reactive({
		name,
		title: "",
		route: "",
		document_type: "CRM Lead",
		description: "",
		submit_button_label: "Submit",
		success_message: "",
		redirect_url: "",
		after_submit: "message", // UI choice; save clears the other value
		allowed_embedding_domains: "",
		published: 0,
		fields: [],
	});

	const availableFields = reactive({
		data: null,
		async reload() {
			this.data = await call("get_form_fields", { document_type: form.document_type });
		},
	});

	// unused (not-yet-added) target fields, as Autocomplete options
	const availableFieldOptions = computed(() => {
		// hidden fields intentionally stay in the picker so they can be re-added to
		// the form (which also removes them from the hidden section)
		const used = new Set(form.fields.map((f) => f.fieldname));
		return (availableFields.data || [])
			.filter((f) => !used.has(f.fieldname))
			.map((af) => ({ label: af.label, value: af.fieldname, icon: fieldTypeIcon(af), af }))
			.sort((a, b) => a.label.localeCompare(b.label));
	});

	// fieldnames the target doctype marks mandatory (from the field catalog)
	const mandatorySet = computed(
		() => new Set((availableFields.data || []).filter((f) => f.reqd).map((f) => f.fieldname))
	);
	const doctypeLabel = computed(() => docLabel(form.document_type));

	const hidden = useHiddenRows({
		form,
		hiddenFields,
		availableFields,
		availableFieldOptions,
		linkMeta,
		markDirty: () => markDirty(),
	});

	// select is bound to this so we can intercept the change and confirm before
	// dropping incompatible fields; cancelling leaves form.document_type untouched
	// so the dropdown snaps back to the current value
	const doctypeModel = computed({
		get: () => form.document_type,
		set: (v) => requestDoctypeChange(v),
	});

	// every edit funnels through markDirty(), which just flags unsaved changes;
	// the user persists explicitly via the header Save button (saveNow)
	let revision = 0; // bumped per edit so a save can tell whether edits landed mid-request
	function markDirty() {
		revision++;
		dirty.value = true;
	}

	function isMandatory(fieldname) {
		return mandatorySet.value.has(fieldname);
	}

	function onTitleInput() {
		if (!routeEdited.value && !form.published) form.route = slugify(form.title);
		markDirty();
	}

	// header Publish: saves pending edits with it, so the guard (every hidden field
	// needs a default) runs; a refused or failed save leaves the form a draft
	async function publish() {
		if (saving.value) return;
		form.published = 1;
		const ok = await save();
		if (!ok) form.published = 0;
		else {
			routeEdited.value = true; // the link is live: a later rename must not move it
			toast.success(__("Form published"));
		}
	}

	// header Unpublish takes the form down at once; unsaved edits stay unsaved
	async function unpublish() {
		if (saving.value) return;
		saving.value = true; // holds off a save, so the two requests cannot cross
		try {
			await call("set_published", { name: form.name, published: 0 });
			form.published = 0;
			toast.success(__("Form unpublished"));
		} catch (e) {
			toast.error(errorText(e, __("Could not unpublish the form")));
		} finally {
			saving.value = false;
		}
	}

	function rebuildModel() {
		sections.value = buildSections(form.fields);
	}

	function syncFromModel() {
		form.fields = flattenSections(sections.value);
		markDirty();
	}

	// apply an edit from the field panel to the parent-owned field object
	function updateField(f, patch) {
		Object.assign(f, patch);
		markDirty();
	}

	function removeField(f) {
		form.fields = form.fields.filter((x) => x !== f);
		rebuildModel();
		markDirty();
	}

	function removeBreak(marker) {
		// dropping a break marker merges its content back into the previous
		// section/column (rebuildGroups normalises the structure)
		form.fields = form.fields.filter((x) => x !== marker);
		rebuildModel();
		markDirty();
	}

	// add a field into a column (at the end, or at `index`); returns the new field
	function addFieldToColumn(col, option, index = col.items.length) {
		const af = option?.af || option;
		if (!af?.fieldname) return null;
		// re-adding a field that was moved to hidden brings it back onto the form
		hiddenFields.value = hiddenFields.value.filter((h) => h.fieldname !== af.fieldname);
		const field = newFieldFromCatalog(af);
		col.items.splice(index, 0, field);
		if (af.fieldtype === "Link") ensureLinkMeta(af.options);
		syncFromModel();
		return field;
	}

	// a section's "Add field": after the selected field when it is in the section, else in its shortest column
	function addFieldToSection(sec, option, after = null) {
		const col = sec.columns.find((c) => c.items.includes(after));
		const target = col || sec.columns.reduce((a, c) => (c.items.length <= a.items.length ? c : a));
		return addFieldToColumn(
			target,
			option,
			col ? col.items.indexOf(after) + 1 : target.items.length
		);
	}

	// "Add to form" on a hidden row: the end of the last section, in its shortest column
	function addHiddenToForm(h) {
		return addFieldToSection(sections.value.at(-1), hidden.catalogField(h.fieldname) || h);
	}

	// a field dragged in from the panel's list or the hidden block lands as a clone: tidy the model after it
	function settleCloneDrop() {
		const onForm = new Set(flattenSections(sections.value).map((f) => f.fieldname));
		hiddenFields.value = hiddenFields.value.filter((h) => !onForm.has(h.fieldname));
		syncFromModel();
		form.fields.forEach((f) => f.fieldtype === "Link" && ensureLinkMeta(f.options));
	}

	function addSection() {
		form.fields.push(makeMarker("Section Break"));
		rebuildModel();
		markDirty();
		return sections.value.at(-1);
	}

	// the panel's Columns setting: add empty columns, or fold the last ones into the previous
	function setColumns(sec, count) {
		const cols = sec.columns;
		while (cols.length < count) cols.push(newColumn());
		while (cols.length > Math.max(count, 1)) {
			const last = cols.pop();
			cols.at(-1).items.push(...last.items);
		}
		syncFromModel();
	}

	// header Save button: persist and confirm (errors are toasted inside save())
	async function saveNow() {
		if (!dirty.value || saving.value) return;
		const ok = await save();
		if (ok) toast.success(__("Form updated"));
	}

	async function save({ silent = false } = {}) {
		// drafts auto-save freely; only a published form requires every hidden field
		// to carry a default (an empty one would break record creation)
		hidden.settleHiddenDefaults();
		if (form.published) {
			const missing = hidden.unpublishableRows();
			if (missing.length) {
				hidden.stopEditing(); // the refused required rows turn red again
				if (!silent)
					toast.error(
						__("Give a value to, or add to the form: {0}", [
							missing.map((h) => h.label || h.fieldname).join(", "),
						])
					);
				return false;
			}
		}
		if (!loaded.value || saving.value) return false;
		saving.value = true;
		const savedRevision = revision;
		// normalise from the model so every section break (incl. the first) persists
		form.fields = flattenSections(sections.value);
		try {
			const doc = await call("save_form", {
				name: form.name,
				form: toSavePayload(form, hiddenFields.value),
			});
			form.route = doc.route;
			savedRoute.value = doc.route;
			(doc.fields || []).forEach((df, i) => {
				if (form.fields[i]) form.fields[i].name = df.name;
			});
			dirty.value = savedRevision !== revision;
			onSaved?.();
			return true;
		} catch (e) {
			if (!silent) toast.error(e?.messages?.[0] || e?.message || __("Could not save"));
			return false;
		} finally {
			saving.value = false;
		}
	}

	function load() {
		call("get_form_config", { name })
			.then((doc) => {
				form.title = doc.title || "";
				form.route = doc.route || "";
				savedRoute.value = form.route;
				form.document_type = doc.document_type || "CRM Lead";
				form.description = doc.description || "";
				form.submit_button_label = doc.submit_button_label || "Submit";
				form.success_message = doc.success_message || "";
				form.redirect_url = doc.redirect_url || "";
				form.after_submit = afterSubmitOf(form);
				form.allowed_embedding_domains = doc.allowed_embedding_domains || "";
				form.published = doc.published || 0;
				form.fields = fieldsFromServer(doc.fields);
				setHiddenFields(doc.hidden_fields);
				// resolve guest-access state up front so a Link field can warn on the build tab
				form.fields.forEach((f) => {
					if (f.fieldtype === "Link") ensureLinkMeta(f.options);
				});
				rebuildModel();
				// only keep auto-syncing the route if it's still an untouched default
				routeEdited.value = !/^untitled-form(-\d+)?$/.test(form.route);
				loaded.value = true;
				availableFields.reload();
			})
			.catch((e) => {
				loadError.value = errorText(e, __("Could not load the form"));
			});
	}

	function setHiddenFields(rows) {
		hiddenFields.value = (rows || []).map((h) => ({
			fieldname: h.fieldname,
			label: h.label,
			fieldtype: h.fieldtype,
			options: h.options || "",
			default: settledValue(h.fieldtype, h.default),
		}));
		hiddenFields.value.forEach((h) => {
			if (h.fieldtype === "Link") ensureLinkOptions(h.options);
		});
	}

	const { requestDoctypeChange } = useDoctypeSwitch({
		form,
		hiddenFields,
		availableFields,
		linkMeta,
		setHiddenFields,
		rebuildModel,
		markDirty,
	});

	load();

	return {
		form,
		loaded,
		loadError,
		saving,
		dirty,
		routeEdited,
		savedRoute,
		sections,
		hiddenFields,
		...hidden,
		availableFieldOptions,
		doctypeModel,
		targetOptions,
		doctypeLabel,
		linkMeta,
		isMandatory,
		markDirty,
		onTitleInput,
		publish,
		unpublish,
		syncFromModel,
		addFieldToColumn,
		addFieldToSection,
		addHiddenToForm,
		addSection,
		settleCloneDrop,
		setColumns,
		updateField,
		removeField,
		removeBreak,
		saveNow,
	};
}
