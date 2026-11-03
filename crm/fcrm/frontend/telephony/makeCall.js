// "Make a call": the palette takes a typed number, the Lead and Deal headers offer the record's own.
import { __ } from "frappe/i18n";
import { callState, startOutgoingCall } from "./callState.js";

export const MAKE_A_CALL = "shell.crm.make_a_call";

const NUMBER_FIELDS = ["mobile_no", "phone"];
const MIN_DIGITS = 3;
const MAX_DIGITS = 15;

/** Reads the reactive call state, so a user whose media arrive after the first paint is offered the act then. */
const hasMedium = () => callState.media.length > 0;

/** The record's distinct numbers, mobile first. */
export function recordNumbers(doc) {
  const numbers = NUMBER_FIELDS.map((field) => doc?.[field]?.trim()).filter(Boolean);
  return [...new Set(numbers)];
}

/** The typed text as the palette's one choice, once it reads as a phone number. */
export function typedNumberOptions(query) {
  const number = query.trim();
  const digits = number.replace(/\D/g, "").length;
  if (!/^\+?\d[\d\s().-]*$/.test(number) || digits < MIN_DIGITS || digits > MAX_DIGITS) return [];
  return [{ value: number, label: number, icon: "lucide-phone" }];
}

/** The shell act: `value` is the number the palette's argument step picked. */
export const makeACallAct = {
  name: "make_a_call",
  get label() {
    return __("Make a call");
  },
  icon: "lucide-phone",
  when: hasMedium,
  argument: {
    get label() {
      return __("Type a phone number");
    },
    options: (shell, query) => typedNumberOptions(query),
  },
  run: (shell, number) => {
    if (!number) throw new Error(__("Make a call needs a number"));
    return startOutgoingCall(number);
  },
};

const countOf = (page) => recordNumbers(page.doc).length;

/** Adds the `⋯` entries on a saved record: one that calls its only number, one that asks when it has two. */
export function addCallItem(page) {
  if (page.isNew) return;
  // `palette: false`: the palette lists the Desk act `shell.crm.make_a_call`, so the header entry would double it.
  const item = { name: "make_a_call", label: __("Make a call"), icon: "lucide-phone", palette: false };
  // `when` reads the draft, so a number typed or cleared before the save changes the entry offered.
  page.header.add({
    ...item,
    when: (page) => hasMedium() && countOf(page) === 1,
    run: (page) => page.run(MAKE_A_CALL, recordNumbers(page.doc)[0]),
  });
  page.header.add({
    ...item,
    name: "make_a_call_from",
    when: (page) => hasMedium() && countOf(page) > 1,
    argument: {
      label: __("Numbers"),
      options: (page) =>
        recordNumbers(page.doc).map((number) => ({ value: number, label: number })),
    },
    run: (page, number) => page.run(MAKE_A_CALL, number),
  });
}
