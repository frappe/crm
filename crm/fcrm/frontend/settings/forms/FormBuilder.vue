<template>
	<div class="flex flex-col text-ink-gray-8">
		<!-- header -->
		<div class="flex items-center justify-between py-3">
			<div class="flex items-center gap-2">
				<Button
					variant="ghost"
					icon-left="lucide-chevron-left"
					:label="form.title || __('Untitled')"
					size="md"
					class="-ml-4 cursor-pointer !max-w-96 !justify-start !pr-0 text-lg-semibold text-ink-gray-7 no-underline hover:bg-transparent hover:no-underline hover:opacity-70 focus:bg-transparent focus:outline-none focus:ring-0"
					@click="goBack"
				/>
				<Badge v-if="dirty" variant="subtle" theme="amber" size="sm" :label="__('Not Saved')" />
			</div>
			<div v-if="loaded" class="flex items-center gap-4">
				<div class="flex items-center justify-between gap-2 h-7" @click="togglePublish">
					<Switch size="sm" :model-value="Boolean(form.published)" />
					<span class="text-sm text-ink-gray-7">{{ __("Publish") }}</span>
				</div>
				<Button
					:label="mode === 'edit' ? __('Preview') : __('Edit')"
					@click="(mode = mode === 'edit' ? 'preview' : 'edit'), resetPreview()"
				>
					<template #prefix>
						<span class="lucide-eye h-4 w-4" aria-hidden="true" v-if="mode === 'edit'" />
						<span class="lucide-pencil h-4 w-4" aria-hidden="true" v-else />
					</template>
				</Button>
				<Button
					:disabled="!dirty"
					:label="__('Save')"
					theme="gray"
					variant="solid"
					:loading="saving"
					@click="saveNow"
				/>
			</div>
		</div>

		<ErrorMessage v-if="loadError" class="py-3.5" :message="loadError" />
		<div v-if="loaded" class="pb-6">
			<!-- EDIT MODE -->
			<div v-if="mode === 'edit'" class="wf-tabs">
				<Tabs v-model="activeTab" as="div" :tabs="tabs">
					<template #tab-panel="{ tab }">
						<!-- EDITOR TAB -->
						<div v-if="tab.value === 'editor'" class="pt-5">
							<!-- form masthead (title + description) — typed right on the canvas -->
							<div class="mb-5 px-1">
								<input
									v-model="form.title"
									:placeholder="__('Form title')"
									class="w-full border-0 bg-transparent p-0 text-2xl font-semibold leading-tight text-ink-gray-9 placeholder:text-ink-gray-4 focus:outline-none focus:ring-0"
									@input="onTitleInput"
								/>
								<textarea
									ref="descInput"
									v-model="form.description"
									:placeholder="__('Add a description to help people fill out this form')"
									rows="1"
									class="mt-2 w-full resize-none border-0 bg-transparent p-0 text-base leading-relaxed text-ink-gray-6 placeholder:text-ink-gray-4 focus:outline-none focus:ring-0"
									@input="(e) => (autoGrow(e.target), markDirty())"
								/>
								<hr class="mt-5 border-outline-gray-2" />
							</div>

							<!-- native-style layout: draggable section boxes → dashed columns → field cards -->
							<div class="flex flex-col gap-3" :class="{ 'select-none': dragging }">
								<Draggable
									:list="sections"
									:item-key="sectionKey"
									handle=".section-handle"
									group="wf-sections"
									class="flex flex-col gap-3"
									ghost-class="opacity-40"
									:force-fallback="true"
									:fallback-on-body="false"
									fallback-class="wf-drag-fallback"
									:animation="120"
									@start="dragging = true"
									@end="onSortEnd"
								>
									<template #item="{ element: sec }">
										<div class="flex flex-col gap-1.5 rounded-4 bg-surface-gray-2 p-2.5">
											<div class="flex h-7 items-center justify-between">
												<div class="flex items-center gap-2 text-base-medium text-ink-gray-9">
													<span
														class="lucide-grip-vertical section-handle h-3.5 shrink-0 cursor-grab text-ink-gray-3"
														aria-hidden="true"
													/>
													<input
														v-if="sec.editingLabel"
														:ref="(el) => el && el.focus()"
														v-model="sec.secField.label"
														:placeholder="__('Section title')"
														class="min-w-0 flex-1 border-0 bg-transparent p-0 text-base-medium text-ink-gray-9 placeholder:font-normal placeholder:italic placeholder:text-ink-gray-4 focus:outline-none focus:ring-0"
														@blur="sec.editingLabel = false"
														@keydown.enter="sec.editingLabel = false"
														@input="markDirty"
													/>
													<span
														v-else
														class="cursor-text truncate"
														:class="{
															'italic text-ink-gray-4': !sec.secField.label,
														}"
														@click="sec.editingLabel = true"
													>
														{{ sec.secField.label || __("Section title") }}
													</span>
												</div>
												<div class="flex items-center gap-1.5">
													<span
														v-if="sectionFieldCount(sec)"
														class="rounded-4 bg-surface-gray-3 px-1.5 py-0.5 text-xs leading-none text-ink-gray-4"
													>
														{{ sectionFieldCount(sec) }}
														{{ sectionFieldCount(sec) === 1 ? __("field") : __("fields") }}
													</span>
													<Dropdown :options="sectionMenu(sec)">
														<template #default>
															<Button variant="ghost">
																<span class="lucide-more-horizontal h-4" aria-hidden="true" />
															</Button>
														</template>
													</Dropdown>
												</div>
											</div>
											<div class="flex gap-2">
												<div
													v-for="col in sec.columns"
													:key="columnKey(col)"
													class="flex min-w-0 flex-1 flex-col gap-1.5 rounded-4 border border-dashed border-outline-gray-2 bg-surface-elevation-2 p-2"
												>
													<Draggable
														:list="col.items"
														group="wf-fields"
														item-key="fieldname"
														handle=".drag-handle"
														class="flex min-h-[34px] min-w-0 flex-1 flex-col gap-1.5"
														ghost-class="opacity-40"
														:force-fallback="true"
														:fallback-on-body="false"
														fallback-class="wf-drag-fallback"
														:animation="120"
														@start="dragging = true"
														@end="onSortEnd"
													>
														<template #item="{ element: f }">
															<FieldCard
																:field="f"
																:expanded="expanded === f.fieldname"
																:locked="isMandatory(f.fieldname)"
																:guest-select-missing="
																	f.fieldtype === 'Link' && guestSelect[f.options] === false
																"
																:granting="!!grantingSelect[f.options]"
																@open="open(f)"
																@toggle="toggle(f)"
																@remove="removeField(f)"
																@update="(patch) => updateField(f, patch)"
																@grant-guest="grantGuestSelect(f.options)"
															/>
														</template>
													</Draggable>
													<Combobox
														:options="availableFieldOptions"
														:model-value="null"
														:placeholder="__('Search fields…')"
														@update:selected-option="(e) => addFieldToColumn(col, e)"
													>
														<template #trigger="{ open, setOpen }">
															<Button
																class="!h-8 w-full !bg-surface-elevation-2"
																variant="outline"
																:label="__('Add Field')"
																icon-left="lucide-plus"
																@click="openFieldPicker(open, setOpen)"
															/>
														</template>
													</Combobox>
												</div>
											</div>
										</div>
									</template>
								</Draggable>

								<Button
									class="!h-8 w-full"
									variant="subtle"
									:label="__('Add Section')"
									icon-left="lucide-plus"
									@click="addBreak('Section Break')"
								/>
							</div>

							<!-- hidden required fields: kept off the form, a default is applied
                   on submission so the record can still be created -->
							<div v-if="hiddenFields.length" class="mt-6">
								<div class="mb-2 flex items-center gap-1.5 text-base-medium text-ink-gray-7">
									<span class="lucide-eye-off h-3.5 w-3.5 text-ink-gray-5" aria-hidden="true" />
									{{ __("Hidden required fields") }}
								</div>
								<div class="rounded-4 bg-surface-gray-2 p-2.5">
									<p class="mb-2.5 text-p-sm text-ink-gray-5">
										{{
											__(
												"These fields aren't shown to users. Default values are used when the form is submitted."
											)
										}}
									</p>
									<div class="flex flex-col gap-2">
										<div
											v-for="h in hiddenFields"
											:key="h.fieldname"
											class="flex items-center gap-2.5 rounded-4 border border-outline-gray-2 bg-surface-elevation-2 px-2.5 py-2"
										>
											<span
												:class="[fieldTypeIcon(h), 'h-4 w-4 shrink-0 text-ink-gray-5']"
												aria-hidden="true"
											/>
											<span class="flex-1 truncate text-base text-ink-gray-8" :title="h.label">{{
												h.label
											}}</span>
											<div class="w-52 shrink-0">
												<FormControl
													v-if="hiddenIsSelect(h)"
													type="select"
													size="sm"
													:modelValue="h.default"
													:options="hiddenSelectOptions(h)"
													@update:modelValue="(v) => ((h.default = v), markDirty())"
												/>
												<FormControl
													v-else
													type="text"
													size="sm"
													:modelValue="h.default"
													:placeholder="__('Default value')"
													@update:modelValue="(v) => ((h.default = v), markDirty())"
												/>
											</div>
										</div>
									</div>
									<ErrorMessage
										v-if="hiddenMissingDefault"
										class="mt-2"
										:message="__('Set a default value for each field to publish this form.')"
									/>
								</div>
							</div>
						</div>

						<!-- SETTINGS TAB -->
						<div v-else-if="tab.value === 'settings'" class="flex flex-col pt-5">
							<!-- form details -->
							<div>
								<div class="flex flex-col gap-1">
									<span class="text-lg-semibold text-ink-gray-8">{{ __("Form details") }}</span>
									<span class="text-p-sm text-ink-gray-6">{{
										__("Basic settings for this form.")
									}}</span>
								</div>
								<div class="mt-3.5 flex flex-col gap-4">
									<div class="grid grid-cols-2 gap-4">
										<div>
											<div class="mb-1.5 text-sm text-ink-gray-5">
												{{ __("Route") }}
											</div>
											<div
												class="flex h-7 cursor-text items-center rounded-4 border border-transparent bg-surface-gray-2 px-2.5 text-base transition-colors hover:bg-surface-gray-3 focus-within:border-outline-gray-4 focus-within:bg-surface-base"
												@click="focusRouteEnd"
											>
												<span class="shrink-0 text-ink-gray-4">/crm-form/</span>
												<input
													v-model="form.route"
													class="min-w-0 flex-1 border-0 bg-transparent p-0 text-base text-ink-gray-8 placeholder:text-ink-gray-4 focus:outline-none focus:ring-0"
													@input="(routeEdited = true), markDirty()"
													@blur="form.route = slugify(form.route)"
												/>
											</div>
										</div>
										<FormControl
											v-model="doctypeModel"
											type="select"
											:label="__('Maps to')"
											:options="targetOptions"
										/>
										<FormControl
											v-model="form.submit_button_label"
											type="text"
											:label="__('Submit button label')"
											@input="markDirty"
										/>
									</div>
									<FormControl
										v-model="form.success_message"
										type="textarea"
										:label="__('Success message')"
										:rows="4"
										:placeholder="__('Shown after a successful submission')"
										@input="markDirty"
									/>
									<div>
										<FormControl
											v-model="form.redirect_url"
											type="text"
											:label="__('Redirect URL')"
											:placeholder="__('https://example.com/thank-you')"
											@input="markDirty"
										/>
										<p class="mt-1.5 text-p-sm text-ink-gray-5">
											{{
												__(
													"Send visitors here after they submit. Leave blank to show the success message."
												)
											}}
										</p>
									</div>
								</div>
							</div>
						</div>

						<!-- SHARE TAB -->
						<div v-else class="flex flex-col pt-5">
							<p v-if="!form.published" class="mb-5 text-p-sm text-ink-gray-5">
								{{
									__(
										"This form isn’t published yet. Turn on Publish to make the link and embeds live."
									)
								}}
							</p>

							<!-- link -->
							<div>
								<div class="flex flex-col gap-1">
									<span class="text-lg-semibold text-ink-gray-8">{{ __("Link") }}</span>
									<span class="text-p-sm text-ink-gray-6">{{
										__("Send people straight to the hosted form.")
									}}</span>
								</div>
								<div class="mt-3.5 flex items-center gap-2">
									<TextInput class="flex-1" size="sm" readonly :modelValue="publicUrl">
										<template #suffix>
											<button
												class="flex text-ink-gray-5 transition-colors hover:text-ink-gray-8"
												:title="__('Copy link')"
												@click="copyToClipboard(publicUrl)"
											>
												<span class="lucide-copy h-4 w-4" aria-hidden="true" />
											</button>
										</template>
									</TextInput>
									<a :href="publicUrl" target="_blank">
										<Button :label="__('Open')">
											<template #prefix
												><span class="lucide-external-link h-4 w-4" aria-hidden="true"
											/></template>
										</Button>
									</a>
								</div>
							</div>

							<hr class="my-8 border-outline-gray-2" />

							<!-- embed -->
							<div>
								<div class="flex flex-col gap-1">
									<span class="text-lg-semibold text-ink-gray-8">{{ __("Embed") }}</span>
									<span class="text-p-sm text-ink-gray-6">{{
										__("Drop the form into your own website.")
									}}</span>
								</div>

								<div class="mt-3.5 flex flex-col gap-5">
									<!-- iframe (isolated) -->
									<div>
										<div class="mb-1 text-base text-ink-gray-5">
											{{ __("iframe") }}
										</div>
										<p class="mb-2 text-p-sm text-ink-gray-5">
											{{
												__(
													"Sandboxed in a frame. Simplest, but a fixed height and its own styling."
												)
											}}
										</p>
										<div class="relative">
											<textarea
												readonly
												rows="3"
												class="w-full resize-none rounded-5 border border-outline-gray-2 bg-surface-gray-1 py-2 pl-3 pr-10 font-mono text-xs text-ink-gray-7 focus:border-outline-gray-4 focus:outline-none focus:ring-0 focus-visible:outline-none"
												:value="iframeSnippet"
											/>
											<button
												class="absolute right-2 top-2 flex text-ink-gray-5 transition-colors hover:text-ink-gray-8"
												:title="__('Copy')"
												@click="copyToClipboard(iframeSnippet)"
											>
												<span class="lucide-copy h-4 w-4" aria-hidden="true" />
											</button>
										</div>
									</div>
								</div>
							</div>

							<hr class="my-8 border-outline-gray-2" />

							<!-- allowed domains -->
							<div>
								<div class="flex flex-col gap-1">
									<span class="text-lg-semibold text-ink-gray-8">{{ __("Allowed domains") }}</span>
									<span class="text-p-sm text-ink-gray-6">
										{{
											__(
												"Sites where this form may be embedded, one per line. Browsers block the iframe on any site not listed here."
											)
										}}
									</span>
								</div>
								<textarea
									v-model="form.allowed_embedding_domains"
									rows="3"
									spellcheck="false"
									placeholder="https://www.example.com"
									class="mt-3.5 w-full resize-none rounded-5 border border-outline-gray-2 px-3 py-2 font-mono text-xs text-ink-gray-8 focus:border-outline-gray-4 focus:outline-none focus:ring-0 focus-visible:outline-none"
									@input="markDirty"
								/>
								<p v-if="invalidEmbeddingDomains.length" class="mt-1.5 text-xs text-ink-red-5">
									{{
										__("Not a valid domain and will be ignored: {0}", [
											invalidEmbeddingDomains.join(", "),
										])
									}}
								</p>
								<p v-else-if="!embeddingDomains.length" class="mt-1.5 text-xs text-ink-gray-5">
									{{
										__("No domains added. The embed will only work on this site until you add one.")
									}}
								</p>
							</div>
						</div>
					</template>
				</Tabs>
			</div>

			<!-- PREVIEW MODE -->
			<div v-else class="max-w-2xl pt-6">
				<div class="rounded-7 border bg-surface-white p-7">
					<!-- simulated success screen -->
					<div v-if="previewSubmitted" class="flex flex-col items-center gap-3 py-10 text-center">
						<div
							class="flex h-12 w-12 items-center justify-center rounded-full bg-surface-green-2 text-ink-green-2"
						>
							<span class="lucide-check h-6 w-6" aria-hidden="true" />
						</div>
						<div class="text-lg font-semibold text-ink-gray-9">
							{{ form.success_message || __("Thank you!") }}
						</div>
						<Button :label="__('Preview again')" @click="resetPreview" />
					</div>

					<template v-else>
						<!-- mirror the public page (crm_form.html): 20px title, ~14px gap -->
						<div class="text-xl font-semibold text-ink-gray-9">
							{{ form.title || __("Form title") }}
						</div>
						<div v-if="form.description" class="mt-3.5 whitespace-pre-wrap text-sm text-ink-gray-6">
							{{ form.description }}
						</div>
						<div class="mt-5 flex flex-col gap-5">
							<div v-for="(section, si) in layout" :key="si">
								<div v-if="section.label" class="mb-3 text-sm font-semibold text-ink-gray-8">
									{{ section.label }}
								</div>
								<div
									class="grid gap-x-5"
									:style="{
										gridTemplateColumns: `repeat(${section.columns.length}, minmax(0,1fr))`,
									}"
								>
									<div v-for="(col, ci) in section.columns" :key="ci" class="flex flex-col gap-4">
										<div v-show="fieldVisible(f)" v-for="f in col" :key="f.fieldname">
											<div v-if="f.fieldtype !== 'Check'" class="mb-1.5 text-sm text-ink-gray-5">
												{{ f.label }}<span v-if="fieldRequired(f)" class="text-ink-red-4">*</span>
											</div>
											<FormControl
												v-if="TEXTAREA_TYPES.includes(f.fieldtype)"
												v-model="previewModel[f.fieldname]"
												type="textarea"
												:placeholder="f.placeholder"
												:disabled="fieldReadOnly(f)"
											/>
											<FormControl
												v-else-if="f.fieldtype === 'Select'"
												v-model="previewModel[f.fieldname]"
												type="select"
												:options="selectOptions(f)"
												:placeholder="f.placeholder || __('Select an option')"
												:disabled="fieldReadOnly(f)"
											/>
											<FormControl
												v-else-if="f.fieldtype === 'Link'"
												v-model="previewModel[f.fieldname]"
												type="select"
												:options="linkSelectOptions(f)"
												:placeholder="f.placeholder || __('Select an option')"
												:disabled="fieldReadOnly(f)"
											/>
											<div v-else-if="f.fieldtype === 'Check'" class="flex items-center gap-2">
												<FormControl
													v-model="previewModel[f.fieldname]"
													type="checkbox"
													:disabled="fieldReadOnly(f)"
												/>
												<span class="text-sm text-ink-gray-5"
													>{{ f.label
													}}<span v-if="fieldRequired(f)" class="text-ink-red-4">*</span></span
												>
											</div>
											<FormControl
												v-else
												v-model="previewModel[f.fieldname]"
												:type="inputType(f)"
												:placeholder="f.placeholder"
												:disabled="fieldReadOnly(f)"
											/>
											<div v-if="f.field_description" class="mt-1 text-sm text-ink-gray-4">
												{{ f.field_description }}
											</div>
										</div>
									</div>
								</div>
							</div>
							<div v-if="!inputFieldCount" class="text-sm text-ink-gray-4">
								{{ __("Add fields to see them here.") }}
							</div>
							<div class="mt-1 flex justify-end gap-2.5">
								<Button variant="subtle" size="md" :label="__('Discard')" @click="resetPreview" />
								<Button
									variant="solid"
									size="md"
									:label="form.submit_button_label || __('Submit')"
									@click="previewSubmitted = true"
								/>
							</div>
						</div>
					</template>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import {
	Badge,
	Button,
	Switch,
	Combobox,
	Tabs,
	TextInput,
	FormControl,
	Dropdown,
	ErrorMessage,
	dialog,
	toast,
} from "frappe-ui";
import { __ } from "frappe/i18n";
import FieldCard from "./FieldCard.vue";
import { evaluateRule } from "./conditionalRule";
import { call, copyToClipboard, errorText, recordNames } from "./formsApi";
import { fieldTypeIcon } from "./fieldTypeIcon";
import Draggable from "vuedraggable";
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount } from "vue";

