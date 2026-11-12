<template>
	<div class="flex flex-col text-ink-gray-8">
		<div class="flex flex-col">
			<div v-if="forms.loading && !forms.data" class="flex items-center justify-center mt-12">
				<LoadingIndicator class="w-4" />
			</div>
			<ErrorMessage v-else-if="forms.error" :message="forms.error" />
			<div
				v-else-if="forms.data?.length === 0"
				class="flex flex-col items-center gap-1 py-12 text-center"
			>
				<span class="lucide-text-cursor-input size-6 text-ink-gray-4" aria-hidden="true" />
				<p class="text-base-medium text-ink-gray-7">{{ __("No web forms yet") }}</p>
				<p class="text-p-base text-ink-gray-5">{{ __("Create one to start capturing leads.") }}</p>
			</div>
			<FrappeList
				v-else
				divider="inset"
				:columns="COLUMNS"
				:row-height="40"
				class="-mx-2 pt-2"
				style="--list-row-padding-x: 0.5rem; --list-gap: 1rem"
			>
				<ListHeader>
					<ListHeaderCell>{{ __("Form") }}</ListHeaderCell>
					<ListHeaderCell>{{ __("Maps to") }}</ListHeaderCell>
					<ListHeaderCell>{{ __("Status") }}</ListHeaderCell>
					<div role="columnheader" aria-hidden="true" />
				</ListHeader>
				<ListRow
					v-for="form in forms.data"
					:key="form.name"
					:route="{ query: { form: form.name } }"
				>
					<ListCell class="gap-2">
						<div class="max-w-[60%] truncate text-base-medium text-ink-gray-8">
							{{ form.title }}
						</div>
						<div class="min-w-0 truncate text-base text-ink-gray-5">
							/crm-form/{{ form.route }}
						</div>
					</ListCell>
					<ListCell>
						<div class="truncate text-base text-ink-gray-8">
							{{ docLabel(form.document_type) }}
						</div>
					</ListCell>
					<ListCell>
						<Badge
							:theme="form.published ? 'green' : 'gray'"
							variant="outline"
							size="md"
							:label="form.published ? __('Published') : __('Draft')"
						/>
					</ListCell>
					<ListCell>
						<div class="flex w-full justify-end" @click.stop.prevent>
							<Dropdown align="end" :options="rowOptions(form)">
								<Button
									icon="lucide-more-horizontal"
									variant="ghost"
									:aria-label="__('More actions')"
								/>
							</Dropdown>
						</div>
					</ListCell>
				</ListRow>
			</FrappeList>
		</div>
	</div>

	<!-- create dialog -->
	<Dialog v-model:open="showCreate" :title="__('New form')">
		<template #default>
			<div class="flex flex-col gap-4">
				<FormControl
					v-model="draft.title"
					type="text"
					:label="__('Title')"
					:placeholder="__('Contact sales')"
					@input="onTitleInput"
				/>
				<FormControl
					v-model="draft.document_type"
					type="select"
					:label="__('Maps to')"
					:options="targetOptions"
				/>
				<div>
					<div class="mb-1.5 text-sm text-ink-gray-5">{{ __("Route") }}</div>
					<div
						class="flex h-7 cursor-text items-center rounded-4 border border-transparent bg-surface-gray-2 px-2.5 text-base transition-colors hover:bg-surface-gray-3 focus-within:border-outline-gray-4 focus-within:bg-surface-base"
						@click="focusRouteEnd"
					>
						<span class="shrink-0 text-ink-gray-4">/crm-form/</span>
						<input
							v-model="draft.route"
							:placeholder="__('contact-sales')"
							class="min-w-0 flex-1 border-0 bg-transparent p-0 text-base text-ink-gray-8 placeholder:text-ink-gray-4 focus:outline-none focus:ring-0"
							@input="routeEdited = true"
						/>
					</div>
				</div>
				<ErrorMessage v-if="createError" :message="createError" />
			</div>
		</template>
		<template #actions>
			<Button
				class="w-full"
				variant="solid"
				:label="__('Create form')"
				:loading="creating"
				@click="createForm"
			/>
		</template>
	</Dialog>
</template>

