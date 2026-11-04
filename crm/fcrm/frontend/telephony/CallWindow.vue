<!-- CRM's call window, Twilio and Exotel: a phone card inside desk v2's standing frame (#46115, layout C). -->
<template>
  <div v-if="pending" class="flex flex-col gap-3 pb-1 pt-1">
    <div class="text-p-sm text-ink-gray-5">{{ __("Call with") }}</div>
    <Button
      v-for="medium in callState.media"
      :key="medium"
      class="w-full"
      icon-left="lucide-phone"
      :label="medium"
      @click="choose(medium)"
    />
    <Checkbox v-model="remember" :label="__('Remember my choice')" />
  </div>
  <div
    v-else-if="contact"
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
      v-if="showClock"
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
import {
  computed,
  onBeforeUnmount,
  ref,
  watch,
  watchEffect,
} from "vue";
import { Avatar, Button, Checkbox, Tooltip } from "frappe-ui";
import { routeFor } from "@shell";
import { __ } from "frappe/i18n";
import { callApi } from "./callApi.js";
import { callState } from "./callState.js";
import { createExotelCall } from "./exotelCall.js";
import { createTwilioCall, formatClock } from "./twilioCall.js";
import { loadTwilioDevice } from "./twilioDevice.js";

// `dial` is the request an act made through `shell.windowOf`, possibly before this window mounted.
const props = defineProps({ shell: Object, window: Object, dial: Object });

// One call controller per enabled medium; the card shows whichever has a call.
const calls = {};
if (callState.media.includes("Twilio"))
  calls.Twilio = createTwilioCall({
    api: callApi,
    loadDevice: (tokenData) =>
      loadTwilioDevice(tokenData, () => import("@twilio/voice-sdk")),
  });
if (callState.media.includes("Exotel"))
  calls.Exotel = createExotelCall({
    api: { ...callApi, call: callApi.exotelCall },
    realtime: props.shell.realtime,
  });
const controllers = Object.values(calls);
controllers.forEach((controller) => {
  controller.start();
  watch(
    () => controller.state.error,
    (message) => message && props.shell.toast.error(message)
  );
});
onBeforeUnmount(() =>
  controllers.forEach((controller) => controller.destroy())
);

const call = computed(
  () =>
    controllers.find((controller) => controller.isLive()) ||
    controllers.find((controller) => controller.state.step !== "idle") ||
    controllers[0]
);
const state = computed(() => call.value.state);
const isTwilio = computed(() => call.value === calls.Twilio);

const contact = computed(() => state.value.contact);
const clock = computed(() => formatClock(state.value.seconds));
const showClock = computed(() =>
  ["oncall", "ended"].includes(state.value.step)
);
const ringing = computed(
  () => state.value.step === "incoming" || state.value.step === "ringing"
);
const record = computed(() => contact.value?.record);

// The medium picker: a first step when the user has several media and no default.
const pending = ref(null);
const remember = ref(false);

function startOutgoing(number) {
  if (controllers.some((controller) => controller.isLive())) return;
  const medium =
    callState.media.length === 1 ? callState.media[0] : callState.defaultMedium;
  if (medium) return dial(medium, number);
  pending.value = number;
  props.window.open();
}

async function dial(medium, number) {
  pending.value = null;
  try {
    await calls[medium].makeCall(number);
  } catch {
    // The controller put the message in its `error`, which toasts; the window the act opened has nothing to show.
    if (controllers.every((controller) => controller.state.step === "idle"))
      props.window.close();
  }
}

async function choose(medium) {
  const number = pending.value;
  if (remember.value) {
    try {
      await callApi.rememberMedium(medium);
      callState.defaultMedium = medium;
    } catch (error) {
      props.shell.toast.error(error.message);
    }
  }
  return dial(medium, number);
}

watch(() => props.dial, (request) => request && startOutgoing(request.number), {
  immediate: true,
});

// Exotel shows the controls of the phone call only as far as the record: Note, Task and the lead or deal. It has no
// "connected" event for a call coming in, so those show from the first ring.
const notable = computed(() =>
  isTwilio.value ? ["oncall", "ended"] : ["incoming", "oncall", "ended"]
);

const buttons = computed(() => {
  const step = state.value.step;
  const twilio = isTwilio.value;
  if (twilio && step === "incoming") return [accept, reject];
  if (twilio && step === "ringing")
    return [
      { ...reject, label: __("Cancel"), run: () => calls.Twilio.hangUp() },
    ];
  if (!notable.value.includes(step)) return [];
  return [
    ...(twilio && step === "oncall" ? [mute.value] : []),
    ...extras.value,
    ...(twilio && step === "oncall" ? [hangUp] : []),
  ];
});
const accept = {
  label: __("Accept"),
  icon: "lucide-phone",
  theme: "green",
  pill: true,
  run: () => calls.Twilio.accept(),
};
const reject = {
  label: __("Reject"),
  icon: "lucide-phone-off",
  theme: "red",
  pill: true,
  run: () => calls.Twilio.reject(),
};
const mute = computed(() => ({
  label: state.value.muted ? __("Unmute") : __("Mute"),
  icon: state.value.muted ? "lucide-mic-off" : "lucide-mic",
  pill: true,
  run: () => calls.Twilio.toggleMute(),
}));
const hangUp = {
  label: __("Hang up"),
  icon: "lucide-phone-off",
  theme: "red",
  pill: true,
  run: () => calls.Twilio.hangUp(),
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
          label: record.value.doctype === "CRM Deal" ? __("Deal") : __("Lead"),
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
    values.title = __("Follow up with {0}", [
      contact.value.name || contact.value.number,
    ]);
  // The form can stay open past the call: the log to link is the one this call had.
  const callSid = state.value.callSid;
  const linker = call.value;
  const doc = await props.shell.create(doctype, { values });
  if (!doc) return;
  try {
    await linker.linkToCall(callSid, doctype, doc);
  } catch (error) {
    props.shell.toast.error(error.message);
  }
}

function openRecord() {
  return props.shell.router.push(
    routeFor(record.value.doctype, record.value.name)
  );
}

const STATUS = computed(() => {
  const { customerRinging } = state.value;
  return {
    incoming: [__("Incoming call"), __("Incoming")],
    ringing: isTwilio.value
      ? [__("Calling…"), __("Calling…")]
      : customerRinging
      ? [__("Calling…"), __("Calling…")]
      : [__("Ringing your phone…"), __("Ringing…")],
    oncall: [__("On call"), clock.value],
    ended: [__("Call ended"), __("Ended")],
  };
});

// The open frame's title is the call's state (the card has the name); the pill shows "name · status".
watchEffect(() => {
  if (pending.value)
    return props.window.setTitle(__("Call {0}", [pending.value]));
  const [title, short] = STATUS.value[state.value.step] || [];
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
watchEffect(() =>
  props.window.setClosable(!!pending.value || state.value.step === "ended")
);
watchEffect(() => props.window.setKeepAlive(call.value.isLive()));
// A minimised pill pulses while a caller waits on us to answer.
watchEffect(() => props.window.setAttention(state.value.step === "incoming"));

watch(
  () => state.value.step,
  (step, before) => {
    // A call restored after a reload goes from idle straight to on call.
    if (
      ["incoming", "ringing"].includes(step) ||
      (step === "oncall" && before === "idle")
    )
      props.window.open();
    if (step === "idle" && !pending.value) props.window.close();
  }
);
// The frame's close after a call hides the window; the card is spent.
watch(
  () => props.window.state,
  (frame) => {
    if (frame !== "closed") return;
    pending.value = null;
    controllers.forEach((controller) => controller.dismiss());
  }
);

// After a reload the phone call went on: Exotel reopens on it.
if (calls.Exotel && callState.liveExotel) {
  calls.Exotel.restore(callState.liveExotel);
  callState.liveExotel = null;
}
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
