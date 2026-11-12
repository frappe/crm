<template>
	<div class="mx-auto flex w-full max-w-[640px] flex-col gap-8 pt-6">
		<section class="flex flex-col gap-4">
			<div class="flex flex-col gap-1">
				<h3 class="text-base-medium text-ink-gray-8">{{ __("Link") }}</h3>
				<p class="text-p-sm text-ink-gray-5">
					{{
						form.published
							? __("Send people straight to the hosted form.")
							: __("Not published yet. Publish it to make the link and embed live.")
					}}
				</p>
			</div>
			<div class="flex items-center gap-2">
				<TextInput class="flex-1" readonly :modelValue="publicUrl" />
				<Button icon="lucide-copy" :tooltip="__('Copy link')" @click="copyToClipboard(publicUrl)" />
				<Button :label="__('Open')" icon-left="lucide-external-link" :href="publicUrl" />
			</div>
		</section>

		<section class="flex flex-col gap-4">
			<div class="flex flex-col gap-1">
				<h3 class="text-base-medium text-ink-gray-8">{{ __("Embed") }}</h3>
				<p class="text-p-sm text-ink-gray-5">
					{{ __("Paste this code into a page of your website.") }}
				</p>
			</div>
			<div class="relative rounded-4 bg-surface-gray-2">
				<pre
					class="whitespace-pre-wrap py-2 pl-3 pr-10 font-mono text-sm leading-5 text-ink-gray-7 [overflow-wrap:anywhere]"
					>{{ iframeSnippet }}</pre
				>
				<Button
					class="absolute right-1 top-1"
					variant="ghost"
					icon="lucide-copy"
					:tooltip="__('Copy code')"
					@click="copyToClipboard(iframeSnippet)"
				/>
			</div>
		</section>

		<section class="flex flex-col gap-4">
			<div class="flex flex-col gap-1">
				<h3 class="text-base-medium text-ink-gray-8">{{ __("Allowed domains") }}</h3>
				<p class="text-p-sm text-ink-gray-5">
					{{ __("Sites that may show the embed. Browsers block it everywhere else.") }}
				</p>
			</div>
			<ul v-if="embeddingDomains.length" class="flex flex-col">
				<li
					v-for="domain in embeddingDomains"
					:key="domain"
					class="flex h-9 items-center gap-2 border-b border-outline-gray-1 first:border-t"
				>
					<span class="lucide-globe h-4 w-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
					<span class="flex-1 truncate text-base text-ink-gray-8">{{ domain }}</span>
					<span v-if="!normalizeDomain(domain)" class="shrink-0 text-p-sm text-ink-red-4">
						{{ __("Not valid, ignored") }}
					</span>
					<Button
						class="-mr-1.5"
						variant="ghost"
						icon="lucide-x"
						:tooltip="__('Remove')"
						@click="removeDomain(domain)"
					/>
				</li>
			</ul>
			<div class="flex flex-col gap-1.5">
				<div class="flex items-center gap-2">
					<TextInput
						v-model="newDomain"
						class="flex-1"
						placeholder="https://www.example.com"
						@keydown.enter.prevent="addDomain"
						@input="domainError = ''"
					/>
					<Button :label="__('Add domain')" icon-left="lucide-plus" @click="addDomain" />
				</div>
				<p v-if="domainError" class="text-p-sm text-ink-red-4">{{ domainError }}</p>
				<p v-else-if="!embeddingDomains.length" class="text-p-sm text-ink-gray-5">
					{{ __("No domains added. The embed works only on this site until you add one.") }}
				</p>
			</div>
		</section>
	</div>
</template>

<script setup>
import { Button, TextInput } from "frappe-ui";
import { computed, ref } from "vue";
import { __ } from "frappe/i18n";
import { copyToClipboard } from "../formsApi";
import { domainList, normalizeDomain } from "./formModel";

const props = defineProps({ draft: { type: Object, required: true } });
const { form, markDirty } = props.draft;

const publicUrl = computed(() => `${window.location.origin}/crm-form/${form.route}`);
const embeddingDomains = computed(() => domainList(form.allowed_embedding_domains));

const newDomain = ref("");
const domainError = ref("");

function addDomain() {
	if (!newDomain.value.trim()) return;
	const domain = normalizeDomain(newDomain.value);
	if (!domain) {
		domainError.value = __("Enter a valid site address, like https://www.example.com");
		return;
	}
	if (!embeddingDomains.value.includes(domain)) setDomains([...embeddingDomains.value, domain]);
	newDomain.value = "";
}

function removeDomain(domain) {
	setDomains(embeddingDomains.value.filter((d) => d !== domain));
}

function setDomains(list) {
	form.allowed_embedding_domains = list.join("\n");
	markDirty();
}

const escapeAttr = (text) => text.replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
const iframeSnippet = computed(
	() =>
		`<iframe src="${
			publicUrl.value
		}?embed=1" width="100%" height="640" style="border:0" title="${escapeAttr(
			form.title || "Web form"
		)}"></iframe>`
);
</script>