const BREAK_TYPES = ["Section Break", "Column Break"];

const props = defineProps({
	name: { type: String, required: true },
	router: { type: Object, default: null },
});
const emit = defineEmits(["back", "saved"]);

const targetOptions = [
	{ label: "Lead", value: "CRM Lead" },
	{ label: "Deal", value: "CRM Deal" },
];
const docLabel = (dt) => targetOptions.find((o) => o.value === dt)?.label || dt;

const loaded = ref(false);
const loadError = ref("");
const saving = ref(false);
const dirty = ref(false);

const mode = ref("edit"); // edit | preview
const activeTab = ref("editor");
const tabs = [
	{ value: "editor", label: __("Editor"), iconLeft: "lucide-layout-list" },
	{ value: "settings", label: __("Settings"), iconLeft: "lucide-settings" },
	{ value: "share", label: __("Share"), iconLeft: "lucide-share-2" },
];
const expanded = ref(null); // fieldname of the expanded field editor
const descInput = ref(null);
// while a draft still has an auto-generated route, keep it in sync with the
// title; once the user edits the route (or the form is published) we stop
const routeEdited = ref(false);

function slugify(v) {
	return (v || "")
		.toString()
		.trim()
		.toLowerCase()
		.replace(/[^a-z0-9]+/g, "-")
		.replace(/^-+|-+$/g, "");
}

