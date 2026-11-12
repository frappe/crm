<template>
	<div class="flex h-full min-h-0 flex-1 flex-col text-ink-gray-8">
		<ErrorMessage v-if="draft.loadError" class="px-3 py-3.5 sm:px-5" :message="draft.loadError" />
		<template v-if="draft.loaded">
			<EditorTab v-if="tab === 'editor'" :draft="draft" />
			<div v-else class="min-h-0 flex-1 overflow-y-auto px-3 pb-6 sm:px-5">
				<SettingsTab v-if="tab === 'settings'" :draft="draft" />
				<ShareTab v-else-if="tab === 'share'" :draft="draft" />
				<PreviewPane v-else :draft="draft" />
			</div>
		</template>
	</div>
</template>

<script setup>
import { ErrorMessage } from "frappe-ui";
import { reactive, toRef } from "vue";
import EditorTab from "./builder/EditorTab.vue";
import PreviewPane from "./builder/PreviewPane.vue";
import SettingsTab from "./builder/SettingsTab.vue";
import ShareTab from "./builder/ShareTab.vue";
import { useFormDraft } from "./builder/useFormDraft";
import { useLeaveGuard } from "./builder/useLeaveGuard";

const props = defineProps({
	name: { type: String, required: true },
	tab: { type: String, default: "editor" }, // editor | settings | share | preview
	router: { type: Object, default: null },
});
const emit = defineEmits(["saved"]);

// One reactive draft for the tabs and the header, which sits above this component's key.
const draft = reactive(useFormDraft({ name: props.name, onSaved: () => emit("saved") }));
useLeaveGuard(props.router, toRef(draft, "dirty"));

defineExpose({ draft });
</script>
