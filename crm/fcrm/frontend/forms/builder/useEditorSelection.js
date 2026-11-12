import { computed, onBeforeUnmount, ref } from "vue";

const OPEN_OVERLAY = "[role='listbox'], [role='menu'], [role='dialog'][aria-modal='true']";
const TYPING = "input, textarea, select, [contenteditable='true']";

// What the panel shows: a selected field, a selected section heading, or nothing.
// `draft` is the reactive form draft; `drag` is useEditorDrag (Escape cancels a drag first).
export function useEditorSelection({ draft, drag }) {
	const selected = ref(null); // { field } or { secField }

	const field = computed(() => selected.value?.field || null);
	const section = computed(() =>
		selected.value?.secField
			? draft.sections.find((s) => s.secField === selected.value.secField) || null
			: null
	);
	const sectionFieldCount = computed(
		() => section.value?.columns.reduce((n, c) => n + c.items.length, 0) || 0
	);

	const selectField = (f) => (selected.value = { field: f });
	const selectSection = (sec) => (selected.value = { secField: sec.secField });
	const isSectionSelected = (sec) => selected.value?.secField === sec.secField;
	const clear = () => (selected.value = null);

	function removeSelected() {
		const f = field.value;
		clear();
		if (f) draft.removeField(f);
	}

	function removeSelectedSection() {
		const sec = section.value;
		clear();
		if (sec) draft.removeBreak(sec.secField);
	}

	// a click on empty canvas clears the selection; a field or a heading stops its own click
	function onCanvasClick(e) {
		if (e.target.closest("[data-editor-select], input, textarea, button")) return;
		clear();
	}

	function onKeydown(e) {
		if (e.key === "Escape" && drag.active()) return drag.cancel(e);
		if (document.querySelector(OPEN_OVERLAY)) return;
		if (e.key === "Escape") return clear();
		if (!["Delete", "Backspace"].includes(e.key) || !field.value) return;
		if (e.target.closest?.(TYPING)) return;
		e.preventDefault();
		removeSelected();
	}

	window.addEventListener("keydown", onKeydown);
	onBeforeUnmount(() => window.removeEventListener("keydown", onKeydown));

	return {
		field,
		section,
		sectionFieldCount,
		selectField,
		selectSection,
		isSectionSelected,
		clear,
		removeSelected,
		removeSelectedSection,
		onCanvasClick,
		onKeydown,
	};
}