<script setup>
import {
	Button,
	Badge,
	Dropdown,
	Dialog,
	FormControl,
	ErrorMessage,
	LoadingIndicator,
	dialog,
	toast,
} from "frappe-ui";
import { List as FrappeList, ListCell, ListHeader, ListHeaderCell, ListRow } from "frappe-ui/list";
import { __ } from "frappe/i18n";
import { computed, reactive, ref } from "vue";
import { call, copyToClipboard, errorText } from "./formsApi";

defineOptions({ inheritAttrs: false });
const emit = defineEmits(["open"]);

const targetOptions = [
	{ label: "Lead", value: "CRM Lead" },
	{ label: "Deal", value: "CRM Deal" },
];
const docLabel = (dt) => targetOptions.find((o) => o.value === dt)?.label || dt;

const COLUMNS = ["minmax(0, 6fr)", "minmax(0, 3fr)", "minmax(0, 3fr)", "2rem"];

const forms = reactive({ data: null, loading: false, error: "" });

async function loadForms() {
	forms.loading = true;
	try {
		forms.data = await call("list_forms");
		forms.error = "";
	} catch (e) {
		forms.error = errorText(e, __("Could not load forms"));
	} finally {
		forms.loading = false;
	}
}
loadForms();

// create dialog: title, maps-to and route captured up front (maps-to governs
// which fields are available, so it's a first-class creation choice)
const showCreate = ref(false);
const creating = ref(false);
const createError = ref("");
const draft = reactive({ title: "", route: "", document_type: "CRM Lead" });
let routeEdited = false;

function slugify(v) {
	return (v || "")
		.toString()
		.trim()
		.toLowerCase()
		.replace(/[^a-z0-9]+/g, "-")
		.replace(/^-+|-+$/g, "");
}
function openCreate() {
	draft.title = "";
	draft.route = "";
	draft.document_type = "CRM Lead";
	routeEdited = false;
	createError.value = "";
	showCreate.value = true;
}
function onTitleInput(e) {
	if (!routeEdited) draft.route = slugify(e?.target?.value ?? draft.title);
}
// clicking the /crm-form/ prefix or box padding focuses the slug at the end
function focusRouteEnd(e) {
	if (e.target.tagName === "INPUT") return;
	const input = e.currentTarget.querySelector("input");
	if (!input) return;
	input.focus();
	input.setSelectionRange(input.value.length, input.value.length);
}
async function createForm() {
	createError.value = "";
	const route = slugify(draft.route || draft.title);
	if (!draft.title || !route) {
		createError.value = __("Title and route are required");
		return;
	}
	creating.value = true;
	try {
		const doc = await call("save_form", {
			name: null,
			form: { title: draft.title, route, document_type: draft.document_type },
		});
		showCreate.value = false;
		emit("open", doc.name);
		loadForms();
		toast.success(__("Form created"));
	} catch (e) {
		createError.value = e?.messages?.[0] || e?.message || __("Could not create form");
	} finally {
		creating.value = false;
	}
}

async function togglePublished(form, value) {
	try {
		await call("set_published", {
			name: form.name,
			published: value ? 1 : 0,
		});
		form.published = value ? 1 : 0;
		toast.success(value ? __("Form published") : __("Form unpublished"));
	} catch (e) {
		loadForms();
		toast.error(errorText(e, __("Could not update form")));
	}
}

function copyLink(form) {
	copyToClipboard(`${window.location.origin}/crm-form/${form.route}`);
}

function confirmDelete(form) {
	dialog.confirm({
		title: __("Delete {0}?", [form.title]),
		message: __("The public link stops working. This cannot be undone."),
		confirmLabel: __("Delete"),
		theme: "red",
		onConfirm: async () => {
			await call("delete_form", { name: form.name });
			loadForms();
			toast.success(__("Form deleted"));
		},
	});
}

function rowOptions(form) {
	return [
		{
			label: __("Edit"),
			icon: "lucide-edit-2",
			onClick: () => emit("open", form.name),
		},
		{
			label: form.published ? __("Unpublish") : __("Publish"),
			icon: form.published ? "lucide-eye-off" : "lucide-eye",
			onClick: () => togglePublished(form, !form.published),
		},
		{
			label: __("Copy link"),
			icon: "lucide-link",
			onClick: () => copyLink(form),
		},
		{
			label: __("Delete"),
			icon: "lucide-trash-2",
			theme: "red",
			onClick: () => confirmDelete(form),
		},
	];
}

defineExpose({ reload: loadForms, openCreate, failed: computed(() => Boolean(forms.error)) });
</script>