function onTitleInput() {
	if (!routeEdited.value && !form.published) form.route = slugify(form.title);
	markDirty();
}

// clicking the /crm-form/ prefix or the box padding focuses the slug input with
// the caret at the end (not the start)
function focusRouteEnd(e) {
	if (e.target.tagName === "INPUT") return;
	const input = e.currentTarget.querySelector("input");
	if (!input) return;
	input.focus();
	input.setSelectionRange(input.value.length, input.value.length);
}

// keep the description textarea sized to its content
function autoGrow(el) {
	if (!el) return;
	el.style.height = "auto";
	el.style.height = el.scrollHeight + "px";
}
// Robustly size the description box: measure on an animation frame (after layout),
// and if the box isn't laid out yet — it lives in a lazily-rendered Tabs panel, so
// on re-navigation it can be briefly zero-width/hidden — retry on the next frame.
// Without this, opening a saved multi-line description shows only the first line.
function sizeDescription(tries = 0) {
	requestAnimationFrame(() => {
		const el = descInput.value;
		if (!el) return;
		if (!el.clientWidth && tries < 20) return sizeDescription(tries + 1);
		autoGrow(el);
	});
}
const dragging = ref(false);

// Editing model: form.fields (flat) is the source of truth, derived into a
// draggable list of sections, each holding columns of field items. Every
// section (including the first) is a real Section Break, so they all behave
// identically. After any drag / structural change we re-flatten to form.fields.
const sections = ref([]);

