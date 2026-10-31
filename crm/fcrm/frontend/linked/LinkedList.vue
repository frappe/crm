<!-- A tab's table of the records that link to the page's record, each row opening its record. -->
<template>
	<div class="flex flex-col gap-3 px-[--page-gutter] pb-8 pt-4">
		<List
			v-if="rows.length"
			:columns="columns.map((column) => column.width)"
			:rowHeight="40"
			class="-mx-2 list-row-px-2 list-gap-4"
		>
			<ListHeader>
				<ListHeaderCell
					v-for="column in columns"
					:key="column.label"
					:class="{ 'justify-end': column.align === 'right' }"
				>
					{{ column.label }}
				</ListHeaderCell>
			</ListHeader>
			<ListRow v-for="row in rows" :key="row.name" :route="routeFor(source.doctype, row.name)">
				<slot :row="row" />
			</ListRow>
		</List>
		<div v-else-if="list.loading.value" class="flex flex-col gap-3 py-2">
			<Skeleton v-for="index in 3" :key="index" class="h-4 w-full rounded-2" />
		</div>
		<p v-else-if="!list.error.value" class="py-10 text-center text-base text-ink-gray-5">{{ empty }}</p>
		<p v-if="list.error.value" class="py-4 text-center text-base text-ink-gray-5">
			{{ __('Could not load the list.') }}
		</p>
		<div v-if="list.hasNextPage.value" class="flex justify-center">
			<Button variant="ghost" :label="__('Load more')" :loading="list.loading.value" @click="list.loadMore()" />
		</div>
	</div>
</template>

<script setup>
import { computed } from 'vue'
import { Button, Skeleton } from 'frappe-ui'
import { List, ListHeader, ListHeaderCell, ListRow } from 'frappe-ui/list'
import { usePagedList } from '@framework/ui'
import { routeFor } from '@shell'
import { __ } from 'frappe/i18n'
import { linkedQuery, uniqueRows } from './linkedQuery.js'

const props = defineProps({
	page: { type: Object, required: true },
	source: { type: Object, required: true },
	columns: { type: Array, required: true },
	empty: { type: String, required: true },
})

const list = usePagedList(props.source.doctype, () => linkedQuery(props.source, props.page.docname))
list.reload()
const rows = computed(() => uniqueRows(list.rows.value))
</script>
