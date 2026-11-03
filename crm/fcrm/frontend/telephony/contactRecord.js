// The record a call's number belongs to, for the call card: shared by every medium.

/** `{ name, image, number, record }` for `number`; `record` is the deal, lead or contact it resolves to. */
export async function lookupContact(api, number) {
  const found = await api.contact(number);
  const doctype = found.deal
    ? "CRM Deal"
    : found.lead
    ? "CRM Lead"
    : found.name
    ? "Contact"
    : "";
  return {
    name: found.full_name || "",
    image: found.image || "",
    number,
    record: doctype
      ? { doctype, name: found.deal || found.lead || found.name }
      : null,
  };
}