// doctype-mandatory fields removed from the visible form. Each carries a default
// value that's applied on submission so the record can still be created.
const hiddenFields = ref([]);

// fieldnames the target doctype marks mandatory (from the field catalog). They
// stay in the form: the server only accepts system-managed fields as hidden.
const mandatorySet = computed(
	() => new Set((availableFields.data || []).filter((f) => f.reqd).map((f) => f.fieldname))
);
function isMandatory(fieldname) {
	return mandatorySet.value.has(fieldname);
}
// true while any hidden required field is missing its default (blocks publish)
const hiddenMissingDefault = computed(() =>
	hiddenFields.value.some((h) => !String(h.default || "").trim())
);
function hiddenIsSelect(h) {
	return h.fieldtype === "Select" || h.fieldtype === "Link";
}
function hiddenSelectOptions(h) {
	let opts = [];
	if (h.fieldtype === "Select") {
		opts = (h.options || "").split("\n").filter(Boolean);
	} else if (h.fieldtype === "Link") {
		opts = linkOptions[h.options] || [];
	}
	opts = opts.slice();
	if (h.default && !opts.includes(h.default)) opts.unshift(h.default);
	return opts.map((o) => ({ label: o, value: o }));
}

// cache of Link option lists (e.g. CRM Lead Status names) for hidden Link fields
const linkOptions = reactive({});
async function ensureLinkOptions(doctype) {
	if (!doctype || linkOptions[doctype]) return;
	linkOptions[doctype] = [];
	try {
		linkOptions[doctype] = await recordNames(doctype);
	} catch {
		linkOptions[doctype] = [];
	}
}

