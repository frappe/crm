<template>
	<div class="flex flex-col pt-5">
		<p v-if="!form.published" class="mb-5 text-p-sm text-ink-gray-5">
			{{ __("This form isn’t published yet. Turn on Publish to make the link and embeds live.") }}
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
						{{ __("Sandboxed in a frame. Simplest, but a fixed height and its own styling.") }}
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
					__("Not a valid domain and will be ignored: {0}", [invalidEmbeddingDomains.join(", ")])
				}}
			</p>
			<p v-else-if="!embeddingDomains.length" class="mt-1.5 text-xs text-ink-gray-5">
				{{ __("No domains added. The embed will only work on this site until you add one.") }}
			</p>
		</div>
	</div>
</template>

<script setup>
import { Button, TextInput } from "frappe-ui";
import { computed } from "vue";
import { __ } from "frappe/i18n";
import { copyToClipboard } from "../formsApi";

const props = defineProps({ draft: { type: Object, required: true } });
const { form, markDirty } = props.draft;

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
</script>
