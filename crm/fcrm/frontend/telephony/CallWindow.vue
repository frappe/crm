<!-- CRM's call window, Twilio: a phone card inside desk v2's standing frame (#46115, layout C). -->
<template>
  <div
    v-if="contact"
    class="flex flex-col items-center gap-4 pb-1 pt-2 text-center"
  >
    <div class="rounded-full" :class="{ 'call-ring': ringing }">
      <Avatar
        :label="contact.name || '#'"
        :image="contact.image"
        size="3xl"
        shape="circle"
      />
    </div>
    <div class="flex min-w-0 max-w-full flex-col gap-1.5">
      <div class="truncate text-lg font-medium text-ink-gray-8">
        {{ contact.name || contact.number }}
      </div>
      <div class="truncate text-p-sm text-ink-gray-5">
        {{ contact.name ? contact.number : __("Unknown number") }}
      </div>
    </div>
    <div
      v-if="state.step === 'oncall' || state.step === 'ended'"
      class="text-base tabular-nums transition-colors duration-300"
      :class="state.step === 'ended' ? 'text-ink-gray-5' : 'text-ink-gray-7'"
    >
      {{ clock }}
    </div>
    <div class="flex flex-wrap items-center justify-center gap-3">
      <Tooltip
        v-for="button in buttons"
        :key="button.label"
        :text="button.label"
      >
        <Button
          class="!size-9 !rounded-full"
          :icon="button.icon"
          :label="button.label"
          :variant="button.theme ? 'solid' : 'subtle'"
          :theme="button.theme || 'gray'"
          @click="button.run"
        />
      </Tooltip>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, watch, watchEffect } from "vue";
import { Avatar, Button, Tooltip } from "frappe-ui";
import { routeFor } from "@shell";
import { __ } from "frappe/i18n";
import { callApi } from "./callApi.js";
import { createTwilioCall, formatClock } from "./twilioCall.js";
import { loadTwilioDevice } from "./twilioDevice.js";

const props = defineProps({ shell: Object, window: Object });

const call = createTwilioCall({
  api: callApi,
  loadDevice: (tokenData) =>
    loadTwilioDevice(tokenData, () => import("@twilio/voice-sdk")),
});
const { state } = call;
call.start();
onBeforeUnmount(call.destroy);

const contact = computed(() => state.contact);
const clock = computed(() => formatClock(state.seconds));
const ringing = computed(
  () => state.step === "incoming" || state.step === "ringing"
);
const record = computed(() => contact.value?.record);

const buttons = computed(() => {
  const accept = {
    label: __("Accept"),
    icon: "lucide-phone",
    theme: "green",
    pill: true,
    run: call.accept,
  };
  const reject = {
    label: __("Reject"),
    icon: "lucide-phone-off",
    theme: "red",
    pill: true,
    run: call.reject,
  };
  if (state.step === "incoming") return [accept, reject];
  if (state.step === "ringing")
    return [{ ...reject, label: __("Cancel"), pill: true, run: call.hangUp }];
  if (state.step !== "oncall" && state.step !== "ended") return [];
  return [
    ...(state.step === "oncall" ? [mute.value] : []),
    ...extras.value,
    ...(state.step === "oncall" ? [hangUp] : []),
  ];
});
const mute = computed(() => ({
  label: state.muted ? __("Unmute") : __("Mute"),
  icon: state.muted ? "lucide-mic-off" : "lucide-mic",
  pill: true,
  run: call.toggleMute,
}));
const hangUp = {
  label: __("Hang up"),
  icon: "lucide-phone-off",
  theme: "red",
  pill: true,
  run: call.hangUp,
};
const extras = computed(() => [
  {
    label: __("Note"),
    icon: "lucide-notebook-pen",
    run: () => createDuringCall("FCRM Note"),
  },
  {
    label: __("Task"),
    icon: "lucide-square-check",
    run: () => createDuringCall("CRM Task"),
  },
  ...(record.value && record.value.doctype !== "Contact"
    ? [
        {
          label: __(record.value.doctype === "CRM Deal" ? "Deal" : "Lead"),
          icon: "lucide-arrow-up-right",
          run: openRecord,
        },
      ]
    : []),
]);

async function createDuringCall(doctype) {
  const linked = record.value && record.value.doctype !== "Contact";
  const values = linked
    ? {
        reference_doctype: record.value.doctype,
        reference_docname: record.value.name,
      }
    : {};
  if (doctype === "CRM Task")
    values.title = `${__("Follow up with")} ${
      contact.value.name || contact.value.number
    }`;
  const doc = await props.shell.create(doctype, { values });
  if (!doc) return;
  try {
    await call.linkToCall(doctype, doc);
  } catch (error) {
    props.shell.toast.error(error.message);
  }
}

function openRecord() {
  return props.shell.router.push(
    routeFor(record.value.doctype, record.value.name)
  );
}

const STATUS = computed(() => ({
  incoming: [__("Incoming call"), __("Incoming")],
  ringing: [__("Calling…"), __("Calling…")],
  oncall: [__("On call"), clock.value],
  ended: [__("Call ended"), __("Ended")],
}));

// The open frame's title is the call's state (the card has the name); the pill shows "name · status".
watchEffect(() => {
  const [title, short] = STATUS.value[state.step] || [];
  if (!title) return;
  const who = contact.value?.name || contact.value?.number;
  props.window.setTitle(
    props.window.state === "minimised" ? `${who} · ${short}` : title
  );
});
// Only the pill carries actions: the card's round buttons do the same job when it is open.
watchEffect(() => {
  const minimised = props.window.state === "minimised";
  props.window.setActions(minimised ? buttons.value.filter((b) => b.pill) : []);
});
watchEffect(() => props.window.setClosable(state.step === "ended"));
watchEffect(() => props.window.setKeepAlive(call.isLive()));
// TODO(#46261): `window.setAttention(ringing)` pulses the pill while the call rings.

watch(
  () => state.step,
  (step) => {
    if (step === "incoming" || step === "ringing") props.window.open();
    if (step === "idle") props.window.close();
  }
);
// The frame's close after a call hides the window; the card is spent.
watch(
  () => props.window.state,
  (frame) => frame === "closed" && call.dismiss()
);
</script>

<style>
@media (prefers-reduced-motion: no-preference) {
  .call-ring {
    animation: call-ring 1.6s ease-out infinite;
  }
}
@keyframes call-ring {
  from {
    box-shadow: 0 0 0 0 var(--outline-gray-3);
  }
  to {
    box-shadow: 0 0 0 10px transparent;
  }
}
</style>