// per target doctype: can a guest select it? Drives the Link-field warning in
// FieldCard. Fail-open on error so a failed check doesn't nag.
const guestSelect = reactive({});
const grantingSelect = reactive({});
async function ensureGuestSelect(doctype) {
	if (!doctype || doctype in guestSelect) return;
	guestSelect[doctype] = true;
	try {
		const res = await call("link_field_guest_access", { doctype });
		guestSelect[doctype] = !!res?.guest_can_select;
	} catch {
		guestSelect[doctype] = true;
	}
}
// the grant is site-wide, not scoped to this form, so the author confirms it by name
let grantConfirmOpen = false;
function grantGuestSelect(doctype) {
	if (!doctype || grantingSelect[doctype] || grantConfirmOpen) return;
	grantConfirmOpen = true;
	dialog.confirm({
		title: __("Give Guest access to {0}?", [doctype]),
		message: __(
			"Guest gets the Select permission on {0} for the whole site. Anyone, signed in or not, can then search and list all {0} records with their names, titles and owners, not only through this form.",
			[doctype]
		),
		confirmLabel: __("Grant"),
		cancelLabel: __("Cancel"),
		onConfirm: () => {
			grantConfirmOpen = false;
			return grantGuestSelectNow(doctype);
		},
		onCancel: () => (grantConfirmOpen = false),
	});
}
async function grantGuestSelectNow(doctype) {
	grantingSelect[doctype] = true;
	try {
		const res = await call("grant_guest_link_access", { doctype });
		guestSelect[doctype] = !!res?.guest_can_select;
		if (guestSelect[doctype]) {
			// records are now guest-visible — refresh the preview dropdown
			delete linkOptions[doctype];
			ensureLinkOptions(doctype);
			toast.success(__("Guests can now select {0} records.", [doctype]));
		}
	} catch (e) {
		toast.error(e?.messages?.[0] || __("Could not grant guest access."));
	} finally {
		grantingSelect[doctype] = false;
	}
}
// resolve both the preview options and the guest-access state for a Link target
function ensureLinkMeta(doctype) {
	ensureLinkOptions(doctype);
	ensureGuestSelect(doctype);
}

function newColumn(colField = null) {
	return { colField, items: [] };
}

function newSection(secField = null) {
	return {
		secField: secField || makeMarker("Section Break"),
		columns: [newColumn()],
		editingLabel: false,
	};
}

function rebuildModel() {
	const secs = [];
	let cur = null;
	const ensureSection = () => {
		// fields before the first explicit Section Break get a synthesized one so
		// the first section is a normal, draggable section like the rest
		if (!cur) {
			cur = newSection();
			secs.push(cur);
		}
		return cur;
	};
	for (const f of form.fields || []) {
		if (f.fieldtype === "Section Break") {
			cur = newSection(f);
			secs.push(cur);
		} else if (f.fieldtype === "Column Break") {
			ensureSection().columns.push(newColumn(f));
		} else {
			const sec = ensureSection();
			sec.columns[sec.columns.length - 1].items.push(f);
		}
	}
	if (!secs.length) secs.push(newSection()); // empty form → one empty section
	sections.value = secs;
}

