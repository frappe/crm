<template>
	<div class="flex flex-col text-ink-gray-8">
		<BuilderHeader :draft="draft" v-model:mode="mode" @back="emit('back')" />

		<ErrorMessage v-if="draft.loadError.value" class="py-3.5" :message="draft.loadError.value" />
		<div v-if="draft.loaded.value" class="pb-6">
			<div v-if="mode === 'edit'" class="wf-tabs">
				<Tabs v-model="activeTab" as="div" :tabs="tabs">
					<template #tab-panel="{ tab }">
						<EditorTab v-if="tab.value === 'editor'" :draft="draft" />
						<SettingsTab v-else-if="tab.value === 'settings'" :draft="draft" />
						<ShareTab v-else :draft="draft" />
					</template>
				</Tabs>
			</div>
			<PreviewPane v-else :draft="draft" />
		</div>
	</div>
</template>

<script setup>
import { ErrorMessage, Tabs } from "frappe-ui";
import { ref } from "vue";
import { __ } from "frappe/i18n";
import BuilderHeader from "./builder/BuilderHeader.vue";
import EditorTab from "./builder/EditorTab.vue";
import PreviewPane from "./builder/PreviewPane.vue";
import SettingsTab from "./builder/SettingsTab.vue";
import ShareTab from "./builder/ShareTab.vue";
import { useFormDraft } from "./builder/useFormDraft";
import { useLeaveGuard } from "./builder/useLeaveGuard";

const props = defineProps({
	name: { type: String, required: true },
	router: { type: Object, default: null },
});
const emit = defineEmits(["back", "saved"]);

const draft = useFormDraft({ name: props.name, onSaved: () => emit("saved") });
useLeaveGuard(props.router, draft.dirty);

const mode = ref("edit"); // edit | preview
const activeTab = ref("editor");
const tabs = [
	{ value: "editor", label: __("Editor"), iconLeft: "lucide-layout-list" },
	{ value: "settings", label: __("Settings"), iconLeft: "lucide-settings" },
	{ value: "share", label: __("Share"), iconLeft: "lucide-share-2" },
];
</script>

<style>
/* The frappe-ui Tabs root is overflow-hidden, which would trap a sticky child;
   relax it so the tab list can stick to the outer scroll container. */
.wf-tabs > div {
	overflow: visible;
}

/* Keep just the tab bar (Editor / Settings / Share) pinned to the top while the
   panel scrolls. px-0 aligns the labels + underline with the content below
   (frappe-ui bakes px-5 into the list). */
.wf-tabs [role="tablist"] {
	position: sticky;
	top: 0;
	z-index: 10;
	padding-left: 0;
	padding-right: 0;
	background-color: var(--surface-base, #fff);
}
</style>
