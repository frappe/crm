import { ref } from "vue";
import { fieldTypeIcon } from "../fieldTypeIcon";

// One drag at a time: a canvas field, a row of the panel's list, or a hidden row. It snapshots
// every list at the start, so Escape can put them back, and asks the drag layer whether the
// pointer let go over the bin. `layer` is a template ref to DragLayer.vue.
export function useEditorDrag({ draft, layer }) {
	const dragging = ref(false);
	let current = null; // { kind, element, columns, hidden, cancelled }

	function start(kind, evt) {
		const el = evt?.item?.__draggable_context?.element;
		window.getSelection()?.removeAllRanges();
		current = {
			kind,
			element: el,
			cancelled: false,
			columns: draft.sections.map((sec) => sec.columns.map((c) => [...c.items])),
			hidden: draft.hiddenFields.map((h) => ({ ...h })),
		};
		if (el) {
			const icon = el.icon || fieldTypeIcon(el.af || el);
			layer.value?.start({ label: el.label || el.fieldname, icon }, kind === "field");
		}
		dragging.value = true;
	}

	// returns what the drop did: { cancelled } after Escape, { removed: field } after a release over the bin
	function end() {
		dragging.value = false;
		const overBin = layer.value?.end();
		const result = { cancelled: !!current?.cancelled, removed: null };
		if (current?.cancelled) restore(current);
		else if (current?.kind === "field" && overBin) {
			draft.hiddenFields = current.hidden; // a release over the bin never leaves the field hidden
			result.removed = current.element;
		}
		current = null;
		return result;
	}

	function restore({ columns, hidden }) {
		draft.sections.forEach((sec, i) =>
			sec.columns.forEach(
				(c, j) => columns[i]?.[j] && c.items.splice(0, c.items.length, ...columns[i][j])
			)
		);
		draft.hiddenFields = hidden;
	}

	// Sortable ends its drag on the document's pointer/mouse up
	function cancel(e) {
		e.preventDefault();
		if (current) current.cancelled = true;
		const { x, y } = layer.value?.pos || {};
		document.dispatchEvent(
			new PointerEvent("pointerup", { bubbles: true, clientX: x, clientY: y })
		);
		document.dispatchEvent(new MouseEvent("mouseup", { bubbles: true, clientX: x, clientY: y }));
	}

	return {
		dragging,
		active: () => !!current,
		startField: (evt) => start("field", evt),
		startPalette: (evt) => start("palette", evt),
		startHidden: (evt) => start("hidden", evt),
		end,
		cancel,
	};
}