// emit a container's columns, normalising column-break markers to position
function emitColumns(out, cols) {
	cols.forEach((col, i) => {
		if (i === 0) {
			col.colField = null;
		} else if (!col.colField) {
			col.colField = makeMarker("Column Break");
		}
		if (col.colField) out.push(col.colField);
		for (const f of col.items) out.push(f);
	});
}

function flattenModel() {
	const out = [];
	for (const sec of sections.value) {
		out.push(sec.secField);
		emitColumns(out, sec.columns);
	}
	return out;
}

function syncFromModel() {
	form.fields = flattenModel();
	markDirty();
}

function onSortEnd() {
	dragging.value = false;
	syncFromModel();
}

// vuedraggable item-keys
const sectionKey = (sec) => sec.secField?.fieldname || "sec";
const columnKey = (col) => col.colField?.fieldname || "col0";
const previewModel = reactive({}); // throwaway values so the preview is interactive

// the public page's fallbacks: a rule that does not parse shows the field, and does not require or lock it
const fieldVisible = (f) => evaluateRule(f.depends_on, previewModel, true);
const fieldRequired = (f) =>
	f.reqd ? true : evaluateRule(f.mandatory_depends_on, previewModel, false);
const fieldReadOnly = (f) => evaluateRule(f.read_only_depends_on, previewModel, false);
const previewSubmitted = ref(false);

function resetPreview() {
	previewSubmitted.value = false;
	Object.keys(previewModel).forEach((k) => delete previewModel[k]);
}

const form = reactive({
	name: props.name,
	title: "",
	route: "",
	document_type: "CRM Lead",
	description: "",
	submit_button_label: "Submit",
	success_message: "",
	redirect_url: "",
	allowed_embedding_domains: "",
	published: 0,
	fields: [],
});

// Keep the description box sized to its text. flush:'post' runs after the DOM
// settles, so it fires whenever the textarea actually mounts (initial load, or
// re-entering Edit — it lives inside a lazily-rendered Tabs panel) or its content
// changes — no more 1-row box scrolled to the last line.
watch([descInput, () => form.description], () => sizeDescription(), {
	flush: "post",
});
// re-measure once web fonts load: scrollHeight with the fallback font wraps wrong
onMounted(() => document.fonts?.ready?.then(() => sizeDescription()));

