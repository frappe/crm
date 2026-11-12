import { toast } from "frappe-ui";
import { ref, reactive, computed } from "vue";
import { __ } from "frappe/i18n";
import { call, errorText } from "../formsApi";
import {
	fieldsFromServer,
	MAX_COLUMNS,
	afterSubmitOf,
	buildSections,
	flattenSections,
	makeMarker,
	newColumn,
	newFieldFromCatalog,
	slugify,
	toSavePayload,
} from "./formModel";
import { targetOptions, useDoctypeSwitch } from "./useDoctypeSwitch";
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
	const expanded = ref(null); // fieldname of the expanded field editor
	// while a draft still has an auto-generated route, keep it in sync with the
	// title; once the user edits the route (or the form is published) we stop
	const routeEdited = ref(false);
	const sections = ref([]);
	// doctype-mandatory fields removed from the visible form. Each carries a default
	// value that's applied on submission so the record can still be created.
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
			.map((af) => ({ label: af.label, value: af.fieldname, af }));
	});

	// fieldnames the target doctype marks mandatory (from the field catalog). They
	// stay in the form: the server only accepts system-managed fields as hidden.
	const mandatorySet = computed(
		() => new Set((availableFields.data || []).filter((f) => f.reqd).map((f) => f.fieldname))
	);
	// true while any hidden required field is missing its default (blocks publish)
	const hiddenMissingDefault = computed(() =>
		hiddenFields.value.some((h) => !String(h.default || "").trim())
	);

	// select is bound to this so we can intercept the change and confirm before
	// dropping incompatible fields; cancelling leaves form.document_type untouched
	// so the dropdown snaps back to the current value
	const doctypeModel = computed({
		get: () => form.document_type,
		set: (v) => requestDoctypeChange(v),
	});

	// a section can't take a new column break once the last one is full
	const columnBreakDisabled = computed(() => {
		const secs = sections.value;
		return (secs.length ? secs[secs.length - 1].columns.length : 1) >= MAX_COLUMNS;
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

	// header Publish toggle: flip the flag locally (instant, no animation) and mark
	// dirty — like Assignment Rule's Enabled switch, it persists on Save, where the
	// publish guard (every hidden field needs a default) is enforced
	function togglePublish() {
		form.published = form.published ? 0 : 1;
		markDirty();
	}

	function rebuildModel() {
		sections.value = buildSections(form.fields);
	}

	function syncFromModel() {
		form.fields = flattenSections(sections.value);
		markDirty();
	}

	// apply an edit emitted by a FieldCard to the parent-owned field object
	function updateField(f, patch) {
		Object.assign(f, patch);
		markDirty();
	}

	function removeField(f) {
		form.fields = form.fields.filter((x) => x !== f);
		if (expanded.value === f.fieldname) expanded.value = null;
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

	function addBreak(fieldtype) {
		if (fieldtype === "Column Break" && columnBreakDisabled.value) {
			toast.info(__("A section can have up to {0} columns", [MAX_COLUMNS]));
			return;
		}
		// append at the end: a Section Break starts a new section, a Column Break
		// adds a new column to the last section
		form.fields.push(makeMarker(fieldtype));
		rebuildModel();
		markDirty();
	}

	function toggle(f) {
		expanded.value = expanded.value === f.fieldname ? null : f.fieldname;
	}

	// focusing a field's label selects it (reveals inline editor) without toggling off
	function open(f) {
		expanded.value = f.fieldname;
	}

	// add a field into a specific column, then re-flatten to form.fields
	function addFieldToColumn(col, option) {
		const af = option?.af || option;
		if (!af?.fieldname) return;
		// a freshly added field starts collapsed, not stacked under a previously open one
		expanded.value = null;
		// re-adding a field that was moved to hidden brings it back onto the form
		hiddenFields.value = hiddenFields.value.filter((h) => h.fieldname !== af.fieldname);
		col.items.push(newFieldFromCatalog(af));
		if (af.fieldtype === "Link") ensureLinkMeta(af.options);
		syncFromModel();
	}

	function addColumn(cols) {
		if (cols.length >= MAX_COLUMNS) {
			toast.info(__("A section can have up to {0} columns", [MAX_COLUMNS]));
			return;
		}
		cols.push(newColumn());
		syncFromModel();
	}

	function removeLastColumn(cols) {
		if (cols.length <= 1) return;
		const last = cols[cols.length - 1];
		const prev = cols[cols.length - 2];
		if (last.items.length) prev.items.push(...last.items); // keep the fields
		cols.pop();
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
		if (form.published) {
			const missing = hiddenFields.value.filter((h) => !String(h.default || "").trim());
			if (missing.length) {
				if (!silent)
					toast.error(
						__("Set a default value for hidden required field(s): {0}", [
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
			default: h.default ?? "",
		}));
		hiddenFields.value.forEach((h) => {
			if (h.fieldtype === "Link") ensureLinkOptions(h.options);
		});
	}

	const { requestDoctypeChange } = useDoctypeSwitch({
		form,
		expanded,
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
		expanded,
		routeEdited,
		sections,
		hiddenFields,
		hiddenMissingDefault,
		availableFieldOptions,
		doctypeModel,
		targetOptions,
		linkMeta,
		isMandatory,
		markDirty,
		onTitleInput,
		togglePublish,
		syncFromModel,
		toggle,
		open,
		addFieldToColumn,
		addColumn,
		removeLastColumn,
		updateField,
		removeField,
		removeBreak,
		addBreak,
		saveNow,
	};
}
