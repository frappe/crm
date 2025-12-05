<template>
    <div v-if="selectedLog">
        <div class="flex justify-between items-center">
            <Button variant="ghost" icon-left="chevron-left" @click="selectedLog = null">
                {{ __("Back to all logs") }}
            </Button>
            <Button v-if="logDoc?.document?.retrySync && selectedLog.type != 'Synced'" :loading="logDoc?.document?.retrySync.loading"
                @click="logDoc?.document?.retrySync.submit()">
                {{ __("Retry Sync") }}
            </Button>
        </div>

        <div class="grid grid-cols-2 gap-2 mt-4">
            <FormControl type="text" :label="__('Log ID')" :value="selectedLog.name" disabled />

            <FormControl type="text" :label="__('Reason')" :value="selectedLog.type" disabled />
        </div>

        <div class="mt-4 flex flex-col gap-8">
            <div>
                <Textarea class="h-[250px]" :label="__('Lead Data')" :value="selectedLog.lead_data" disabled />
            </div>

            <div>
                <Textarea v-if="selectedLog.traceback" class="h-[250px]" :label="__('Traceback')" disabled
                    :value="selectedLog.traceback" />
            </div>

        </div>
    </div>

    <ListView v-if="!selectedLog && failedLeadSyncLogList?.data" class="h-full" :columns="columns"
        :rows="failedLeadSyncLogList?.data" :options="{
            selectable: false,
            showTooltip: true,
            resizeColumn: false,
            emptyState: {
                title: __('No failure logs found'),
                description: __('Any failed lead syncs will show up here'),
            },
            onRowClick: (row) => {
                selectedLog = row
            }
        }">
        <template #cell="{ item, row, column }">
            <Badge v-if="column.key === 'type'">{{ item }}</Badge>
            <span v-else class="text-base">{{ item }}</span>
        </template>
    </ListView>
</template>

<script setup>
import { ref, watch } from "vue";
import { useDocument } from "@/data/document";
import { Badge, createListResource, Textarea, ListView, FormControl, toast } from "frappe-ui";

const props = defineProps({
    source: {
        type: String,
        required: true
    }
})

const selectedLog = ref(null);

const failedLeadSyncLogList = createListResource({
    doctype: "Failed Lead Sync Log",
    fields: ["name", "type", "lead_data", "traceback"],
    filters: {
        source: props.source
    },
    auto: true
})

const columns = [
    {
        "label": __("ID"),
        "key": "name"
    },
    {
        "label": __("Type"),
        "key": "type"
    }
]

const logDoc = ref(null);
watch(selectedLog, () => {
    if (!selectedLog.value?.name) {
        return
    }

    logDoc.value = useDocument("Failed Lead Sync Log", selectedLog.value.name, {
        whitelistedMethods: {
            retrySync: {
                method: 'retry_sync',
                onSuccess() {
                    toast.success(__("Sync successful!"))
                },
                onError(e) {
                    toast.error(e.message || (e.messages ?? e.messages[0]) || e.exc_type || __("Error syncing lead"))
                }
            }
        }
    });
})
</script>