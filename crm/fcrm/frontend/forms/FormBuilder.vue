<template>
	<div class="flex flex-col text-ink-gray-8">
		<ErrorMessage v-if="draft.loadError.value" class="py-3.5" :message="draft.loadError.value" />
		<div v-if="draft.loaded.value" class="pb-6">
			<EditorTab v-if="tab === 'editor'" :draft="draft" />
			<SettingsTab v-else-if="tab === 'settings'" :draft="draft" />
			<ShareTab v-else-if="tab === 'share'" :draft="draft" />
			<PreviewPane v-else :draft="draft" />
		</div>
	</div>
</template>

<script setup>
import { ErrorMessage } from "frappe-ui";
import { reactive } from "vue";
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

const draft = useFormDraft({ name: props.name, onSaved: () => emit("saved") });
useLeaveGuard(props.router, draft.dirty);

// The header sits above this component's key, so it reads the draft from here.
defineExpose({ draft: reactive(draft) });
</script>
