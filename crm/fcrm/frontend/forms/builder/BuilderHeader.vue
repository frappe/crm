<!-- The builder's header: crumbs, Draft/Published badge, Not Saved, Save, and the tab strip. -->
<template>
	<PageHeader>
		<div class="flex w-full flex-col">
			<div
				class="-mx-3 flex h-12 items-center justify-between gap-3 border-b px-3 sm:-mx-5 sm:px-5"
			>
				<div class="flex min-w-0 flex-1 items-center gap-2">
					<Breadcrumbs class="-ml-0.5 min-w-0" :items="crumbs" />
					<Dropdown v-if="ready" :options="publishMenu" side="bottom" align="start">
						<button
							type="button"
							:aria-label="__('Publish status: {0}', [published ? __('Published') : __('Draft')])"
							class="flex shrink-0 items-center rounded-full focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
						>
							<Badge
								:label="published ? __('Published') : __('Draft')"
								:theme="published ? 'green' : 'gray'"
							>
								<template #suffix>
									<span class="lucide-chevron-down -mr-0.5 size-3" aria-hidden="true" />
								</template>
							</Badge>
						</button>
					</Dropdown>
					<Badge v-if="ready && draft.dirty" :label="__('Not Saved')" theme="amber" />
				</div>
				<Tooltip v-if="ready" :text="__('No changes to save')" :disabled="draft.dirty">
					<div class="flex shrink-0">
						<Button
							variant="solid"
							:label="__('Save')"
							:disabled="!draft.dirty"
							:loading="draft.saving"
							@click="draft.saveNow()"
						/>
					</div>
				</Tooltip>
			</div>
			<!-- The record page's strip; its bottom border sits on the header's, so one line shows. -->
			<Tabs
				:model-value="tab"
				class="-mx-3 -mb-px sm:-mx-5 [&_[role='tab']]:rounded-4 [&_[role='tablist']]:gap-5 [&_[role='tablist']]:px-3 [&_[role='tablist']]:py-2 sm:[&_[role='tablist']]:px-5"
				@update:model-value="emit('update:tab', $event)"
			>
				<TabList variant="underline">
					<TabTrigger
						v-for="t in TABS"
						:key="t.value"
						:value="t.value"
						:label="t.label"
						:icon-left="t.iconLeft"
					/>
				</TabList>
			</Tabs>
		</div>
	</PageHeader>
</template>

<script setup>
import { computed } from "vue";
import {
	Badge,
	Breadcrumbs,
	Button,
	Dropdown,
	PageHeader,
	TabList,
	TabTrigger,
	Tabs,
	Tooltip,
} from "frappe-ui";
import { __ } from "frappe/i18n";
import { copyToClipboard } from "../formsApi";

const props = defineProps({
	draft: { type: Object, default: null }, // the builder's draft, unwrapped; null until the builder mounts
	tab: { type: String, required: true },
});
const emit = defineEmits(["back", "update:tab"]);

const TABS = [
	{ value: "editor", label: __("Editor"), iconLeft: "lucide-layout-list" },
	{ value: "settings", label: __("Settings"), iconLeft: "lucide-settings" },
	{ value: "share", label: __("Share"), iconLeft: "lucide-share-2" },
	{ value: "preview", label: __("Preview"), iconLeft: "lucide-eye" },
];

const ready = computed(() => Boolean(props.draft?.loaded));
const published = computed(() => Boolean(props.draft?.form.published));
const crumbs = computed(() => [
	{ label: __("Forms"), onClick: () => emit("back") },
	...(ready.value
		? [{ label: props.draft.form.title || __("Untitled form"), onClick: () => {} }]
		: []),
]);

const publishMenu = computed(() => {
	if (!ready.value) return [];
	const { form, dirty, publish, unpublish } = props.draft;
	if (!form.published) {
		const label = dirty ? __("Save and publish") : __("Publish");
		return [{ label, icon: "lucide-globe", onClick: publish }];
	}
	const url = `${window.location.origin}/crm-form/${props.draft.savedRoute}`;
	return [
		{
			group: __("Link"),
			hideLabel: true,
			options: [
				{ label: __("Open form"), icon: "lucide-external-link", onClick: () => window.open(url) },
				{ label: __("Copy link"), icon: "lucide-link", onClick: () => copyToClipboard(url) },
			],
		},
		{
			group: __("Status"),
			hideLabel: true,
			options: [{ label: __("Unpublish"), icon: "lucide-eye-off", onClick: unpublish }],
		},
	];
});
</script>
