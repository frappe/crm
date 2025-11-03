<template>
      <div class="flex h-full flex-col gap-6 text-ink-gray-8">
        <!-- Header -->
        <div class="flex justify-between px-2 pt-2">
            <div class="flex flex-col gap-1 w-9/12">
                <h2 class="flex gap-2 text-xl font-semibold leading-none h-5 items-center">
                    {{ __('Lead sources') }}
                    <Badge theme="orange" size="sm">Beta</Badge>
                </h2>
                <p class="text-p-base text-ink-gray-6">
                {{
                    __(
                    'Add, edit, and manage sources for automatic lead syncing to your CRM',
                    )
                }}
                </p>
            </div>
            <div class="flex item-center space-x-2 w-3/12 justify-end">
                <Button
                    :label="__('New')"
                    icon-left="plus"
                    variant="solid"
                    @click="emit('updateStep', 'new-source')"
                />
            </div>
        </div>

        <!-- loading state -->
        <div
        v-if="sources.loading"
        class="flex mt-28 justify-between w-full h-full"
        >
            <Button
                :loading="sources.loading"
                variant="ghost"
                class="w-full"
                size="2xl"
            />
        </div>
        
        <!-- Empty State -->
        <div
        v-if="!sources.loading && !sources.data?.length"
        class="flex justify-between w-full h-full"
        >
            <div
                class="text-ink-gray-4 border border-dashed rounded w-full flex items-center justify-center"
            >
                {{ __('No lead sources found') }}
            </div>
        </div>

        <!-- Lead source list -->
        <div
        class="flex flex-col overflow-hidden"
        v-if="!sources.loading && sources.data?.length"
        >
        <div class="flex items-center py-2 px-4 text-sm text-ink-gray-5">
            <div class="w-4/6">{{ __('Name') }}</div>
            <div class="w-1/6">{{ __('Source') }}</div>
            <div class="w-1/6">{{ __('Enabled') }}</div>
        </div>
        <div class="h-px border-t mx-4 border-outline-gray-modals" />
        <ul class="overflow-y-auto px-2">
            <template v-for="(source, i) in sourcesList" :key="source.name">
            <li
                class="flex items-center justify-between p-3 cursor-pointer hover:bg-surface-menu-bar rounded"
                @click="() => emit('updateStep', 'edit-source', { ...source })"
            >
                <div class="flex flex-col w-4/6 pr-5">
                    <div class="text-p-base font-medium text-ink-gray-7 truncate">
                        {{ source.name }}
                    </div>
                </div>

                <div class="flex flex-col w-1/6 pr-5">
                    <div class="text-p-base font-medium text-ink-gray-7 truncate">
                        {{ source.type }}
                    </div>
                </div>

                <div class="flex items-center justify-between w-1/6">
                    <Switch
                        size="sm"
                        v-model="source.enabled"
                        @update:model-value="toggleLeadSyncSourceEnabled(source)"
                        @click.stop
                    />
                    <Dropdown
                        class=""
                        :options="getDropdownOptions(source)"
                        placement="right"
                        :button="{
                        icon: 'more-horizontal',
                        variant: 'ghost',
                        onblur: (e) => {
                            e.stopPropagation()
                            confirmDelete = false
                        },
                        }"
                        @click.stop
                    />
                </div>
            </li>
            <div
                v-if="sourcesList.length !== i + 1"
                class="h-px border-t mx-2 border-outline-gray-modals"
            />
            </template>
            <!-- Load More Button -->
            <div
            v-if="!sources.loading && sources.hasNextPage"
            class="flex justify-center"
            >
           
            <Button
                class="mt-3.5 p-2"
                @click="() => sources.next()"
                :loading="sources.loading"
                :label="__('Load More')"
                icon-left="refresh-cw"
            />
            </div>
        </ul>
        </div>
      </div>
</template>
<script setup>
import {
	Switch,
	Dropdown,
	toast,
    Badge,
} from "frappe-ui";
import { ref, computed, inject } from "vue";

const emit = defineEmits(["updateStep"]);

const sources = inject("sources");

const search = ref("");
const confirmDelete = ref(false);

const sourcesList = computed(() => {
	let list = sources.data || [];
	if (search.value) {
		list = list.filter(
			(source) =>
				source.name.toLowerCase().includes(search.value.toLowerCase()) ||
				source.subject.toLowerCase().includes(search.value.toLowerCase()),
		);
	}
	return list;
});

function toggleLeadSyncSourceEnabled(source) {
  sources.setValue.submit(
    {
      name: source.name,
      enabled: source.enabled ? 1 : 0,
    },
    {
      onSuccess: () => {
        toast.success(
          source.enabled
            ? __('Source enabled successfully')
            : __('Source disabled successfully'),
        )
      },
      onError: (error) => {
        toast.error(error.messages[0] || __('Failed to update source'))
        // Revert the change if there was an error
        source.enabled = !source.enabled
      },
    },
  )
}

function deleteLeadSource(source) {
	confirmDelete.value = false;
	sources.delete.submit(source.name, {
		onSuccess: () => {
			toast.success(__("Lead Sync Source deleted successfully"));
		},
		onError: (error) => {
			toast.error(error.messages[0] || __("Failed to delete Lead Sync Source"));
		},
	});
}

function getDropdownOptions(source) {
	let options = [
		{
			label: __("Duplicate"),
			icon: "copy",
			onClick: () => emit("updateStep", "new-source", { ...source }),
		},
		{
			label: __("Delete"),
			icon: "trash-2",
			onClick: (e) => {
				e.preventDefault();
				e.stopPropagation();
				confirmDelete.value = true;
			},
			condition: () => !confirmDelete.value,
		},
		{
			label: __("Confirm Delete"),
			icon: "trash-2",
			theme: "red",
			onClick: () => deleteLeadSource(source),
			condition: () => confirmDelete.value,
		},
	];

	return options;
}
</script>