const publicUrl = computed(() => `${window.location.origin}/crm-form/${form.route}`);
const embeddingDomains = computed(() =>
	(form.allowed_embedding_domains || "").split(/\s+/).filter(Boolean)
);
// mirror the server's ALLOWED_EMBEDDING_DOMAIN_RE (crm/www/crm_form.py): bare host,
// optional scheme/port, optional leading "*." wildcard. Anything else is dropped
// from the CSP header server-side, so flag it here instead of failing silently.
const EMBEDDING_DOMAIN_RE =
	/^(https?:\/\/)?(\*\.)?[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?(?::\d+)?$/;
const invalidEmbeddingDomains = computed(() =>
	embeddingDomains.value.filter((d) => !EMBEDDING_DOMAIN_RE.test(d))
);

const escapeAttr = (text) => text.replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
const iframeSnippet = computed(
	() =>
		`<iframe src="${
			publicUrl.value
		}?embed=1" width="100%" height="640" style="border:0" title="${escapeAttr(
			form.title || "Web form"
		)}"></iframe>`
);

// every edit funnels through markDirty(), which just flags unsaved changes;
// the user persists explicitly via the header Save button (saveNow)
let revision = 0; // bumped per edit so a save can tell whether edits landed mid-request
function markDirty() {
	revision++;
	dirty.value = true;
}
// header Save button: persist and confirm (errors are toasted inside save())
async function saveNow() {
	if (!dirty.value || saving.value) return;
	const ok = await save();
	if (ok) toast.success(__("Form updated"));
}
async function goBack() {
	if (!dirty.value || (await confirmDiscard())) emit("back");
}
// Closing the dialog, Esc and a pane switch all move the address.
const stopLeaveGuard = props.router?.beforeEach((to, from) =>
	!dirty.value || samePane(to, from) ? true : confirmDiscard()
);
function blockUnload(event) {
	if (!dirty.value) return;
	event.preventDefault();
	event.returnValue = "";
}
window.addEventListener("beforeunload", blockUnload);
onBeforeUnmount(() => {
	stopLeaveGuard?.();
	window.removeEventListener("beforeunload", blockUnload);
});
function samePane(to, from) {
	const pane = (hash) => hash.split("/").slice(0, 3).join("/");
	return to.path === from.path && pane(to.hash) === pane(from.hash);
}
function confirmDiscard() {
	return new Promise((resolve) =>
		dialog.confirm({
			title: __("Discard unsaved changes?"),
			message: __("This form has changes that are not saved."),
			confirmLabel: __("Discard"),
			cancelLabel: __("Keep editing"),
			onConfirm: () => resolve(true),
			onCancel: () => resolve(false),
		})
	);
}
function toggle(f) {
	expanded.value = expanded.value === f.fieldname ? null : f.fieldname;
}
// focusing a field's label selects it (reveals inline editor) without toggling off
function open(f) {
	expanded.value = f.fieldname;
}

// field counts shown in section headers
function sectionFieldCount(sec) {
	return sec.columns.reduce((n, c) => n + c.items.length, 0);
}

// opening the Add Field picker collapses any open field editor
function openFieldPicker(isOpen, setOpen) {
	if (!isOpen) expanded.value = null;
	setOpen(!isOpen);
}

// add a field into a specific column, then re-flatten to form.fields
function addFieldToColumn(col, option) {
	const af = option?.af || option;
	if (!af?.fieldname) return;
	// a freshly added field starts collapsed, not stacked under a previously open one
	expanded.value = null;
	// re-adding a field that was moved to hidden brings it back onto the form
	hiddenFields.value = hiddenFields.value.filter((h) => h.fieldname !== af.fieldname);
	col.items.push({
		fieldname: af.fieldname,
		label: af.label,
		fieldtype: af.fieldtype,
		options: af.options,
		reqd: !!af.reqd,
		placeholder: "",
		field_description: "",
		depends_on: "",
		mandatory_depends_on: "",
		read_only_depends_on: "",
	});
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

// ⋯ menu: column ops shared by the root section and every section
function columnOps(cols) {
	return [
		{
			label: __("Add Column"),
			icon: "lucide-columns",
			onClick: () => addColumn(cols),
			condition: () => cols.length < MAX_COLUMNS,
		},
		{
			label: __("Remove Last Column"),
			icon: "lucide-trash-2",
			onClick: () => removeLastColumn(cols),
			condition: () => cols.length > 1,
		},
	];
}

// ⋯ menu for a section: rename / remove + column ops
function sectionMenu(sec) {
	return [
		{
			group: __("Section"),
			options: [
				{
					label: __("Rename"),
					icon: "lucide-edit",
					onClick: () => (sec.editingLabel = true),
				},
				{
					label: __("Remove Section"),
					icon: "lucide-trash-2",
					onClick: () => removeBreak(sec.secField),
				},
			],
		},
		{ group: __("Column"), options: columnOps(sec.columns) },
	];
}
function optionList(f) {
	return (f.options || "").split("\n").filter(Boolean);
}
function selectOptions(f) {
	const opts = optionList(f).map((o) => ({ label: o, value: o }));
	return [{ label: __("Select an option"), value: "" }, ...opts];
}
// preview dropdown for a Link field — the target doctype's records, fetched lazily
// into `linkOptions`; mirrors the public form's server-populated <select>.
function linkSelectOptions(f) {
	ensureLinkMeta(f.options);
	const opts = (linkOptions[f.options] || []).map((o) => ({
		label: o,
		value: o,
	}));
	return [{ label: __("Select an option"), value: "" }, ...opts];
}
const TEXTAREA_TYPES = [
	"Small Text",
	"Text",
	"Long Text",
	"Text Editor",
	"HTML Editor",
	"Markdown Editor",
];
function inputType(f) {
	if (f.options === "Email") return "email";
	if (["Int", "Float", "Currency", "Percent"].includes(f.fieldtype)) return "number";
	if (f.fieldtype === "Date") return "date";
	if (f.fieldtype === "Datetime") return "datetime-local";
	if (f.fieldtype === "Time") return "time";
	if (f.fieldtype === "Color") return "color";
	return "text";
}

const inputFieldCount = computed(
	() => form.fields.filter((f) => !BREAK_TYPES.includes(f.fieldtype)).length
);

// group fields into sections -> columns for the preview
const layout = computed(() => {
	const sections = [];
	let cur = { label: null, columns: [[]] };
	for (const f of form.fields) {
		if (f.fieldtype === "Section Break") {
			sections.push(cur);
			cur = { label: f.label || null, columns: [[]] };
		} else if (f.fieldtype === "Column Break") {
			cur.columns.push([]);
		} else {
			cur.columns[cur.columns.length - 1].push(f);
		}
	}
	sections.push(cur);
	return sections.filter((s) => s.label || s.columns.some((c) => c.length));
});

function uid(fieldtype) {
	const p = fieldtype === "Section Break" ? "section_break_" : "column_break_";
	return p + Math.random().toString(36).slice(2, 8);
}
function makeMarker(fieldtype) {
	return {
		fieldname: uid(fieldtype),
		label: "",
		fieldtype,
		options: "",
		reqd: false,
		placeholder: "",
		field_description: "",
	};
}
// a section can hold this many columns before it gets too cramped to build/fill
const MAX_COLUMNS = 4;

// columns in the last section (where a new Column Break would land)
const lastSectionColumns = computed(() => {
	const secs = sections.value;
	return secs.length ? secs[secs.length - 1].columns.length : 1;
});
const columnBreakDisabled = computed(() => lastSectionColumns.value >= MAX_COLUMNS);

function addBreak(fieldtype) {
	if (fieldtype === "Column Break" && columnBreakDisabled.value) {
		toast.info(__("A section can have up to {0} columns", [MAX_COLUMNS]));
		return;
	}
	// append at the end: a Section Break starts a new section, a Column Break
	// adds a new column to the last section
	form.fields.push({
		fieldname: uid(fieldtype),
		label: "",
		fieldtype,
		options: "",
		reqd: false,
		placeholder: "",
		field_description: "",
	});
	rebuildModel();
	markDirty();
}

// load
call("get_form_config", { name: props.name })
	.then((doc) => {
		form.title = doc.title || "";
		form.route = doc.route || "";
		form.document_type = doc.document_type || "CRM Lead";
		form.description = doc.description || "";
		form.submit_button_label = doc.submit_button_label || "Submit";
		form.success_message = doc.success_message || "";
		form.redirect_url = doc.redirect_url || "";
		form.allowed_embedding_domains = doc.allowed_embedding_domains || "";
		form.published = doc.published || 0;
		form.fields = (doc.fields || []).map((f) => ({
			name: f.name,
			fieldname: f.fieldname,
			label: f.label,
			fieldtype: f.fieldtype,
			options: f.options,
			reqd: !!f.reqd,
			placeholder: f.placeholder,
			field_description: f.field_description,
			depends_on: f.depends_on || "",
			mandatory_depends_on: f.mandatory_depends_on || "",
			read_only_depends_on: f.read_only_depends_on || "",
		}));
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

// select is bound to this so we can intercept the change and confirm before
// dropping incompatible fields; cancelling leaves form.document_type untouched
// so the dropdown snaps back to the current value
const doctypeModel = computed({
	get: () => form.document_type,
	set: (v) => requestDoctypeChange(v),
});

async function requestDoctypeChange(newDt) {
	if (!newDt || newDt === form.document_type) return;
	let fields, seed;
	try {
		// fetch both before touching the form, so a failure leaves it unchanged
		[fields, seed] = await Promise.all([
			call("get_form_fields", { document_type: newDt }),
			call("get_hidden_seed", { document_type: newDt }),
		]);
	} catch (e) {
		toast.error(errorText(e, __("Could not change the form type")));
		return;
	}
	const valid = new Set((fields || []).map((f) => f.fieldname));
	const wouldDrop = form.fields.filter(
		(f) => !BREAK_TYPES.includes(f.fieldtype) && !valid.has(f.fieldname)
	).length;
	const losses = [];
	if (wouldDrop)
		losses.push(
			__("Switching to {0} will remove {1} field(s) that don't exist on {0}.", [
				docLabel(newDt),
				wouldDrop,
			])
		);
	if (hiddenDefaultsLost(seed))
		losses.push(
			__("The hidden fields' default values are reset to those of {0}.", [docLabel(newDt)])
		);

	if (!losses.length) {
		commitDoctype(newDt, valid, seed);
		return;
	}
	dialog.confirm({
		title: __("Change form type?"),
		message: [...losses, __("This can't be undone.")].join(" "),
		confirmLabel: wouldDrop ? __("Change & remove fields") : __("Change form type"),
		theme: "red",
		onConfirm: () => commitDoctype(newDt, valid, seed),
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
function hiddenDefaultsLost(seed) {
	const next = new Map((seed || []).map((h) => [h.fieldname, String(h.default ?? "")]));
	return hiddenFields.value.some((h) => String(h.default ?? "") !== (next.get(h.fieldname) ?? ""));
}

async function commitDoctype(newDt, valid, seed) {
	form.document_type = newDt;
	expanded.value = null;
	await availableFields.reload();
	const before = form.fields.length;
	form.fields = form.fields.filter(
		(f) => BREAK_TYPES.includes(f.fieldtype) || valid.has(f.fieldname)
	);
	const dropped = before - form.fields.length;
	// reconcile the fields we kept against the new doctype's real definitions:
	// pick up its options and enforce its mandatory flags
	const catalog = new Map((availableFields.data || []).map((f) => [f.fieldname, f]));
	form.fields.forEach((f) => {
		const c = catalog.get(f.fieldname);
		if (!c) return;
		f.options = c.options;
		if (c.reqd) f.reqd = true;
		if (f.fieldtype === "Link") ensureLinkMeta(f.options);
	});
	// rebuild hidden fields for the new doctype: its system-hidden fields (Status,
	// with the right options + default)
	setHiddenFields(seed);
	rebuildModel();
	markDirty();
	if (dropped) {
		toast.info(__("{0} field(s) removed. Not available on {1}.", [dropped, docLabel(newDt)]));
	}
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
	form.fields = flattenModel();
	try {
		const doc = await call("save_form", {
			name: form.name,
			form: {
				title: form.title,
				route: slugify(form.route),
				document_type: form.document_type,
				description: form.description,
				submit_button_label: form.submit_button_label,
				success_message: form.success_message,
				redirect_url: form.redirect_url,
				allowed_embedding_domains: form.allowed_embedding_domains,
				published: form.published ? 1 : 0,
				fields: form.fields.map((f) => ({
					fieldname: f.fieldname,
					label: f.label,
					fieldtype: f.fieldtype,
					options: f.options,
					reqd: f.reqd ? 1 : 0,
					placeholder: f.placeholder,
					field_description: f.field_description,
					depends_on: f.depends_on || "",
					mandatory_depends_on: f.mandatory_depends_on || "",
					read_only_depends_on: f.read_only_depends_on || "",
				})),
				hidden_fields: hiddenFields.value.map((h) => ({
					fieldname: h.fieldname,
					label: h.label,
					fieldtype: h.fieldtype,
					options: h.options,
					default: h.default,
				})),
			},
		});
		form.route = doc.route;
		(doc.fields || []).forEach((df, i) => {
			if (form.fields[i]) form.fields[i].name = df.name;
		});
		dirty.value = savedRevision !== revision;
		emit("saved");
		return true;
	} catch (e) {
		if (!silent) toast.error(e?.messages?.[0] || e?.message || __("Could not save"));
		return false;
	} finally {
		saving.value = false;
	}
}

// header Publish toggle: flip the flag locally (instant, no animation) and mark
// dirty — like Assignment Rule's Enabled switch, it persists on Save, where the
// publish guard (every hidden field needs a default) is enforced
function togglePublish() {
	form.published = form.published ? 0 : 1;
	markDirty();
}
</script>

<style>
/* Hide Sortable's floating drag clone so reordering stays contained to the
   fields list — only the in-list placeholder moves, never a copy that can
   drift outside the section/modal. */
.wf-drag-fallback {
	opacity: 0 !important;
}

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
