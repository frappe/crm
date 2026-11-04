// "Make a call": the palette offers the open record's Phone numbers and takes a typed one; the shell offers them on the record from `field-actions.js`.
import { __ } from "frappe/i18n";
import { callState, startOutgoingCall } from "./callState.js";

export const MAKE_A_CALL = "shell.crm.make_a_call";

const MIN_DIGITS = 3;
const MAX_DIGITS = 15;

/** Reads the reactive call state, so a user whose media arrive after the first paint is offered the act then. */
const hasMedium = () => callState.media.length > 0;

/** A Phone field, or a Data field whose options say Phone. */
const isPhoneField = ({ fieldtype, options }) =>
  fieldtype === "Phone" || (fieldtype === "Data" && options === "Phone");

/**
 * The doc's non-empty Phone values with their field labels, from the doctype's meta (`{ fields }`).
 * One entry per distinct number, in field order; a number two fields hold has both labels, joined by ", ".
 * @returns {{ value: string, label: string }[]}
 */
export function phoneValues(doc, meta) {
  const labels = new Map();
  for (const field of meta?.fields ?? []) {
    const value = String(doc?.[field.fieldname] ?? "").trim();
    if (!value || !isPhoneField(field)) continue;
    labels.set(value, [...(labels.get(value) ?? []), field.label]);
  }
  return [...labels].map(([value, names]) => ({ value, label: names.join(", ") }));
}

/** The open record's Phone values as palette options: the number, with its fields' labels beside it. */
export function recordPhoneOptions(record) {
  return phoneValues(record?.doc, record).map(({ value, label }) => ({
    value,
    label: value,
    description: label,
    icon: "lucide-phone",
  }));
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
    options: (shell, query) => {
      const offered = recordPhoneOptions(shell.record?.());
      const typed = typedNumberOptions(query).filter(
        ({ value }) => !offered.some((option) => option.value === value)
      );
      return [...offered, ...typed];
    },
  },
  run: (shell, number) => {
    if (!number) throw new Error(__("Make a call needs a number"));
    startOutgoingCall(shell, number);
  },
};
